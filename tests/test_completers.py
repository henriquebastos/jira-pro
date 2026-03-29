# Python imports

# Internal imports
from jira_genie.completers import complete_field_set, complete_template

SCHEMA_FIELDS = {
    "summary": {"id": "summary", "type": "string", "system": True},
    "priority": {"id": "priority", "type": "priority", "system": True},
    "story_points": {"id": "customfield_10036", "type": "number", "name": "Story Points"},
    "team": {"id": "customfield_10001", "type": "option", "name": "Team"},
    "labels": {"id": "labels", "type": "array", "system": True},
}

SCHEMA_PROJECTS = {
    "DEV": {
        "types": {
            "Task": {
                "fields": {
                    "priority": {
                        "type": "priority",
                        "allowed": ["P0: Critical", "P1: High", "P2: Medium", "P3: Low"],
                    },
                    "customfield_10001": {
                        "type": "option",
                        "allowed": ["Backend", "Frontend", "Platform"],
                    },
                }
            }
        }
    }
}


class TestCompleteTemplate:
    def test_lists_templates(self, tmp_path):
        (tmp_path / "instant-right.json").write_text("{}")
        (tmp_path / "instant-work.json").write_text("{}")
        (tmp_path / "bug.json").write_text("{}")
        result = complete_template("", tmp_path)
        assert sorted(result) == ["bug", "instant-right", "instant-work"]

    def test_filters_by_prefix(self, tmp_path):
        (tmp_path / "instant-right.json").write_text("{}")
        (tmp_path / "instant-work.json").write_text("{}")
        (tmp_path / "bug.json").write_text("{}")
        result = complete_template("inst", tmp_path)
        assert sorted(result) == ["instant-right", "instant-work"]

    def test_empty_dir(self, tmp_path):
        assert complete_template("", tmp_path) == []


class TestCompleteFieldSet:
    def test_completes_field_names(self):
        result = complete_field_set("", SCHEMA_FIELDS, SCHEMA_PROJECTS)
        assert "summary=" in result
        assert "priority=" in result
        assert "story_points=" in result

    def test_filters_field_names_by_prefix(self):
        result = complete_field_set("sto", SCHEMA_FIELDS, SCHEMA_PROJECTS)
        assert result == ["story_points="]

    def test_completes_enum_values_after_equals(self):
        result = complete_field_set("priority=P1", SCHEMA_FIELDS, SCHEMA_PROJECTS)
        assert "priority=P1: High" in result

    def test_completes_all_enum_values(self):
        result = complete_field_set("priority=", SCHEMA_FIELDS, SCHEMA_PROJECTS)
        assert "priority=P0: Critical" in result
        assert "priority=P3: Low" in result

    def test_completes_custom_option_values(self):
        result = complete_field_set("team=", SCHEMA_FIELDS, SCHEMA_PROJECTS)
        assert "team=Backend" in result
        assert "team=Frontend" in result

    def test_no_values_for_string_field(self):
        result = complete_field_set("summary=", SCHEMA_FIELDS, SCHEMA_PROJECTS)
        assert result == []

    def test_no_match(self):
        result = complete_field_set("zzz", SCHEMA_FIELDS, SCHEMA_PROJECTS)
        assert result == []
