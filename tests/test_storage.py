import json
import os
import threading

import pytest

from app.exceptions import DuplicateStudentError, StorageError, StudentNotFoundError
from app.storage.json_store import JsonFileStore, JsonStudentRepository
from app.storage.seed import force_seed, seed_if_missing


@pytest.fixture
def store(tmp_path):
    return JsonFileStore(tmp_path / "nested" / "students.json")


@pytest.fixture
def repo(store):
    return JsonStudentRepository(store)


def record(student_id="S1", **extra):
    return {"student_id": student_id, "full_name": "Test User", **extra}


def test_missing_file_reads_as_empty(store):
    assert not store.exists()
    assert store.read() == []


def test_write_creates_directories_and_round_trips(store):
    store.write([record("S1"), record("S2")])
    assert store.path.exists()
    assert [r["student_id"] for r in store.read()] == ["S1", "S2"]
    payload = json.loads(store.path.read_text(encoding="utf-8"))
    assert payload["version"] == 1 and len(payload["students"]) == 2


def test_unicode_is_preserved(store):
    store.write([record("S1", full_name="Zoe Muller-Nunez, Chandra")])
    assert store.read()[0]["full_name"] == "Zoe Muller-Nunez, Chandra"


def test_malformed_json_is_quarantined_not_overwritten(store):
    store.path.parent.mkdir(parents=True)
    store.path.write_text("{ this is not json", encoding="utf-8")
    assert store.read() == []
    assert not store.path.exists()
    backups = list(store.path.parent.glob("students.json.corrupt-*"))
    assert len(backups) == 1
    assert backups[0].read_text(encoding="utf-8") == "{ this is not json"
    # the store is usable again afterwards
    store.write([record("S1")])
    assert len(store.read()) == 1


@pytest.mark.parametrize("content", [
    "",                                    # empty file
    "null",                                # wrong top-level type
    '{"students": "oops"}',                # students is not a list
    '{"version": 1}',                      # missing key
    '{"students": [1, 2, 3]}',             # records are not objects
    '{"students": [{"name": "no id"}]}',   # record without student_id
])
def test_structurally_invalid_files_are_quarantined(store, content):
    store.path.parent.mkdir(parents=True)
    store.path.write_text(content, encoding="utf-8")
    assert store.read() == []
    assert list(store.path.parent.glob("students.json.corrupt-*"))


def test_binary_garbage_is_quarantined(store):
    store.path.parent.mkdir(parents=True)
    store.path.write_bytes(b"\xff\xfe\x00\x80garbage")
    assert store.read() == []
    assert list(store.path.parent.glob("students.json.corrupt-*"))


def test_bare_list_format_is_tolerated(store):
    store.path.parent.mkdir(parents=True)
    store.path.write_text(json.dumps([record("S1")]), encoding="utf-8")
    assert store.read()[0]["student_id"] == "S1"


def test_failed_write_leaves_original_intact_and_no_temp_files(store, monkeypatch):
    store.write([record("S1")])

    def failing_replace(src, dst):
        raise OSError("disk full")

    monkeypatch.setattr(os, "replace", failing_replace)
    with pytest.raises(StorageError):
        store.write([record("S1"), record("S2")])
    monkeypatch.undo()

    assert [r["student_id"] for r in store.read()] == ["S1"]
    assert list(store.path.parent.glob("*.tmp")) == []


def test_unserialisable_data_does_not_corrupt_file(store):
    store.write([record("S1")])
    with pytest.raises(StorageError):
        store.write([record("S2", bad=object())])
    assert [r["student_id"] for r in store.read()] == ["S1"]
    assert list(store.path.parent.glob("*.tmp")) == []


def test_repository_crud(repo):
    repo.add(record("S1", marks=50))
    repo.add(record("S2"))
    assert repo.get("S1")["marks"] == 50
    assert repo.get("MISSING") is None
    assert len(repo.all()) == 2

    updated = repo.update("S1", {"marks": 75, "student_id": "CHANGED"})
    assert updated["marks"] == 75 and updated["student_id"] == "S1"
    assert repo.get("S1")["marks"] == 75

    repo.delete("S1")
    assert repo.get("S1") is None and len(repo.all()) == 1


def test_repository_errors(repo):
    repo.add(record("S1"))
    with pytest.raises(DuplicateStudentError):
        repo.add(record("S1"))
    with pytest.raises(StudentNotFoundError):
        repo.update("NOPE", {"x": 1})
    with pytest.raises(StudentNotFoundError):
        repo.delete("NOPE")
    assert len(repo.all()) == 1


def test_concurrent_adds_do_not_lose_records(repo):
    errors = []

    def worker(n):
        try:
            repo.add(record(f"T{n}"))
        except Exception as exc:  # pragma: no cover - failure path
            errors.append(exc)

    threads = [threading.Thread(target=worker, args=(n,)) for n in range(20)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert errors == []
    assert len(repo.all()) == 20


def test_unwritable_location_raises_storage_error(tmp_path):
    blocker = tmp_path / "blocker"
    blocker.write_text("a file, not a directory")
    store = JsonFileStore(blocker / "students.json")
    with pytest.raises(StorageError):
        store.write([record("S1")])


def sample_file(tmp_path, count=3):
    path = tmp_path / "sample.json"
    path.write_text(json.dumps({"version": 1, "students": [record(f"D{n}") for n in range(count)]}),
                    encoding="utf-8")
    return path


def test_seed_only_when_data_file_is_missing(store, tmp_path):
    sample = sample_file(tmp_path)
    assert seed_if_missing(store, sample) is True
    assert len(store.read()) == 3
    store.write([record("REAL")])
    assert seed_if_missing(store, sample) is False
    assert [r["student_id"] for r in store.read()] == ["REAL"]


def test_seed_does_not_replace_an_empty_existing_file(store, tmp_path):
    store.write([])
    assert seed_if_missing(store, sample_file(tmp_path)) is False
    assert store.read() == []


def test_seed_with_missing_sample_file_is_a_noop(store, tmp_path):
    assert seed_if_missing(store, tmp_path / "absent.json") is False
    assert not store.exists()


def test_force_seed_keeps_backup(store, tmp_path):
    store.write([record("REAL")])
    count, backup = force_seed(store, sample_file(tmp_path, 2))
    assert count == 2 and backup is not None and backup.exists()
    assert [r["student_id"] for r in store.read()] == ["D0", "D1"]
    assert json.loads(backup.read_text(encoding="utf-8"))["students"][0]["student_id"] == "REAL"


def test_bundled_sample_data_is_valid(tmp_path):
    from config import load_config
    from app.utils.validators import validate_student

    payload = json.loads(load_config()["SAMPLE_DATA_FILE"].read_text(encoding="utf-8"))
    students = payload["students"]
    assert len(students) >= 20
    assert len({s["student_id"] for s in students}) == len(students)
    for s in students:
        data = {k: ("" if v is None else v) for k, v in s.items()}
        _, errors = validate_student(data)
        assert errors == {}, (s["student_id"], errors)


def test_application_start_seeds_only_missing_file(tmp_path):
    from app import create_app

    config = {"TESTING": True, "SECRET_KEY": "k" * 32, "DATA_DIR": tmp_path / "d", "SEED_SAMPLE_DATA": True}
    first = create_app(config)
    seeded = first.extensions["sms"].repository.all()
    assert len(seeded) >= 20

    first.extensions["sms"].repository.delete(seeded[0]["student_id"])
    second = create_app(config)
    assert len(second.extensions["sms"].repository.all()) == len(seeded) - 1


def test_corrupt_data_file_does_not_crash_the_app(tmp_path):
    from app import create_app
    from tests.helpers import login

    data_dir = tmp_path / "d"
    data_dir.mkdir()
    (data_dir / "students.json").write_text("<<<corrupt>>>", encoding="utf-8")
    app = create_app({"TESTING": True, "SECRET_KEY": "k" * 32, "DATA_DIR": data_dir,
                      "SEED_SAMPLE_DATA": False, "ADMIN_PASSWORD": "a-long-test-password"})
    client = app.test_client()
    assert login(client, password="a-long-test-password").status_code == 302
    assert client.get("/students/").status_code == 200
    assert list(data_dir.glob("students.json.corrupt-*"))


def test_tests_do_not_touch_real_data_directory(app):
    from config import BASE_DIR
    assert app.config["DATA_DIR"] != BASE_DIR / "data"
