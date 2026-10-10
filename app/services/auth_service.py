"""Administrator credential verification."""
import hmac
import secrets

from werkzeug.security import check_password_hash, generate_password_hash

HASH_METHOD = "pbkdf2:sha256"


class AuthService:
    def __init__(self, username, password_hash=None, password=None):
        self.username = username
        if password_hash:
            self._hash = password_hash
        elif password:
            # Hashed in memory only; the plaintext is never stored or logged.
            self._hash = generate_password_hash(password, method=HASH_METHOD)
        else:
            self._hash = None
        # Verified against when the username is wrong, so timing does not
        # reveal whether the username was correct.
        self._dummy_hash = generate_password_hash(secrets.token_hex(16), method=HASH_METHOD)

    @property
    def configured(self):
        return bool(self.username and self._hash)

    def verify(self, username, password):
        if not self.configured:
            return False
        username_ok = hmac.compare_digest(username.encode("utf-8"), self.username.encode("utf-8"))
        try:
            password_ok = check_password_hash(self._hash if username_ok else self._dummy_hash, password)
        except (ValueError, TypeError):
            password_ok = False
        return username_ok and password_ok
