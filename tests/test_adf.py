# Internal imports
from jira.adf import markdown_to_adf


class TestBlockNodes:
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


