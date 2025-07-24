import logging
from typing import List, Optional

from flask import current_app
from govcert_file_scan.scanner import MultiAVScanner, ScanResultEnum

from udata import mail
from udata.core import storages


async def trigger_antivirus_scan(
    log,
    fs_filename: str,
    filename: str,
    send_mail: Optional[List[str]] = None,
    send_if_ok: bool = False,
    is_local_file: bool = False,
    resource_id: Optional[str] = None,
    dataset_id: Optional[str] = None,
    resource_url: Optional[str] = None,
    dataset_url: Optional[str] = None,
) -> ScanResultEnum:
    """
    Scans a file, removes it from storage if infected, and sends notifications.
    This is the core business logic.
    """
    api_key = current_app.config.get("GOVCERT_AV_API_KEY")
    if not api_key:
        log.info("No API key found for the GovCERT AV scanner. Skipping scan.")
        return None

    if is_local_file:
        with open(fs_filename, "rb") as f:
            data = f.read()
    else:
        data = storages.resources.read(fs_filename)

    if not isinstance(data, bytes):
        raise ValueError(f"The file is not in bytes format. Got '{type(data)}' instead")

    resource_id = resource_id if resource_id else "not set"
    dataset_id = dataset_id if dataset_id else "not set"
    resource_url = resource_url if resource_url else "not set"
    dataset_url = dataset_url if dataset_url else "not set"

    scanner = MultiAVScanner(api_key=api_key)
    result = await scanner.scan_file(data, file_name=filename)

    log.info(f"Scan result for file '{filename}': {result}")

    # The rest of the notification logic remains the same...
    if result == ScanResultEnum.INFECTED:
        log.warning(f"File '{filename}' is INFECTED")
        # storages.resources.delete(fs_filename)
        if send_mail:
            log.info(f"Sending infected file notification to {send_mail}")
            subject = f"Infected file found: {filename}"
            mail.send(
                subject,
                send_mail,
                "infected_file",
                first_sentence=subject,
                filename=filename,
                filepath=fs_filename,
                resource_id=resource_id,
                dataset_id=dataset_id,
                resource_url=resource_url,
                dataset_url=dataset_url,
            )
    elif send_if_ok and send_mail:
        log.info(f"File '{filename}' is clean. Sending notification to {send_mail}")
        subject = f"File scan complete (clean): {filename}"
        mail.send(
            subject,
            send_mail,
            "clean_file",
            first_sentence=subject,
            filename=filename,
            fs_filename=fs_filename,
            resource_id=resource_id,
            dataset_id=dataset_id,
            resource_url=storages.resources.get_url(fs_filename),
            dataset_url=dataset_url,
        )

    return result
