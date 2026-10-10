"""Demonstration data loading.

seed_if_missing is the only function used at startup and it never touches an
existing data file. force_seed is for the explicit CLI script only.
"""
import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)


def _load_sample(sample_file):
    path = Path(sample_file)
    if not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        logger.error("Sample data file %s could not be read.", path.name)
        return None
    records = payload.get("students") if isinstance(payload, dict) else payload
    return records if isinstance(records, list) else None


def seed_if_missing(store, sample_file):
    """Create the data file from sample data only if it does not exist yet."""
    if store.exists():
        return False
    with store.transaction():
        if store.exists():
            return False
        records = _load_sample(sample_file)
        if not records:
            return False
        store.write(records)
    logger.info("Created %s with %d demonstration records.", store.path.name, len(records))
    return True


def force_seed(store, sample_file):
    """Replace the data file with sample data, keeping a timestamped backup."""
    records = _load_sample(sample_file)
    if not records:
        raise RuntimeError("Sample data file is missing or invalid.")
    backup = None
    with store.transaction():
        if store.exists():
            stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            backup = store.path.with_name(f"{store.path.name}.bak-{stamp}")
            os.replace(store.path, backup)
        store.write(records)
    return len(records), backup
