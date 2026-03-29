# Python imports
import json
import os
from pathlib import Path

BASE_DIR = "~/.config/jira-genie"


class ConfigError(Exception):
    pass


def discover_instance_dir(instance=None, base_dir=BASE_DIR):
    """Resolve instance directory.

    Resolution order:
    1. instance arg (matches site name in config.json)
    2. JIRA_INSTANCE env var
    3. config.json -> 'default'
    4. Only one instance exists? Use it.
    5. Error
    """
    base = Path(base_dir).expanduser()

    if not base.exists():
        raise ConfigError(f"No config directory found at {base}. Run: jira auth login")

    instance = instance or os.environ.get("JIRA_INSTANCE")

    # Try matching by site name
    if instance:
        for d in base.iterdir():
            if not d.is_dir():
                continue
            config_file = d / "config.json"
            if not config_file.exists():
                continue
            config = json.loads(config_file.read_text())
            site = config.get("site", "")
            # Match against subdomain prefix: "acme" matches "acme.atlassian.net"
            if site.startswith(instance + ".") or site == instance:
                return d
        raise ConfigError(f"No instance matching '{instance}' found.")

    # Try default from base config
    base_config = base / "config.json"
    if base_config.exists():
        config = json.loads(base_config.read_text())
        default = config.get("default")
        if default:
            d = base / default
            if d.is_dir():
                return d

    # Auto-detect single instance
    dirs = [d for d in base.iterdir() if d.is_dir() and (d / "config.json").exists()]
    if len(dirs) == 1:
        return dirs[0]
    if len(dirs) == 0:
        raise ConfigError("No instances found. Run: jira auth login")

    raise ConfigError("Multiple instances found. Use --instance or set a default.")
