# Python imports
from datetime import UTC, datetime

# Pip imports
import pytest

# Internal imports
from jira_genie.cache import FileCache


@pytest.fixture()
def cache(tmp_path):
    return FileCache(tmp_path / "cache.json")


class TestFileCacheSetAndGet:
    def test_set_and_get_round_trip(self, cache):
        cache.set("token", "abc123", 3600)
        assert cache.get("token") == "abc123"

    def test_get_returns_default_when_file_missing(self, cache):
        assert cache.get("token") is None
        assert cache.get("token", "fallback") == "fallback"

    def test_get_returns_default_when_key_missing(self, cache):
        cache.set("other", "value", 3600)
        assert cache.get("token") is None


class TestFileCacheExpiry:
    def test_get_returns_value_when_not_expired(self, tmp_path):
        fixed = datetime(2026, 1, 1, tzinfo=UTC)
        cache = FileCache(tmp_path / "cache.json", now=lambda: fixed)
        cache.set("token", "abc", 3600)
        assert cache.get("token") == "abc"

    def test_get_returns_default_when_expired(self, tmp_path):
        t1 = datetime(2026, 1, 1, tzinfo=UTC)
        t2 = datetime(2026, 1, 1, hour=2, tzinfo=UTC)
        times = iter([t1, t2])
        cache = FileCache(tmp_path / "cache.json", now=lambda: next(times))
        cache.set("token", "abc", 3600)  # expires at t1 + 1h
        assert cache.get("token") is None  # t2 is 2h later

    def test_set_overwrites_existing_preserves_others(self, tmp_path):
        cache = FileCache(tmp_path / "cache.json")
        cache.set("a", "1", 3600)
        cache.set("b", "2", 3600)
        cache.set("a", "updated", 3600)
        assert cache.get("a") == "updated"
        assert cache.get("b") == "2"

    def test_set_creates_parent_dirs(self, tmp_path):
        cache = FileCache(tmp_path / "deep" / "nested" / "cache.json")
        cache.set("token", "abc", 3600)
        assert cache.get("token") == "abc"

    def test_no_expiry_means_never_expires(self, tmp_path):
        t1 = datetime(2026, 1, 1, tzinfo=UTC)
        t2 = datetime(2099, 12, 31, tzinfo=UTC)
        times = iter([t1, t2])
        cache = FileCache(tmp_path / "cache.json", now=lambda: next(times))
        cache.set("token", "abc", None)  # no expiry
        assert cache.get("token") == "abc"
