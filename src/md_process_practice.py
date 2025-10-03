from pathlib import Path
import mistune
import re

markdown = mistune.create_markdown(renderer=None)

def parse_markdown(text):
    tokens = markdown.block.parse(text)
    chunks = []

    for token in tokens:
        ttype = token["type"]

        if ttype == "heading":
            level = token["level"]
            raw = "".join(child["raw"] for child in token["children"])
            chunks.append(f"[Heading {level}] {raw}")
        elif ttype == "paragraph":
            raw = "".join(child["raw"] for child in token["children"])
            chunks.append(raw)
        elif ttype == "list":
            items = []
            for child in token["children"]:
                raw = "".join(c["raw"] for c in child["children"])
                items.append(f"- {raw}")
            chunks.append("\n".join(items))
        else:
            chunks.append(str(token))
        
        return chunks
text = """
# Tiêu đề 1
 
Đây là một đoạn văn.

- Item 1
- Item 2

> Đây là blockquote

```python
print("Hello World")
"""

tokens = markdown.block.parse(text)
print(tokens)