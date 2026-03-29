# Python imports
from datetime import UTC, datetime, timedelta
import json
from pathlib import Path


def utc_now():
    return datetime.now(UTC)


class FileCache:
    """File-backed cache with expiry. Same .get()/.set() interface as ExpireValue."""

    def __init__(self, path, now=utc_now):
        self.path = Path(path).expanduser()
        self._now = now

    def get(self, key, default=None):
        """Read value from file, return default if missing or expired."""
        if not self.path.exists():
            return default
        data = json.loads(self.path.read_text())
        entry = data.get(key)
        if entry is None:
            return default
        if entry.get("expires_at") and self._now() >= datetime.fromisoformat(entry["expires_at"]):
            return default
        return entry["value"]

    def set(self, key, value, seconds_to_expire):
        """Write value to file with expiry."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        data = json.loads(self.path.read_text()) if self.path.exists() else {}
        expires_at = (self._now() + timedelta(seconds=seconds_to_expire)).isoformat() if seconds_to_expire else None
        data[key] = {"value": value, "expires_at": expires_at}
        self.path.write_text(json.dumps(data, indent=2))
