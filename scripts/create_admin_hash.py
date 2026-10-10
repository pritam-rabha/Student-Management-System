"""Generate a password hash for the ADMIN_PASSWORD_HASH environment variable.

    python scripts/create_admin_hash.py

The password is read without echo and is never written to disk. Copy the
printed value into your environment (Render dashboard or a local .env file).
"""
import getpass
import sys

from werkzeug.security import generate_password_hash

MIN_LENGTH = 10


def main():
    password = getpass.getpass("Administrator password: ")
    if len(password) < MIN_LENGTH:
        print(f"Password must be at least {MIN_LENGTH} characters.", file=sys.stderr)
        return 1
    if password != getpass.getpass("Repeat password: "):
        print("Passwords do not match.", file=sys.stderr)
        return 1

    password_hash = generate_password_hash(password, method="pbkdf2:sha256")
    print("\nSet this environment variable (keep the single quotes in a .env file):\n")
    print(f"ADMIN_PASSWORD_HASH='{password_hash}'")
    return 0


if __name__ == "__main__":
    sys.exit(main())
