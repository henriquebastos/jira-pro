# Python imports
import json
from pathlib import Path


def complete_template(prefix, templates_dir):
    """Complete template names from templates directory."""
    d = Path(templates_dir)
    if not d.exists():
        return []
    names = [f.stem for f in d.glob("*.json")]
    return [n for n in sorted(names) if n.startswith(prefix)]


def complete_field_set(prefix, schema_fields, schema_projects):
    """Complete --set field names and enum values.

    - 'sto' → ['story_points=']
    - 'priority=' → ['priority=P0: Critical', 'priority=P1: High', ...]
    - 'priority=P1' → ['priority=P1: High']
    """
    if "=" in prefix:
        field_name, value_prefix = prefix.split("=", 1)
        # Look up allowed values for this field
        allowed = _find_allowed_values(field_name, schema_fields, schema_projects)
        if not allowed:
            return []
        return [f"{field_name}={v}" for v in allowed if v.startswith(value_prefix)]
    else:
        # Complete field names
        return [f"{k}=" for k in sorted(schema_fields) if k.startswith(prefix)]


def _load_schema():
    """Load schema from the default instance. Returns (fields, projects) or ({}, {})."""
    try:
        from jira_genie.config import discover_instance_dir
        instance_dir = discover_instance_dir()
        schema_path = instance_dir / "schema.json"
        if not schema_path.exists():
            return {}, {}
        schema = json.loads(schema_path.read_text())
        return schema.get("fields", {}), schema.get("projects", {})
    except Exception:
        return {}, {}


def _get_templates_dir():
    """Get templates directory for the default instance."""
    try:
        from jira_genie.config import discover_instance_dir
        return discover_instance_dir() / "templates"
    except Exception:
        return Path("/nonexistent")


class TemplateCompleter:
    """argcomplete-compatible completer for --template."""

    def __call__(self, prefix, **kwargs):
        return complete_template(prefix, _get_templates_dir())


class FieldSetCompleter:
    """argcomplete-compatible completer for --set key=value."""

    def __call__(self, prefix, **kwargs):
        schema_fields, schema_projects = _load_schema()
        return complete_field_set(prefix, schema_fields, schema_projects)


def _find_allowed_values(field_name, schema_fields, schema_projects):
    """Find allowed values for a field by scanning all project type schemas."""
    field_info = schema_fields.get(field_name)
    if not field_info:
        return []
    field_id = field_info["id"]

    # Scan all projects/types for allowed values on this field
    for project_data in schema_projects.values():
        for type_data in project_data.get("types", {}).values():
            field_schema = type_data.get("fields", {}).get(field_id, {})
            if "allowed" in field_schema:
                return field_schema["allowed"]

    return []
