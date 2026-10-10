"""JSON file storage.

File format (see README for the full description):

    {"version": 1, "students": [ {student record}, ... ]}

Writes go to a temporary file in the same directory, are flushed and fsynced,
and then replace the real file with os.replace, so readers never observe a
half-written file. Read-modify-write operations run inside transaction(),
which serialises writers across threads and, where available, processes.
"""
import json
import logging
import os
import tempfile
import threading
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from app.exceptions import DuplicateStudentError, StorageError, StudentNotFoundError
from app.storage.base import StudentRepository

try:  # POSIX only; Windows falls back to the in-process lock.
    import fcntl
except ImportError:  # pragma: no cover
    fcntl = None

SCHEMA_VERSION = 1
ROOT_KEY = "students"

logger = logging.getLogger(__name__)


class JsonFileStore:
    def __init__(self, path):
        self.path = Path(path)
        self._thread_lock = threading.RLock()

    def exists(self):
        return self.path.exists()

    def read(self):
        """Return the stored records.

        A missing file yields an empty list. A malformed or structurally
        invalid file is renamed to <name>.corrupt-<timestamp> (so nothing is
        lost) and an empty list is returned.
        """
        try:
            raw = self.path.read_text(encoding="utf-8")
        except FileNotFoundError:
            return []
        except UnicodeDecodeError:
            return self._quarantine("file is not valid UTF-8")
        except OSError as exc:
            raise StorageError(f"Cannot read {self.path.name}: {exc.strerror}") from exc

        try:
            payload = json.loads(raw)
        except ValueError:
            return self._quarantine("file is not valid JSON")

        if isinstance(payload, list):  # tolerate a bare list
            records = payload
        elif isinstance(payload, dict) and isinstance(payload.get(ROOT_KEY), list):
            records = payload[ROOT_KEY]
        else:
            return self._quarantine("unexpected top-level structure")

        if not all(isinstance(r, dict) and isinstance(r.get("student_id"), str) for r in records):
            return self._quarantine("records are not valid student objects")
        return records

    def write(self, records):
        """Atomically replace the file with the given records."""
        payload = {"version": SCHEMA_VERSION, ROOT_KEY: records}
        directory = self.path.parent
        tmp_name = None
        try:
            directory.mkdir(parents=True, exist_ok=True)
            fd, tmp_name = tempfile.mkstemp(
                dir=directory, prefix=self.path.name + ".", suffix=".tmp"
            )
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(payload, handle, indent=2, ensure_ascii=False)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(tmp_name, self.path)
            tmp_name = None
        except (OSError, TypeError, ValueError) as exc:
            raise StorageError(f"Cannot write {self.path.name}: {exc}") from exc
        finally:
            if tmp_name and os.path.exists(tmp_name):
                try:
                    os.unlink(tmp_name)
                except OSError:
                    pass

    @contextmanager
    def transaction(self):
        """Exclusive section for read-modify-write cycles."""
        with self._thread_lock:
            lock_handle = None
            try:
                if fcntl is not None:
                    self.path.parent.mkdir(parents=True, exist_ok=True)
                    lock_handle = open(self.path.with_name(self.path.name + ".lock"), "a+")
                    fcntl.flock(lock_handle, fcntl.LOCK_EX)
                yield
            except OSError as exc:
                raise StorageError(f"Cannot lock {self.path.name}: {exc.strerror}") from exc
            finally:
                if lock_handle is not None:
                    try:
                        fcntl.flock(lock_handle, fcntl.LOCK_UN)
                    finally:
                        lock_handle.close()

    def _quarantine(self, reason):
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        target = self.path.with_name(f"{self.path.name}.corrupt-{stamp}")
        try:
            os.replace(self.path, target)
            logger.error("%s: %s. Moved to %s and starting empty.", self.path.name, reason, target.name)
        except OSError:
            logger.error("%s: %s. Could not move it aside.", self.path.name, reason)
        return []


class JsonStudentRepository(StudentRepository):
    def __init__(self, store):
        self._store = store

    @property
    def store(self):
        return self._store

    def all(self):
        return self._store.read()

    def get(self, student_id):
        for record in self._store.read():
            if record["student_id"] == student_id:
                return record
        return None

    def add(self, record):
        with self._store.transaction():
            records = self._store.read()
            if any(r["student_id"] == record["student_id"] for r in records):
                raise DuplicateStudentError(record["student_id"])
            records.append(record)
            self._store.write(records)

    def update(self, student_id, fields):
        with self._store.transaction():
            records = self._store.read()
            for index, record in enumerate(records):
                if record["student_id"] == student_id:
                    merged = {**record, **fields, "student_id": student_id}
                    records[index] = merged
                    self._store.write(records)
                    return merged
        raise StudentNotFoundError(student_id)

    def delete(self, student_id):
        with self._store.transaction():
            records = self._store.read()
            remaining = [r for r in records if r["student_id"] != student_id]
            if len(remaining) == len(records):
                raise StudentNotFoundError(student_id)
            self._store.write(remaining)
