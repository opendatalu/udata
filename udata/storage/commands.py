import logging
from typing import Optional
from bson import ObjectId

from pathlib import Path
import asyncio
import click

from udata.commands import cli
from udata.core.storages.file_scan import trigger_antivirus_scan, ScanResultEnum

from udata.core.dataset.models import Dataset

from flask_storage.errors import FileNotFound
# from flask import current_app

log = logging.getLogger(__name__)


@cli.group("storage")
def grp():
    """Storage related operations"""
    pass


def configure_scan_loggers():
    udata_root = Path(__file__).parent.parent.parent
    logs_dir = udata_root / "logs"
    if not logs_dir.exists():
        logs_dir.mkdir()
    clean_log = logs_dir / "clean.log"
    infected_log = logs_dir / "infected.log"
    error_log = logs_dir / "error.log"

    logger_clean = logging.getLogger("clean")
    logger_infected = logging.getLogger("infected")
    logger_error = logging.getLogger("error")

    handler_clean = logging.FileHandler(clean_log)
    handler_infected = logging.FileHandler(infected_log)
    handler_error = logging.FileHandler(error_log)

    formatter = logging.Formatter("[%(asctime)s] %(message)s")
    handler_clean.setFormatter(formatter)
    handler_infected.setFormatter(formatter)
    handler_error.setFormatter(formatter)

    logger_clean.addHandler(handler_clean)
    logger_infected.addHandler(handler_infected)
    logger_error.addHandler(handler_error)

    logger_clean.setLevel(logging.INFO)
    logger_infected.setLevel(logging.INFO)
    logger_error.setLevel(logging.INFO)

    return logger_clean, logger_infected, logger_error


@grp.command()
@click.option("--storage-file", default=None, help="File to scan")
@click.option("--local-file", default=None, help="Local file to scan")
@click.option(
    "--notify-email", default=None, help="Email to notify when infected file is found"
)
@click.option("--send-if-ok", default=False, help="Send email even if file is clean")
def scan_av_one(
    notify_email: Optional[str] = None,
    send_if_ok: bool = False,
    storage_file: Optional[str] = None,
    local_file: Optional[str] = None,
):
    """
    Scan one file locally or from storage
    """

    if notify_email:
        send_mail = [notify_email]
    else:
        send_mail = None

    if storage_file and local_file:
        raise click.ClickException(
            "Only one of --storage-file or --local-file can be used at a time"
        )
    elif not storage_file and not local_file:
        raise click.ClickException(
            "Either --storage-file or --local-file must be provided"
        )
    elif storage_file:
        identifier = f"storage file {storage_file}"
        fs_filename = storage_file
    elif local_file:
        identifier = f"local file {local_file}"
        fs_filename = local_file

    log.info(f"Scanning {identifier}")

    # 2. Call the imported core logic directly, passing it the CLI logger
    result = asyncio.run(
        trigger_antivirus_scan(
            log=log,
            fs_filename=fs_filename,
            filename="test_file",
            send_mail=send_mail,
            send_if_ok=send_if_ok,
            is_local_file=bool(local_file),
            resource_id=None,  # Not applicable for single file scan
            dataset_id=None,  # Not applicable for single file scan
        )
    )

    log.info(f"Scan result: {result}")


@grp.command()
@click.option("--from-id", default=None, help="Start scanning from this dataset ID")
@click.option(
    "--notify-email", default=None, help="Email to notify when infected file is found"
)
@click.option("--send-if-ok", default=False, help="Send email even if file is clean")
def scan_av(
    from_id: Optional[str] = None,
    notify_email: Optional[str] = None,
    send_if_ok: bool = False,
):
    """
    Iterate all datasets and their resources
    Scan each resource
    Write the resource link to one of three log files: clean, infected, error
    If unhandled error, retry 10 times with interval of 2 minutes
    """

    logger_clean, logger_infected, logger_error = configure_scan_loggers()

    if notify_email:
        send_mail = [notify_email]
    else:
        send_mail = None

    # Build query with optional from_id filter and ordering
    query = Dataset.objects.order_by("created_at_internal")
    if from_id:
        try:
            object_id = ObjectId(from_id)
            query = query.filter(created_at_internal__gt=object_id)
        except Exception as e:
            raise click.ClickException(
                f"Invalid ObjectId format for --from-id: {from_id}. Error: {e}"
            )

    # Process datasets
    for dataset in query:
        for resource in dataset.resources:
            identifier = (
                f"{dataset.id}/{resource.id} - {resource.url} ({resource.title})"
            )

            log.info(f"Scanning {identifier}")

            fs_filename = resource.fs_filename

            try:
                result = asyncio.run(
                    trigger_antivirus_scan(
                        fs_filename,
                        resource.id,
                        send_mail=send_mail,
                        send_if_ok=send_if_ok,
                        resource_id=str(resource.id), 
                        dataset_id=str(dataset.id),
                        resource_url=resource.url,
                    )
                )
            except FileNotFound as e:
                logger_error.info(identifier)
                logger_error.exception(e)
                result = None
            except Exception as e:
                logger_error.info(identifier)
                logger_error.exception(e)
                result = None

            if result == ScanResultEnum.OK:
                logger_clean.info(identifier)
            elif result == ScanResultEnum.INFECTED:
                logger_infected.info(identifier)
            else:
                logger_error.info(identifier)
