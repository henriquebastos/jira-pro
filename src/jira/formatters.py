def format_issue(raw):
    """Raw Jira issue → clean {key, summary, status, assignee, ...}"""
    fields = raw.get("fields", {})
    result = {
        "key": raw["key"],
        "summary": fields.get("summary"),
        "status": (fields.get("status") or {}).get("name"),
        "assignee": (fields.get("assignee") or {}).get("displayName"),
        "priority": (fields.get("priority") or {}).get("name"),
        "type": (fields.get("issuetype") or {}).get("name"),
    }
    description = fields.get("description")
    if description and isinstance(description, dict):
        from jira.adf import adf_to_markdown
        result["description"] = adf_to_markdown(description)
    else:
        result["description"] = None
    return result


def format_issue_list(raw_issues):
    """List of raw issues → list of clean dicts"""
    return [format_issue(r) for r in raw_issues]


def format_sprint(raw):
    """Raw sprint → {id, name, state, startDate, endDate}"""
    return {
        "id": raw["id"],
        "name": raw["name"],
        "state": raw["state"],
        "startDate": raw.get("startDate"),
        "endDate": raw.get("endDate"),
    }


def format_transition(raw):
    """Raw transition → {id, name, to_status}"""
    return {
        "id": raw["id"],
        "name": raw["name"],
        "to_status": raw["to"]["name"],
    }
