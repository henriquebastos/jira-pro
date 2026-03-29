# Pip imports
import pytest

# Internal imports
from jira_genie.templates import (
    TemplateError,
    build_issue_fields,
    clear_default,
    delete_template,
    get_default,
    list_templates,
    load_template,
    save_template,
    set_default,
)


class TestTemplateCRUD:
    def test_save_and_load_round_trip(self, tmp_path):
        data = {"project": "DEV", "issuetype": "Task"}
        save_template("bug", data, tmp_path)
        assert load_template("bug", tmp_path) == data

    def test_list_templates(self, tmp_path):
        save_template("bug", {"a": 1}, tmp_path)
        save_template("feature", {"b": 2}, tmp_path)
        result = list_templates(tmp_path)
        assert sorted(result) == ["bug", "feature"]

    def test_list_returns_empty_when_no_dir(self, tmp_path):
        assert list_templates(tmp_path / "nonexistent") == []

    def test_load_raises_for_missing(self, tmp_path):
        with pytest.raises(TemplateError, match="not found"):
            load_template("nope", tmp_path)

    def test_save_overwrites(self, tmp_path):
        save_template("t", {"v": 1}, tmp_path)
        save_template("t", {"v": 2}, tmp_path)
        assert load_template("t", tmp_path) == {"v": 2}

    def test_delete(self, tmp_path):
        save_template("t", {"v": 1}, tmp_path)
        delete_template("t", tmp_path)
        assert list_templates(tmp_path) == []

    def test_delete_raises_for_missing(self, tmp_path):
        with pytest.raises(TemplateError, match="not found"):
            delete_template("nope", tmp_path)


class TestDefaultTemplate:
    def test_set_and_get(self, tmp_path):
        config_file = tmp_path / "config.json"
        set_default("bug", config_file)
        assert get_default(config_file) == "bug"

    def test_get_returns_none_when_unset(self, tmp_path):
        assert get_default(tmp_path / "config.json") is None

    def test_clear(self, tmp_path):
        config_file = tmp_path / "config.json"
        set_default("bug", config_file)
        clear_default(config_file)
        assert get_default(config_file) is None


SCHEMA = {
    "summary": {"id": "summary", "type": "string", "system": True},
    "priority": {"id": "priority", "type": "priority", "system": True},
    "story_points": {"id": "customfield_10036", "type": "number", "name": "Story Points"},
    "team": {"id": "customfield_10001", "type": "option", "name": "Team"},
    "labels": {"id": "labels", "type": "array", "system": True},
}


class TestBuildIssueFields:
    def test_template_only(self):
        result = build_issue_fields({"summary": "Fix"}, None, {}, SCHEMA)
        assert result == {"summary": "Fix"}

    def test_json_overrides_template(self):
        result = build_issue_fields(
            {"summary": "Old", "priority": "P3: Low"},
            {"summary": "New"},
            {},
            SCHEMA,
        )
        assert result["summary"] == "New"
        assert result["priority"] == {"name": "P3: Low"}

    def test_cli_flags_win(self):
        result = build_issue_fields(
            {"summary": "Template"},
            {"summary": "JSON"},
            {"summary": "CLI"},
            SCHEMA,
        )
        assert result == {"summary": "CLI"}

    def test_shallow_override_replaces_arrays(self):
        result = build_issue_fields(
            {"labels": ["old"]},
            {"labels": ["new"]},
            {},
            SCHEMA,
        )
        assert result == {"labels": ["new"]}

    def test_no_template(self):
        result = build_issue_fields(None, {"summary": "Only JSON"}, {}, SCHEMA)
        assert result == {"summary": "Only JSON"}

    def test_all_empty(self):
        result = build_issue_fields(None, None, {}, SCHEMA)
        assert result == {}

    def test_full_pipeline(self):
        result = build_issue_fields(
            {"summary": "Template", "team": "Backend", "labels": ["old"]},
            {"story_points": 5},
            {"labels": ["new"]},
            SCHEMA,
        )
        assert result == {
            "summary": "Template",
            "customfield_10001": {"value": "Backend"},
            "customfield_10036": 5,
            "labels": ["new"],
        }
