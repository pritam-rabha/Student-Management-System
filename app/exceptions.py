"""Domain exceptions shared by the storage and service layers."""


class StudentError(Exception):
    """Base class for student-related errors."""


class StudentNotFoundError(StudentError):
    def __init__(self, student_id):
        super().__init__(f"Student {student_id!r} was not found.")
        self.student_id = student_id


class DuplicateStudentError(StudentError):
    def __init__(self, student_id):
        super().__init__(f"Student ID {student_id!r} already exists.")
        self.student_id = student_id


class ValidationError(StudentError):
    """Raised when submitted data fails validation. errors maps field -> message."""

    def __init__(self, errors):
        super().__init__("Validation failed.")
        self.errors = errors


class StorageError(Exception):
    """Raised when the data store cannot be read or written."""
