# Pip imports
import pytest

# Internal imports
from jira.templates import (
    TemplateError,
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
