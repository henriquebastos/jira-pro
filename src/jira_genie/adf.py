# Pip imports
import mistune
from mistune.plugins.formatting import strikethrough

# ── ADF → Markdown ─────────────────────────────────────────────────────────────

def adf_to_markdown(node) -> str:
    """Convert an ADF document to readable Markdown."""
    if not isinstance(node, dict):
        return ""
    return "".join(_render(node))


def _render(node):
    """Yield markdown fragments for an ADF node."""
    children = node.get("content", [])

    match node.get("type", ""):
        case "doc":
            for i, child in enumerate(children):
                if i > 0:
                    yield "\n\n"
                yield from _render(child)

        case "text":
            text = node.get("text", "")
            for mark in node.get("marks", []):
                match mark.get("type", ""):
                    case "strong":
                        text = f"**{text}**"
                    case "em":
                        text = f"*{text}*"
                    case "code":
                        text = f"`{text}`"
                    case "strike":
                        text = f"~~{text}~~"
                    case "link":
                        url = mark.get("attrs", {}).get("href", "")
                        text = f"[{text}]({url})"
            yield text

        case "paragraph" | "listItem":
            for i, child in enumerate(children):
                if i > 0 and node.get("type") == "listItem":
                    yield "\n"
                yield from _render(child)

        case "heading":
            level = node.get("attrs", {}).get("level", 1)
            yield f"{'#' * level} "
            for child in children:
                yield from _render(child)

        case "codeBlock":
            lang = node.get("attrs", {}).get("language", "")
            yield f"```{lang}\n"
            for child in children:
                yield from _render(child)
            yield "\n```"

        case "blockquote":
            inner = "".join(fragment for child in children for fragment in _render(child))
            yield "\n".join(f"> {line}" for line in inner.split("\n"))

        case "rule":
            yield "---"

        case "bulletList" | "orderedList" as list_type:
            for i, child in enumerate(children):
                if i > 0:
                    yield "\n"
                yield f"{i + 1}. " if list_type == "orderedList" else "- "
                yield from _render(child)

        case _:
            for child in children:
                yield from _render(child)


# ── Markdown → ADF ─────────────────────────────────────────────────────────────

# Mistune inline type → ADF mark type
INLINE_MARKS = {
    "strong": "strong",
    "emphasis": "em",
    "codespan": "code",
    "strikethrough": "strike",
}


def markdown_to_adf(text) -> dict:
    """Convert a Markdown string to an Atlassian Document Format (ADF) document."""
    md = mistune.create_markdown(renderer="ast", plugins=[strikethrough])
    ast = md(text)
    content = convert_children(ast)
    return {"type": "doc", "version": 1, "content": content}


def convert_children(nodes):
    """Convert a list of mistune AST nodes to ADF nodes, filtering blanks."""
    return [adf_node for node in nodes if (adf_node := convert_node(node))]


def convert_node(node):
    """Convert a single mistune AST node to an ADF node."""
    children = node.get("children", [])

    match node["type"]:
        case "paragraph" | "block_text":
            content = convert_inline(children)
            return {"type": "paragraph", "content": content} if content else None

        case "heading":
            level = node["attrs"]["level"]
            return {"type": "heading", "attrs": {"level": level}, "content": convert_inline(children)}

        case "block_code":
            result = {"type": "codeBlock", "content": [{"type": "text", "text": node["raw"]}]}
            info = node.get("attrs", {}).get("info")
            if info:
                result["attrs"] = {"language": info}
            return result

        case "block_quote":
            content = convert_children(children)
            return {"type": "blockquote", "content": content} if content else None

        case "thematic_break":
            return {"type": "rule"}

        case "list":
            ordered = node.get("attrs", {}).get("ordered", False)
            items = convert_children(children)
            if items:
                return {"type": "orderedList" if ordered else "bulletList", "content": items}
            return None

        case "list_item":
            content = convert_children(children)
            return {"type": "listItem", "content": content} if content else None

        case _:
            return None


def convert_inline(children, marks=None):
    """Convert a list of mistune inline AST nodes to ADF inline nodes."""
    result = []
    marks = marks or []

    for child in children:
        match child["type"]:
            case "text":
                node = {"type": "text", "text": child["raw"]}
                if marks:
                    node["marks"] = list(marks)
                result.append(node)

            case "codespan":
                result.append({"type": "text", "text": child["raw"], "marks": [*marks, {"type": "code"}]})

            case "link":
                url = child.get("attrs", {}).get("url", "")
                link_mark = {"type": "link", "attrs": {"href": url}}
                result.extend(convert_inline(child.get("children", []), [*marks, link_mark]))

            case mark_type if mark_type in INLINE_MARKS:
                mark = {"type": INLINE_MARKS[mark_type]}
                result.extend(convert_inline(child.get("children", []), [*marks, mark]))

    return result
