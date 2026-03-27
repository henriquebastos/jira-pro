# Python imports
from datetime import UTC, datetime
import json
from pathlib import Path
import re


def friendly_name(name):
    """'Story Points' → 'story_points'"""
    return re.sub(r"\s+", "_", name.strip()).lower()


def build_field_registry(raw_fields):
    """GET /rest/api/3/field response → {friendly_name: {id, type, name?, system?}}"""
    registry = {}
    for field in raw_fields:
        is_system = not field.get("custom", False)
        fname = field["id"] if is_system else friendly_name(field["name"])
        entry = {
            "id": field["id"],
            "type": field.get("schema", {}).get("type", "any"),
        }
        if is_system:
            entry["system"] = True
        else:
            entry["name"] = field["name"]
        registry[fname] = entry
    return registry


def build_type_schema(raw_createmeta):
    """Per-type createmeta → {id, required, fields: {name: {type, required, allowed?}}}

    Handles both dict-style fields (test fixtures) and list-style fields (real Jira API).
    """
    fields = {}
    required = []
    raw_fields = raw_createmeta.get("fields", {})

    # Real API returns a list of field dicts; test fixtures use a dict keyed by field ID
    if isinstance(raw_fields, list):
        items = [(f.get("fieldId", f.get("key")), f) for f in raw_fields]
    else:
        items = raw_fields.items()

    for field_id, field_data in items:
        entry = {
            "type": field_data.get("schema", {}).get("type", "any"),
            "required": field_data.get("required", False),
        }
        if field_data.get("allowedValues"):
            entry["allowed"] = [v.get("name", v.get("value", str(v))) for v in field_data["allowedValues"]]
        fields[field_id] = entry
        if field_data.get("required"):
            required.append(field_id)
    return {"id": raw_createmeta.get("id", ""), "required": required, "fields": fields}


# Field types that get value expansion
SYSTEM_OPTION_TYPES = {"priority", "status", "resolution"}
LINK_TYPES = {"issuelink"}
KEY_TYPES = {"project"}  # Types that expand string → {"key": value}
KEY_FIELDS = {"parent"}  # Specific field IDs that expand string → {"key": value}
NAME_TYPES = {"issuetype"}  # Types that expand string → {"name": value}
# System array fields where items are {"name": value}
NAMED_ARRAY_FIELDS = {"components", "fixVersions", "versions"}
# Fields that require Atlassian Document Format (ADF) — strings get auto-wrapped
ADF_FIELDS = {"description", "environment"}





def resolve_fields(friendly, schema):
    """Translate friendly names → Jira field IDs AND expand values to API format."""
    result = {}
    for key, value in friendly.items():
        field_info = schema.get(key)
        if not field_info:
            # Unknown field — pass through as-is
            result[key] = value
            continue

        field_id = field_info["id"]
        field_type = field_info.get("type", "any")

        # Already structured (dict or list of dicts) — don't double-wrap
        if isinstance(value, dict):
            result[field_id] = value
            continue

        # ADF fields: convert Markdown strings to ADF
        if field_id in ADF_FIELDS and isinstance(value, str):
            from jira.adf import markdown_to_adf
            result[field_id] = markdown_to_adf(value)
            continue

        # Expand based on type
        if field_type in LINK_TYPES and isinstance(value, str):
            result[field_id] = {"key": value}
        elif (field_type in KEY_TYPES or field_id in KEY_FIELDS) and isinstance(value, str):
            result[field_id] = {"key": value}
        elif field_type in NAME_TYPES and isinstance(value, str):
            result[field_id] = {"name": value}
        elif field_type in SYSTEM_OPTION_TYPES and isinstance(value, str):
            result[field_id] = {"name": value}
        elif field_type == "option" and not field_info.get("system") and isinstance(value, str):
            result[field_id] = {"value": value}
        elif field_id in NAMED_ARRAY_FIELDS and isinstance(value, list) and value and isinstance(value[0], str):
            result[field_id] = [{"name": v} for v in value]
        else:
            result[field_id] = value

    return result


def sync(session, instance_dir, project=None):
    """Fetch from API and write schema.json. I/O boundary.

    Without --project: syncs field list + discovers available project keys.
    With --project: also syncs type schemas (required fields, allowed values) for that project.
    Merges with existing schema — previously synced project schemas are preserved.
    """
    instance_dir = Path(instance_dir)

    # Load existing schema to merge with
    schema_path = instance_dir / "schema.json"
    existing = json.loads(schema_path.read_text()) if schema_path.exists() else {}

    # Fetch all fields
    raw_fields = session.get("rest/api/3/field").json()
    registry = build_field_registry(raw_fields)

    # Discover available projects
    raw_projects = session.get("rest/api/3/project").json()
    available_projects = [p["key"] for p in raw_projects]

    # Preserve existing project schemas, sync requested one
    projects = existing.get("projects", {})

    # Only fetch type schemas when a specific project is requested
    project_keys = [project] if project else []

    for proj_key in project_keys:
        resp = session.get(f"rest/api/3/issue/createmeta/{proj_key}/issuetypes")
        issue_types = resp.json().get("issueTypes", [])
        types = {}
        for itype in issue_types:
            type_resp = session.get(f"rest/api/3/issue/createmeta/{proj_key}/issuetypes/{itype['id']}")
            types[itype["name"]] = build_type_schema(type_resp.json())
        projects[proj_key] = {"types": types}

    schema = {
        "synced_at": datetime.now(UTC).isoformat(),
        "fields": registry,
        "available_projects": available_projects,
        "projects": projects,
    }
    schema_path.write_text(json.dumps(schema, indent=2))
