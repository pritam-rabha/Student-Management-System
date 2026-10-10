"""Storage contract for student records.

Services depend only on this interface. A database or hosted-storage
implementation can replace the JSON one without touching routes or services.
"""
from abc import ABC, abstractmethod


class StudentRepository(ABC):
    @abstractmethod
    def all(self):
        """Return every student record as a list of dicts."""

    @abstractmethod
    def get(self, student_id):
        """Return one record or None."""

    @abstractmethod
    def add(self, record):
        """Insert a record. Raises DuplicateStudentError if the ID exists."""

    @abstractmethod
    def update(self, student_id, fields):
        """Merge fields into an existing record and return it.

        Raises StudentNotFoundError if the ID does not exist.
        """

    @abstractmethod
    def delete(self, student_id):
        """Remove a record. Raises StudentNotFoundError if missing."""
