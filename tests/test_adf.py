# Python imports
from typing import ClassVar

# Internal imports
from jira_genie.adf import adf_to_markdown, markdown_to_adf


class TestBlockNodes:
    """Block-level Markdown elements → ADF top-level nodes."""
    def test_plain_text(self):
        result = markdown_to_adf("Hello world")
        assert result == {
            "type": "doc",
            "version": 1,
            "content": [
                {"type": "paragraph", "content": [{"type": "text", "text": "Hello world"}]},
            ],
        }

    def test_heading_levels(self):
        for level in range(1, 7):
            result = markdown_to_adf(f"{'#' * level} Title")
            assert result["content"] == [
                {"type": "heading", "attrs": {"level": level}, "content": [{"type": "text", "text": "Title"}]},
            ]

    def test_code_block_with_language(self):
        result = markdown_to_adf("```python\nprint('hi')\n```")
        assert result["content"] == [
            {
                "type": "codeBlock",
                "attrs": {"language": "python"},
                "content": [{"type": "text", "text": "print('hi')\n"}],
            },
        ]

    def test_code_block_without_language(self):
        result = markdown_to_adf("```\nplain code\n```")
        assert result["content"] == [
            {"type": "codeBlock", "content": [{"type": "text", "text": "plain code\n"}]},
        ]

    def test_blockquote(self):
        result = markdown_to_adf("> quoted text")
        assert result["content"] == [
            {"type": "blockquote", "content": [
                {"type": "paragraph", "content": [{"type": "text", "text": "quoted text"}]},
            ]},
        ]

    def test_thematic_break(self):
        result = markdown_to_adf("---")
        assert result["content"] == [{"type": "rule"}]

    def test_multiple_blocks(self):
        result = markdown_to_adf("# Title\n\nA paragraph.\n\n---")
        assert result["content"] == [
            {"type": "heading", "attrs": {"level": 1}, "content": [{"type": "text", "text": "Title"}]},
            {"type": "paragraph", "content": [{"type": "text", "text": "A paragraph."}]},
            {"type": "rule"},
        ]




class TestInlineMarks:
    """Inline Markdown formatting → ADF text nodes with marks."""

    def test_bold(self):
        result = markdown_to_adf("**bold**")
        assert result["content"] == [
            {"type": "paragraph", "content": [
                {"type": "text", "text": "bold", "marks": [{"type": "strong"}]},
            ]},
        ]

    def test_italic(self):
        result = markdown_to_adf("*italic*")
        assert result["content"] == [
            {"type": "paragraph", "content": [
                {"type": "text", "text": "italic", "marks": [{"type": "em"}]},
            ]},
        ]

    def test_inline_code(self):
        result = markdown_to_adf("`code`")
        assert result["content"] == [
            {"type": "paragraph", "content": [
                {"type": "text", "text": "code", "marks": [{"type": "code"}]},
            ]},
        ]

    def test_strikethrough(self):
        result = markdown_to_adf("~~deleted~~")
        assert result["content"] == [
            {"type": "paragraph", "content": [
                {"type": "text", "text": "deleted", "marks": [{"type": "strike"}]},
            ]},
        ]

    def test_nested_bold_and_italic(self):
        result = markdown_to_adf("***both***")
        marks = result["content"][0]["content"][0]["marks"]
        mark_types = {m["type"] for m in marks}
        assert mark_types == {"strong", "em"}

    def test_mixed_inline(self):
        result = markdown_to_adf("plain **bold** plain")
        content = result["content"][0]["content"]
        assert content[0] == {"type": "text", "text": "plain "}
        assert content[1] == {"type": "text", "text": "bold", "marks": [{"type": "strong"}]}
        assert content[2] == {"type": "text", "text": " plain"}


class TestLinks:
    """Markdown links → ADF text nodes with link marks."""

    def test_simple_link(self):
        result = markdown_to_adf("[click here](https://example.com)")
        assert result["content"] == [
            {"type": "paragraph", "content": [
                {"type": "text", "text": "click here", "marks": [
                    {"type": "link", "attrs": {"href": "https://example.com"}},
                ]},
            ]},
        ]

    def test_bold_link(self):
        result = markdown_to_adf("**[bold link](https://example.com)**")
        marks = result["content"][0]["content"][0]["marks"]
        mark_types = {m["type"] for m in marks}
        assert mark_types == {"strong", "link"}


class TestFullDocument:
    """End-to-end: a realistic Markdown document using all supported features at once.

    The expected ADF dict below serves as a reference for the complete mapping:
    heading, paragraph, bold, italic, ordered list, inline code, link,
    blockquote, strikethrough, rule, code block, bullet list, nested list.
    """

    MARKDOWN = (
        "# Bug Report\n"
        "\n"
        "This is a **critical** issue with *authentication*.\n"
        "\n"
        "## Steps to reproduce\n"
        "\n"
        "1. Login with `admin` credentials\n"
        "2. Call the [API](https://api.example.com/auth)\n"
        "\n"
        "## Workaround\n"
        "\n"
        "> Use the ~~old~~ new endpoint.\n"
        "\n"
        "---\n"
        "\n"
        "```python\ntoken = refresh()\n```\n"
        "\n"
        "- Check **bold in list**\n"
        "  - Nested item\n"
    )

    EXPECTED_ADF: ClassVar[dict] = {
        "type": "doc",
        "version": 1,
        "content": [
            # --- heading ---
            {"type": "heading", "attrs": {"level": 1}, "content": [
                {"type": "text", "text": "Bug Report"},
            ]},
            # --- paragraph with bold + italic ---
            {"type": "paragraph", "content": [
                {"type": "text", "text": "This is a "},
                {"type": "text", "text": "critical", "marks": [{"type": "strong"}]},
                {"type": "text", "text": " issue with "},
                {"type": "text", "text": "authentication", "marks": [{"type": "em"}]},
                {"type": "text", "text": "."},
            ]},
            # --- h2 ---
            {"type": "heading", "attrs": {"level": 2}, "content": [
                {"type": "text", "text": "Steps to reproduce"},
            ]},
            # --- ordered list with inline code + link ---
            {"type": "orderedList", "content": [
                {"type": "listItem", "content": [
                    {"type": "paragraph", "content": [
                        {"type": "text", "text": "Login with "},
                        {"type": "text", "text": "admin", "marks": [{"type": "code"}]},
                        {"type": "text", "text": " credentials"},
                    ]},
                ]},
                {"type": "listItem", "content": [
                    {"type": "paragraph", "content": [
                        {"type": "text", "text": "Call the "},
                        {"type": "text", "text": "API", "marks": [
                            {"type": "link", "attrs": {"href": "https://api.example.com/auth"}},
                        ]},
                    ]},
                ]},
            ]},
            # --- h2 ---
            {"type": "heading", "attrs": {"level": 2}, "content": [
                {"type": "text", "text": "Workaround"},
            ]},
            # --- blockquote with strikethrough ---
            {"type": "blockquote", "content": [
                {"type": "paragraph", "content": [
                    {"type": "text", "text": "Use the "},
                    {"type": "text", "text": "old", "marks": [{"type": "strike"}]},
                    {"type": "text", "text": " new endpoint."},
                ]},
            ]},
            # --- rule ---
            {"type": "rule"},
            # --- code block with language ---
            {"type": "codeBlock", "content": [
                {"type": "text", "text": "token = refresh()\n"},
            ], "attrs": {"language": "python"}},
            # --- bullet list with bold + nested list ---
            {"type": "bulletList", "content": [
                {"type": "listItem", "content": [
                    {"type": "paragraph", "content": [
                        {"type": "text", "text": "Check "},
                        {"type": "text", "text": "bold in list", "marks": [{"type": "strong"}]},
                    ]},
                    {"type": "bulletList", "content": [
                        {"type": "listItem", "content": [
                            {"type": "paragraph", "content": [
                                {"type": "text", "text": "Nested item"},
                            ]},
                        ]},
                    ]},
                ]},
            ]},
        ],
    }

    def test_all_features(self):
        assert markdown_to_adf(self.MARKDOWN) == self.EXPECTED_ADF


class TestLists:
    """Markdown lists → ADF bulletList/orderedList with listItem nodes."""

    def test_bullet_list(self):
        result = markdown_to_adf("- alpha\n- beta")
        assert result["content"] == [
            {"type": "bulletList", "content": [
                {"type": "listItem", "content": [
                    {"type": "paragraph", "content": [{"type": "text", "text": "alpha"}]},
                ]},
                {"type": "listItem", "content": [
                    {"type": "paragraph", "content": [{"type": "text", "text": "beta"}]},
                ]},
            ]},
        ]

    def test_ordered_list(self):
        result = markdown_to_adf("1. first\n2. second")
        assert result["content"] == [
            {"type": "orderedList", "content": [
                {"type": "listItem", "content": [
                    {"type": "paragraph", "content": [{"type": "text", "text": "first"}]},
                ]},
                {"type": "listItem", "content": [
                    {"type": "paragraph", "content": [{"type": "text", "text": "second"}]},
                ]},
            ]},
        ]

    def test_nested_list(self):
        result = markdown_to_adf("- parent\n  - child")
        outer = result["content"][0]
        assert outer["type"] == "bulletList"
        first_item = outer["content"][0]
        assert first_item["type"] == "listItem"
        # First item has paragraph + nested list
        assert first_item["content"][0]["type"] == "paragraph"
        assert first_item["content"][1]["type"] == "bulletList"
        nested_item = first_item["content"][1]["content"][0]
        assert nested_item["content"][0] == {"type": "paragraph", "content": [{"type": "text", "text": "child"}]}


class TestAdfToText:
    """ADF → readable text round-trip."""

    def test_plain_paragraph(self):
        adf = {"type": "doc", "version": 1, "content": [
            {"type": "paragraph", "content": [{"type": "text", "text": "Hello world"}]},
        ]}
        assert adf_to_markdown(adf) == "Hello world"

    def test_heading(self):
        adf = {"type": "doc", "version": 1, "content": [
            {"type": "heading", "attrs": {"level": 2}, "content": [{"type": "text", "text": "Title"}]},
        ]}
        assert adf_to_markdown(adf) == "## Title"

    def test_bold_and_code_marks(self):
        adf = {"type": "doc", "version": 1, "content": [
            {"type": "paragraph", "content": [
                {"type": "text", "text": "bold", "marks": [{"type": "strong"}]},
                {"type": "text", "text": " and "},
                {"type": "text", "text": "code", "marks": [{"type": "code"}]},
            ]},
        ]}
        assert adf_to_markdown(adf) == "**bold** and `code`"

    def test_bullet_list(self):
        adf = {"type": "doc", "version": 1, "content": [
            {"type": "bulletList", "content": [
                {"type": "listItem", "content": [
                    {"type": "paragraph", "content": [{"type": "text", "text": "one"}]},
                ]},
                {"type": "listItem", "content": [
                    {"type": "paragraph", "content": [{"type": "text", "text": "two"}]},
                ]},
            ]},
        ]}
        assert adf_to_markdown(adf) == "- one\n- two"

    def test_code_block(self):
        adf = {"type": "doc", "version": 1, "content": [
            {"type": "codeBlock", "attrs": {"language": "python"}, "content": [
                {"type": "text", "text": "print('hi')"},
            ]},
        ]}
        assert adf_to_markdown(adf) == "```python\nprint('hi')\n```"

    def test_link_mark(self):
        adf = {"type": "doc", "version": 1, "content": [
            {"type": "paragraph", "content": [
                {"type": "text", "text": "click here", "marks": [
                    {"type": "link", "attrs": {"href": "https://example.com"}},
                ]},
            ]},
        ]}
        assert adf_to_markdown(adf) == "[click here](https://example.com)"

    def test_none_returns_empty(self):
        assert adf_to_markdown(None) == ""

    def test_roundtrip_markdown(self):
        """Markdown → ADF → text should preserve key content."""
        md = "## Problem\n\nUsers get **401 errors** after refresh."
        adf = markdown_to_adf(md)
        text = adf_to_markdown(adf)
        assert "## Problem" in text
        assert "**401 errors**" in text
