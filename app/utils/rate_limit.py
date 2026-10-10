"""In-memory throttle for repeated failed logins (per client address)."""
import threading
import time


class LoginThrottle:
    def __init__(self, max_attempts=5, window_seconds=300, clock=time.monotonic):
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        self._clock = clock
        self._failures = {}
        self._lock = threading.Lock()

    def _recent(self, key, now):
        cutoff = now - self.window_seconds
        recent = [t for t in self._failures.get(key, []) if t > cutoff]
        if recent:
            self._failures[key] = recent
        else:
            self._failures.pop(key, None)
        return recent

    def seconds_blocked(self, key):
        """Seconds until the key may try again, or 0 when not blocked."""
        with self._lock:
            now = self._clock()
            recent = self._recent(key, now)
            if len(recent) < self.max_attempts:
                return 0
            return max(1, int(recent[0] + self.window_seconds - now) + 1)

    def record_failure(self, key):
        with self._lock:
            now = self._clock()
            self._recent(key, now)
            self._failures.setdefault(key, []).append(now)

    def reset(self, key):
        with self._lock:
            self._failures.pop(key, None)
