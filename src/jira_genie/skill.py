"""Install/uninstall the jira agent skill for AI coding tools."""

from pathlib import Path
import shutil

TARGETS = {
    "agents": {
        "label": "Agent Skills standard",
        "detect": "~/.agents",
        "dest": "~/.agents/skills/jira-genie",
    },
    "pi": {
        "label": "Pi",
        "detect": "~/.pi",
        "dest": "~/.pi/agent/skills/jira-genie",
    },
    "claude": {
        "label": "Claude Code",
        "detect": "~/.claude",
        "dest": "~/.claude/skills/jira-genie",
    },
    "codex": {
        "label": "Codex",
        "detect": "~/.codex",
        "dest": "~/.codex/skills/jira-genie",
    },
}


def _bundled_skill() -> Path:
    """Return path to the bundled SKILL.md."""
    return Path(__file__).parent / "skills" / "jira-genie" / "SKILL.md"


def _dest(target: str) -> Path:
    return Path(TARGETS[target]["dest"]).expanduser()


def detect_targets() -> list[str]:
    """Return target names whose config directories exist."""
    found = []
    for name, info in TARGETS.items():
        if Path(info["detect"]).expanduser().is_dir():
            found.append(name)
    return found


def install(targets: list[str], *, dry_run: bool = False) -> list[dict]:
    """Install SKILL.md to each target. Returns list of action dicts."""
    source = _bundled_skill()
    if not source.exists():
        raise FileNotFoundError(f"Bundled skill not found: {source}")

    actions = []
    for name in targets:
        dest_dir = _dest(name)
        dest_file = dest_dir / "SKILL.md"
        exists = dest_file.exists()
        action = {
            "target": name,
            "label": TARGETS[name]["label"],
            "path": str(dest_file),
            "action": "overwrite" if exists else "create",
        }
        if not dry_run:
            dest_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, dest_file)
        actions.append(action)
    return actions


def uninstall(targets: list[str], *, dry_run: bool = False) -> list[dict]:
    """Remove installed skill from each target. Returns list of action dicts."""
    actions = []
    for name in targets:
        dest_dir = _dest(name)
        if not dest_dir.exists():
            continue
        action = {
            "target": name,
            "label": TARGETS[name]["label"],
            "path": str(dest_dir),
            "action": "remove",
        }
        if not dry_run:
            shutil.rmtree(dest_dir)
        actions.append(action)
    return actions
