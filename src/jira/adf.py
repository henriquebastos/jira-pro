# Pip imports
import mistune


def convert_node(node):
    """Convert a single mistune AST node to an ADF node."""
    node_type = node["type"]

    if node_type == "paragraph":
        content = convert_inline(node.get("children", []))
        if content:
            return {"type": "paragraph", "content": content}
        return None

    if node_type == "heading":
        level = node["attrs"]["level"]
        content = convert_inline(node.get("children", []))
        result = {"type": "heading", "attrs": {"level": level}, "content": content}
        return result

    if node_type == "block_code":
        text = node["raw"]
        info = node.get("attrs", {}).get("info")
        result = {"type": "codeBlock", "content": [{"type": "text", "text": text}]}
        if info:
            result["attrs"] = {"language": info}
        return result

    if node_type == "block_quote":
        content = convert_children(node.get("children", []))
        if content:
            return {"type": "blockquote", "content": content}
        return None

    if node_type == "thematic_break":
        return {"type": "rule"}

    return None


def convert_children(nodes):
    """Convert a list of mistune AST nodes to ADF nodes, filtering blanks."""
    result = []
    for node in nodes:
        adf_node = convert_node(node)
        if adf_node:
            result.append(adf_node)
    return result


def convert_inline(children):
    """Convert a list of mistune inline AST nodes to ADF inline nodes."""
    result = []
    for child in children:
        child_type = child["type"]
        if child_type == "text":
            result.append({"type": "text", "text": child["raw"]})
    return result


def markdown_to_adf(text) -> dict:
    """Convert a Markdown string to an Atlassian Document Format (ADF) document."""
    md = mistune.create_markdown(renderer="ast")
    ast = md(text)
    content = convert_children(ast)
    return {"type": "doc", "version": 1, "content": content}
