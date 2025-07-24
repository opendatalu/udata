import asyncio
from typing import List, Optional

from datetime import datetime, timedelta

from dateutil.parser import parse
from flask import current_app, json

from udata import mail
from udata.core import storages
from udata.core.storages import chunks
from udata.core.storages.api import META
from udata.tasks import get_logger, job

from govcert_file_scan.scanner import MultiAVScanner, ScanResultEnum

from .file_scan import trigger_antivirus_scan


log = get_logger(__name__)


@job("purge-chunks")
def purge_chunks(self):
    log.info("Purging uploaded chunks")
    max_retention = timedelta(seconds=current_app.config["UPLOAD_MAX_RETENTION"])
    meta_files = (f for f in chunks.list_files() if f.endswith(META))
    for filename in meta_files:
        metadata = json.loads(chunks.read(filename))
        if datetime.utcnow() - parse(metadata["lastchunk"]) >= max_retention:
            uuid = metadata["uuid"]
            log.info("Removing %s expired chunks", uuid)
            chunks.delete(uuid)


@job("antivirus-scan-file", queue="high")
def run_antivirus_scan(
    self,
    fs_filename: str,
    filename: str,
    send_mail: Optional[List[str]] = None,
    send_if_ok: bool = False,
    is_local_file: bool = False,
    resource_id: Optional[str] = None,
    dataset_id: Optional[str] = None,
    resource_url: Optional[str] = None,
    dataset_url: Optional[str] = None,
):
    """
    Celery task wrapper for triggering an antivirus scan.
    """
    log.info(f"Starting antivirus scan from Celery for: {filename}")
    try:
        result = asyncio.run(
            trigger_antivirus_scan(
                log=log,
                fs_filename=fs_filename,
                filename=filename,
                send_mail=send_mail,
                send_if_ok=send_if_ok,
                is_local_file=is_local_file,
                resource_id=resource_id,
                dataset_id=dataset_id,
                resource_url=resource_url,
                dataset_url=dataset_url,
            )
        )
        log.info(f"Scan complete for '{filename}' with result: {result}")
        return str(result)
    except Exception as e:
        log.exception(f"Error during antivirus scan for '{filename}': {e}")
        raise
