# Python imports
import json

# Pip imports
import pytest

# Internal imports
from jira_genie.config import ConfigError, discover_instance_dir


def make_instance(base_dir, cloud_id, site):
    """Create a fake instance directory with config."""
    d = base_dir / cloud_id
    d.mkdir(parents=True)
    (d / "config.json").write_text(json.dumps({"cloud_id": cloud_id, "site": site}))
    return d


class TestDiscoverInstanceDir:
    def test_auto_detect_single_instance(self, tmp_path):
        instance = make_instance(tmp_path, "abc-123", "acme.atlassian.net")
        result = discover_instance_dir(base_dir=tmp_path)
        assert result == instance

    def test_match_by_instance_arg(self, tmp_path):
        make_instance(tmp_path, "aaa", "acme.atlassian.net")
        other = make_instance(tmp_path, "bbb", "other.atlassian.net")
        result = discover_instance_dir(instance="other", base_dir=tmp_path)
        assert result == other

    def test_match_by_env_var(self, tmp_path, monkeypatch):
        make_instance(tmp_path, "aaa", "acme.atlassian.net")
        other = make_instance(tmp_path, "bbb", "other.atlassian.net")
        monkeypatch.setenv("JIRA_INSTANCE", "other")
        result = discover_instance_dir(base_dir=tmp_path)
        assert result == other

    def test_match_by_default_config(self, tmp_path):
        make_instance(tmp_path, "aaa", "acme.atlassian.net")
        make_instance(tmp_path, "bbb", "other.atlassian.net")
        (tmp_path / "config.json").write_text(json.dumps({"default": "bbb"}))
        result = discover_instance_dir(base_dir=tmp_path)
        assert result == tmp_path / "bbb"

    def test_error_when_multiple_and_no_selection(self, tmp_path):
        make_instance(tmp_path, "aaa", "acme.atlassian.net")
        make_instance(tmp_path, "bbb", "other.atlassian.net")
        with pytest.raises(ConfigError, match="Multiple instances"):
            discover_instance_dir(base_dir=tmp_path)

    def test_error_when_instance_not_found(self, tmp_path):
        make_instance(tmp_path, "aaa", "acme.atlassian.net")
        with pytest.raises(ConfigError, match="No instance matching"):
            discover_instance_dir(instance="nope", base_dir=tmp_path)
