# Python imports
import json
from pathlib import Path

# Internal imports
from jira_genie.schema import resolve_fields


class TemplateError(Exception):
    pass


def list_templates(templates_dir):
    """List template names from directory."""
    d = Path(templates_dir)
    if not d.exists():
        return []
    return [f.stem for f in sorted(d.glob("*.json"))]


def load_template(name, templates_dir):
    """Read and parse a template JSON file."""
    path = Path(templates_dir) / f"{name}.json"
    if not path.exists():
        raise TemplateError(f"Template '{name}' not found")
    return json.loads(path.read_text())


def save_template(name, data, templates_dir):
    """Write a template JSON file, creating dir if needed."""
    d = Path(templates_dir)
    d.mkdir(parents=True, exist_ok=True)
    (d / f"{name}.json").write_text(json.dumps(data, indent=2))


def delete_template(name, templates_dir):
    """Remove a template file."""
    path = Path(templates_dir) / f"{name}.json"
    if not path.exists():
        raise TemplateError(f"Template '{name}' not found")
    path.unlink()


def get_default(config_file):
    """Read default template name from config file."""
    path = Path(config_file)
    if not path.exists():
        return None
    config = json.loads(path.read_text())
    return config.get("default_template")


def set_default(name, config_file):
    """Write default template name to config file."""
    path = Path(config_file)
    config = json.loads(path.read_text()) if path.exists() else {}
    config["default_template"] = name
    path.write_text(json.dumps(config, indent=2))


def clear_default(config_file):
    """Remove default template from config file."""
    path = Path(config_file)
    if not path.exists():
        return
    config = json.loads(path.read_text())
    config.pop("default_template", None)
    path.write_text(json.dumps(config, indent=2))


def build_issue_fields(template, json_override, cli_flags, schema):
    """Pure merge: template | json | flags. Then resolve friendly names + expand values."""
    base = template or {}
    merged = {**base, **(json_override or {}), **cli_flags}
    return resolve_fields(merged, schema)
