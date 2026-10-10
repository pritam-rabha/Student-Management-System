from app.storage.base import StudentRepository
from app.storage.json_store import JsonFileStore, JsonStudentRepository

__all__ = ["StudentRepository", "JsonFileStore", "JsonStudentRepository"]
