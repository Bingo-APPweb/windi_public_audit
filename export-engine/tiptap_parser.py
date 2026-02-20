"""
WINDI M3 Export Engine — Tiptap JSON Parser
============================================
Converts Tiptap/ProseMirror JSON document structure to:
  1. Plain text (for PDF body rendering via reportlab)
  2. HTML (for future rich export)

The Tiptap editor stores documents as nested JSON:
  {"type":"doc","content":[{"type":"paragraph","content":[{"type":"text","text":"Hello"}]}]}

This module recursively walks that tree and extracts human-readable content.

Three Dragons Protocol v1.1 — I9 Active
AI processes. Human decides. WINDI guarantees.
"""

import json
from typing import Union


def tiptap_to_plaintext(doc: Union[str, dict, list]) -> str:
    """
    Convert Tiptap JSON document to plain text.
    
    Args:
        doc: Either a JSON string, a dict (parsed JSON), or a list of nodes
        
    Returns:
        Human-readable plain text with paragraph breaks
    """
    # Handle string input (raw JSON from frontend)
    if isinstance(doc, str):
        try:
            doc = json.loads(doc)
        except (json.JSONDecodeError, TypeError):
            # If it's not valid JSON, return as-is (already plain text)
            return doc.strip()
    
    # Handle list of nodes
    if isinstance(doc, list):
        return _process_nodes(doc)
    
    # Handle document root {"type": "doc", "content": [...]}
    if isinstance(doc, dict):
        content = doc.get("content", [])
        return _process_nodes(content)
    
    return str(doc)


def _process_nodes(nodes: list) -> str:
    """Process a list of Tiptap nodes into text blocks."""
    blocks = []
    
    for node in nodes:
        if not isinstance(node, dict):
            continue
            
        node_type = node.get("type", "")
        content = node.get("content", [])
        attrs = node.get("attrs", {})
        
        if node_type == "text":
            # Leaf text node
            blocks.append(node.get("text", ""))
            
        elif node_type == "paragraph":
            # Paragraph — extract inline content, add newline
            para_text = _extract_inline_text(content)
            blocks.append(para_text + "\n")
            
        elif node_type == "heading":
            # Heading — extract text, add emphasis markers
            level = attrs.get("level", 1)
            heading_text = _extract_inline_text(content)
            if heading_text.strip():
                blocks.append(heading_text.upper() + "\n")
            
        elif node_type == "bulletList":
            # Bullet list
            for item in content:
                if item.get("type") == "listItem":
                    item_text = _extract_inline_text(item.get("content", []))
                    if not item_text:
                        # listItem wraps paragraphs
                        item_text = _process_nested_list_item(item.get("content", []))
                    blocks.append(f"  •  {item_text}")
            blocks.append("")  # spacing after list
            
        elif node_type == "orderedList":
            # Ordered list
            start = attrs.get("start", 1)
            for i, item in enumerate(content):
                if item.get("type") == "listItem":
                    item_text = _extract_inline_text(item.get("content", []))
                    if not item_text:
                        item_text = _process_nested_list_item(item.get("content", []))
                    blocks.append(f"  {start + i}.  {item_text}")
            blocks.append("")
            
        elif node_type == "blockquote":
            # Blockquote
            quote_text = _process_nodes(content)
            for line in quote_text.strip().split("\n"):
                blocks.append(f"  » {line}")
            blocks.append("")
            
        elif node_type == "codeBlock":
            # Code block
            code_text = _extract_inline_text(content)
            blocks.append(f"───────────────────────────────")
            blocks.append(code_text)
            blocks.append(f"───────────────────────────────\n")
            
        elif node_type == "horizontalRule":
            blocks.append("─────────────────────────────────────\n")
            
        elif node_type == "hardBreak":
            blocks.append("\n")
            
        elif node_type == "table":
            # Table — process rows
            table_text = _process_table(content)
            blocks.append(table_text + "\n")
            
        elif node_type == "taskList":
            for item in content:
                if item.get("type") == "taskItem":
                    checked = item.get("attrs", {}).get("checked", False)
                    mark = "☑" if checked else "☐"
                    item_text = _process_nested_list_item(item.get("content", []))
                    blocks.append(f"  {mark}  {item_text}")
            blocks.append("")
            
        elif node_type in ("listItem", "tableRow", "tableCell", "tableHeader"):
            # Container nodes — recurse into content
            blocks.append(_process_nodes(content))
            
        elif node_type == "image":
            alt = attrs.get("alt", "Image")
            blocks.append(f"[{alt}]\n")
            
        else:
            # Unknown node type — try to extract any text content
            if content:
                blocks.append(_process_nodes(content))
    
    return "\n".join(blocks).strip()


def _extract_inline_text(nodes: list) -> str:
    """Extract text from inline nodes (text, marks, etc.)."""
    parts = []
    
    for node in nodes:
        if not isinstance(node, dict):
            continue
            
        node_type = node.get("type", "")
        
        if node_type == "text":
            parts.append(node.get("text", ""))
            
        elif node_type == "hardBreak":
            parts.append("\n")
            
        elif node_type == "paragraph":
            # Nested paragraph inside list items, etc.
            para_text = _extract_inline_text(node.get("content", []))
            parts.append(para_text)
            
        elif node_type == "mention":
            parts.append(node.get("attrs", {}).get("label", "@mention"))
            
        else:
            # Try to recurse
            content = node.get("content", [])
            if content:
                parts.append(_extract_inline_text(content))
    
    return "".join(parts)


def _process_nested_list_item(nodes: list) -> str:
    """Process content inside a list item (may contain paragraphs)."""
    parts = []
    for node in nodes:
        if not isinstance(node, dict):
            continue
        if node.get("type") == "paragraph":
            parts.append(_extract_inline_text(node.get("content", [])))
        elif node.get("content"):
            parts.append(_extract_inline_text(node.get("content", [])))
    return " ".join(parts)


def _process_table(rows: list) -> str:
    """Convert table nodes to simple text table."""
    table_data = []
    
    for row in rows:
        if row.get("type") != "tableRow":
            continue
        cells = []
        for cell in row.get("content", []):
            cell_text = _extract_inline_text(cell.get("content", []))
            if not cell_text:
                cell_text = _process_nodes(cell.get("content", []))
            cells.append(cell_text.strip())
        table_data.append(cells)
    
    if not table_data:
        return ""
    
    # Calculate column widths
    max_cols = max(len(row) for row in table_data)
    col_widths = [0] * max_cols
    for row in table_data:
        for i, cell in enumerate(row):
            col_widths[i] = max(col_widths[i], len(cell))
    
    # Format rows
    lines = []
    for row_idx, row in enumerate(table_data):
        formatted = []
        for i in range(max_cols):
            cell = row[i] if i < len(row) else ""
            formatted.append(cell.ljust(col_widths[i]))
        lines.append("  │  ".join(formatted))
        if row_idx == 0:
            # Header separator
            lines.append("─" * (sum(col_widths) + 5 * (max_cols - 1)))
    
    return "\n".join(lines)


def tiptap_to_html(doc: Union[str, dict]) -> str:
    """
    Convert Tiptap JSON to simple HTML (for future rich PDF export).
    
    Args:
        doc: Either a JSON string or parsed dict
        
    Returns:
        HTML string
    """
    if isinstance(doc, str):
        try:
            doc = json.loads(doc)
        except (json.JSONDecodeError, TypeError):
            return f"<p>{doc}</p>"
    
    if isinstance(doc, dict):
        content = doc.get("content", [])
        return _nodes_to_html(content)
    
    return f"<p>{doc}</p>"


def _nodes_to_html(nodes: list) -> str:
    """Convert node list to HTML."""
    html_parts = []
    
    for node in nodes:
        if not isinstance(node, dict):
            continue
            
        node_type = node.get("type", "")
        content = node.get("content", [])
        attrs = node.get("attrs", {})
        
        if node_type == "text":
            text = node.get("text", "")
            # Apply marks (bold, italic, etc.)
            marks = node.get("marks", [])
            for mark in marks:
                mark_type = mark.get("type", "")
                if mark_type == "bold":
                    text = f"<strong>{text}</strong>"
                elif mark_type == "italic":
                    text = f"<em>{text}</em>"
                elif mark_type == "underline":
                    text = f"<u>{text}</u>"
                elif mark_type == "strike":
                    text = f"<s>{text}</s>"
                elif mark_type == "code":
                    text = f"<code>{text}</code>"
                elif mark_type == "link":
                    href = mark.get("attrs", {}).get("href", "#")
                    text = f'<a href="{href}">{text}</a>'
            html_parts.append(text)
            
        elif node_type == "paragraph":
            inner = _nodes_to_html(content)
            html_parts.append(f"<p>{inner}</p>")
            
        elif node_type == "heading":
            level = attrs.get("level", 1)
            inner = _nodes_to_html(content)
            html_parts.append(f"<h{level}>{inner}</h{level}>")
            
        elif node_type == "bulletList":
            inner = _nodes_to_html(content)
            html_parts.append(f"<ul>{inner}</ul>")
            
        elif node_type == "orderedList":
            inner = _nodes_to_html(content)
            html_parts.append(f"<ol>{inner}</ol>")
            
        elif node_type == "listItem":
            inner = _nodes_to_html(content)
            html_parts.append(f"<li>{inner}</li>")
            
        elif node_type == "blockquote":
            inner = _nodes_to_html(content)
            html_parts.append(f"<blockquote>{inner}</blockquote>")
            
        elif node_type == "codeBlock":
            inner = _nodes_to_html(content)
            html_parts.append(f"<pre><code>{inner}</code></pre>")
            
        elif node_type == "hardBreak":
            html_parts.append("<br/>")
            
        elif node_type == "horizontalRule":
            html_parts.append("<hr/>")
            
        elif node_type == "image":
            src = attrs.get("src", "")
            alt = attrs.get("alt", "")
            html_parts.append(f'<img src="{src}" alt="{alt}"/>')
            
        else:
            if content:
                html_parts.append(_nodes_to_html(content))
    
    return "".join(html_parts)


# ─── Self-test ────────────────────────────────────────────────
if __name__ == "__main__":
    # Test with typical Tiptap JSON
    test_doc = {
        "type": "doc",
        "content": [
            {
                "type": "heading",
                "attrs": {"level": 1},
                "content": [{"type": "text", "text": "WINDI Governance Report"}]
            },
            {
                "type": "paragraph",
                "content": [
                    {"type": "text", "text": "This document has been processed through the "},
                    {"type": "text", "text": "Three Dragons Protocol", "marks": [{"type": "bold"}]},
                    {"type": "text", "text": " and sealed with SHA-256 integrity."}
                ]
            },
            {
                "type": "bulletList",
                "content": [
                    {"type": "listItem", "content": [
                        {"type": "paragraph", "content": [
                            {"type": "text", "text": "Guardian: Claude (Constitutional Base)"}
                        ]}
                    ]},
                    {"type": "listItem", "content": [
                        {"type": "paragraph", "content": [
                            {"type": "text", "text": "Architect: GPT (Extension Layer)"}
                        ]}
                    ]},
                    {"type": "listItem", "content": [
                        {"type": "paragraph", "content": [
                            {"type": "text", "text": "Witness: Gemini (Verification)"}
                        ]}
                    ]}
                ]
            },
            {
                "type": "paragraph",
                "content": [
                    {"type": "text", "text": "AI processes. Human decides. WINDI guarantees."}
                ]
            }
        ]
    }
    
    print("═══ PLAIN TEXT OUTPUT ═══")
    print(tiptap_to_plaintext(test_doc))
    print()
    print("═══ HTML OUTPUT ═══")
    print(tiptap_to_html(test_doc))
    print()
    
    # Test with raw JSON string (as received from frontend)
    raw_json = json.dumps(test_doc)
    print("═══ FROM RAW JSON STRING ═══")
    print(tiptap_to_plaintext(raw_json))
