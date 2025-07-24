import os
from typing import Dict, Any, Optional
from datetime import datetime
import logging
import json

from flask import json
from werkzeug.datastructures import FileStorage
import flask_caching

from udata.app import cache
from udata.api import api, fields

from . import chunks, utils

logger = logging.getLogger(__name__)

META = "meta.json"

IMAGES_MIMETYPES = ("image/jpeg", "image/png", "image/webp")


from flask import current_app


uploaded_image_fields = api.model(
    "UploadedImage",
    {
        "success": fields.Boolean(
            description="Whether the upload succeeded or not.",
            readonly=True,
            default=True,
        ),
        "image": fields.ImageField(),
    },
)

chunk_status_fields = api.model(
    "UploadStatus", {"success": fields.Boolean, "error": fields.String}
)


image_parser = api.parser()
image_parser.add_argument("file", type=FileStorage, location="files")
image_parser.add_argument("bbox", type=str, location="form")


upload_parser = api.parser()
upload_parser.add_argument("file", type=FileStorage, location="files")
upload_parser.add_argument("uuid", type=str, location="form")
upload_parser.add_argument("filename", type=str, location="form")
upload_parser.add_argument("partindex", type=int, location="form")
upload_parser.add_argument("partbyteoffset", type=int, location="form")
upload_parser.add_argument("totalparts", type=int, location="form")
upload_parser.add_argument("chunksize", type=int, location="form")

# redis helpers for multipart uploads


class UploadStatus(Exception):
    def __init__(self, ok=True, error=None):
        super(UploadStatus, self).__init__()
        self.ok = ok
        self.error = error


class UploadProgress(UploadStatus):
    """Raised on successful chunk uploaded"""

    pass


class UploadError(UploadStatus):
    """Raised on any upload error"""

    def __init__(self, error=None):
        super(UploadError, self).__init__(ok=False, error=error)


def on_upload_status(status):
    """Not an error, just raised when chunk is processed"""
    if status.ok:
        return {"success": True}, 200
    else:
        return {"success": False, "error": status.error}, 400


@api.errorhandler(UploadStatus)
@api.errorhandler(UploadError)
@api.errorhandler(UploadProgress)
@api.marshal_with(chunk_status_fields, code=200)
def api_upload_status(status):
    """API Upload response handler"""
    return on_upload_status(status)


def chunk_filename(uuid, part):
    return f"chunk_{uuid}_{part}"


def get_file_size(file):
    file.seek(0, os.SEEK_END)
    size = file.tell()
    file.seek(0)
    return size


def save_chunk(file, args):
    if get_file_size(file) != args["chunksize"]:
        raise UploadProgress(ok=False, error="Chunk size mismatch")
    filename = chunk_filename(args["uuid"], args["partindex"])
    chunks.save(
        file, filename=filename, overwrite=True
    )  # Browsers might attempt to re-upload the same chunk
    meta_filename = chunk_filename(args["uuid"], META)
    chunks.write(
        meta_filename,
        json.dumps(
            {
                "uuid": str(args["uuid"]),
                "filename": args["filename"],
                "totalparts": args["totalparts"],
                "lastchunk": datetime.utcnow(),
            }
        ),
        overwrite=True,
    )


def combine_chunks(storage, args, prefix=None):
    """
    Combine a chunked file into a whole file again.
    Goes through each part, in order,
    and appends that part's bytes to another destination file.
    Chunks are stored in the chunks storage.
    """
    uuid = args["uuid"]
    # Normalize filename including extension
    target = utils.normalize(args["filename"])
    if prefix:
        target = os.path.join(prefix, target)
    with storage.open(target, "wb") as out:
        for i in range(args["totalparts"]):
            partname = chunk_filename(uuid, i)
            out.write(chunks.read(partname))
            # Note: somehow, if the delete is done here, it will be deleted before the read operation is completed,
            # and it will trigger a FIleNotFound error on files with 10+ chunks.
            # chunks.delete(partname)
            # https://gitlab.geoportail.lu/geoportail/migration-data-public-lu/-/issues/177
        # Delete all chunks now instead.
        for i in range(args["totalparts"]):
            partname = chunk_filename(uuid, i)
            chunks.delete(partname)
        chunks.delete(chunk_filename(uuid, META))
    return target


def parse_uploaded_image(field):
    """Parse an uploaded image and save into a db.ImageField()"""
    args = image_parser.parse_args()

    image = args["file"]
    if image.mimetype not in IMAGES_MIMETYPES:
        api.abort(400, "Unsupported image format")
    bbox = args.get("bbox", None)
    if bbox:
        bbox = [int(float(c)) for c in bbox.split(",")]
    field.save(image, bbox=bbox)


def _create_metadata(
    storage, fs_filename: str, filename_normalized: str
) -> Dict[str, Any]:
    """Retrieves and processes file metadata after a successful upload."""
    metadata = storage.metadata(fs_filename)
    metadata["last_modified_internal"] = metadata.pop("modified")
    metadata["fs_filename"] = fs_filename
    metadata["filename"] = filename_normalized

    checksum = metadata.pop("checksum")
    algo, checksum_value = checksum.split(":", 1)
    metadata[algo] = checksum_value

    metadata["format"] = utils.extension(fs_filename)
    return metadata


def _handle_s3_chunk(
    storage, args: Dict[str, Any], uuid: str, fs_filename: str, filename_normalized: str
):
    """Handles the upload of a single chunk to an S3 backend."""
    part_number = args["partindex"] + 1
    uploaded_file = args["file"]
    logger.info(f"Uploading part {part_number} of file {fs_filename}")
    if part_number == 1:
        upload_id, part_info = storage.write_multipart(
            filename=fs_filename, content=uploaded_file, part_number=part_number
        )
        cache.cache.set(f"upload-{uuid}-id", upload_id, 3600)
        cache.cache.set(f"upload-{uuid}-fs_filename", fs_filename, 3600)
        cache.cache.set(f"upload-{uuid}-filename_normalized", filename_normalized, 3600)
    else:
        upload_id = cache.cache.get(f"upload-{uuid}-id")
        cached_fs_filename = cache.cache.get(f"upload-{uuid}-fs_filename")
        if not upload_id or not cached_fs_filename:
            raise UploadError("Missing upload_id or fs_filename from cache")
        _, part_info = storage.write_multipart(
            filename=cached_fs_filename,
            content=uploaded_file,
            part_number=part_number,
            upload_id=upload_id,
        )
    parts_key = f"upload-{uuid}-parts"
    cache.cache._write_client.hset(parts_key, part_number, json.dumps(part_info))
    cache.cache._write_client.expire(parts_key, 3600)


def _finalize_s3_upload(storage, args: Dict[str, Any], uuid: str) -> Dict[str, Any]:
    """Finalizes an S3 multipart upload by combining all chunks."""
    upload_id = cache.cache.get(f"upload-{uuid}-id")
    fs_filename = cache.cache.get(f"upload-{uuid}-fs_filename")
    filename_normalized = cache.cache.get(f"upload-{uuid}-filename_normalized")
    if not all([upload_id, fs_filename, filename_normalized]):
        raise UploadError("Missing upload identifiers from cache for finalization")
    parts_key = f"upload-{uuid}-parts"
    parts_info_raw = cache.cache._read_client.hgetall(parts_key)
    if args["totalparts"] != len(parts_info_raw):
        raise UploadError("Mismatch in expected and received part count")
    parts = [json.loads(part_info_b) for _, part_info_b in parts_info_raw.items()]
    storage.write_multipart(
        filename=fs_filename, upload_id=upload_id, parts_references=parts
    )
    cache.cache._write_client.unlink(parts_key)
    cache.delete(f"upload-{uuid}-id")
    cache.delete(f"upload-{uuid}-fs_filename")
    cache.delete(f"upload-{uuid}-filename_normalized")
    return _create_metadata(storage, fs_filename, filename_normalized)


def _finalize_generic_upload(
    storage, args: Dict[str, Any], prefix: Optional[str]
) -> Dict[str, Any]:
    """Finalizes a generic multipart upload by combining all chunks."""
    # Assumes the original filename is sent with the finalization request
    final_filename_normalized = args.get("filename")
    final_fs_filename = combine_chunks(
        storage, args, prefix=prefix, filename_normalized=final_filename_normalized
    )
    return _create_metadata(storage, final_fs_filename, final_filename_normalized)


def _handle_multipart_upload(
    storage,
    args: Dict[str, Any],
    filename_normalized: Optional[str],
    prefix: Optional[str] = None,
) -> Dict[str, Any]:
    """Handles a multipart file upload, branching by backend type first."""
    uploaded_file = args.get("file")
    is_s3_backend = current_app.config.get("FS_BACKEND").lower() == "s3"

    if is_s3_backend:
        if not isinstance(cache.cache, flask_caching.backends.rediscache.RedisCache):
            raise Exception("S3 backend requires Redis cache for multipart uploads")

        if uploaded_file:
            fs_filename = (
                os.path.join(prefix, filename_normalized)
                if prefix
                else filename_normalized
            )
            _handle_s3_chunk(
                storage, args, args["uuid"], fs_filename, filename_normalized
            )
            raise UploadProgress()
        else:
            return _finalize_s3_upload(storage, args, args["uuid"])

    else:  # Generic (non-S3) backend
        if uploaded_file:
            save_chunk(uploaded_file, args)
            raise UploadProgress()
        else:
            return _finalize_generic_upload(storage, args, prefix)


def handle_upload(storage, prefix: Optional[str] = None) -> Dict[str, Any]:
    """Main entry point for handling a file upload."""
    args = upload_parser.parse_args()
    is_multipart = args.get("totalparts") and args["totalparts"] > 1
    uploaded_file = args.get("file")
    filename_normalized = None

    if args.get("filename"):
        # Otherwise multipart uploads may receive something such as "blob" as filename
        filename_normalized = utils.normalize(args["filename"])
    else:
        try:
            filename_normalized = utils.normalize(uploaded_file.filename)
        except AttributeError:
            if is_multipart and not uploaded_file:
                pass  # Normal for the final chunk combination call
            else:
                raise

    if is_multipart:
        return _handle_multipart_upload(storage, args, filename_normalized, prefix)

    if uploaded_file:
        fs_filename = storage.save(
            uploaded_file, prefix=prefix, filename=filename_normalized
        )
        return _create_metadata(storage, fs_filename, filename_normalized)

    raise UploadError("Missing file or multipart parameters")
