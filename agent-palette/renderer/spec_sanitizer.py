import re
from typing import Dict, Any

ALLOWED_SPEC_FIELDS = {
    "text", "title", "sections", "metadata", "language",
    "template_id", "intent", "tier", "isp_profile"
}

MAX_TITLE_LEN = 200
MAX_SECTION_CONTENT = 10000
MAX_SECTIONS = 50
MAX_TEXT_LEN = 50000

DANGEROUS_PATTERNS = [
    r"\.\./",
    r"/etc/",
    r"file://",
    r"<script",
    r"javascript:",
    r"__import__",
    r"eval\(",
    r"exec\(",
    r"os\.system",
]

def sanitize_spec(spec):
    if not isinstance(spec, dict):
        raise ValueError("Spec must be a dictionary")
    sanitized = {}
    for key, val in spec.items():
        if key not in ALLOWED_SPEC_FIELDS:
            continue
        sanitized[key] = val
    if "text" in sanitized:
        text = str(sanitized["text"])[:MAX_TEXT_LEN]
        _check_dangerous(text, "text")
        sanitized["text"] = text
    if "title" in sanitized:
        title = str(sanitized["title"])[:MAX_TITLE_LEN]
        _check_dangerous(title, "title")
        sanitized["title"] = title
    if "sections" in sanitized:
        sections = sanitized["sections"]
        if isinstance(sections, list):
            sections = sections[:MAX_SECTIONS]
            for s in sections:
                if isinstance(s, dict) and "content" in s:
                    s["content"] = str(s["content"])[:MAX_SECTION_CONTENT]
                    _check_dangerous(s["content"], "section.content")
            sanitized["sections"] = sections
    if "intent" in sanitized and isinstance(sanitized["intent"], dict):
        allowed_intent = {"doc_type", "language", "formality", "urgency"}
        sanitized["intent"] = {k: v for k, v in sanitized["intent"].items() if k in allowed_intent}
    return sanitized

def _check_dangerous(value, field_name):
    for pattern in DANGEROUS_PATTERNS:
        if re.search(pattern, value, re.IGNORECASE):
            raise ValueError(f"Blocked content in '{field_name}': potential injection detected")

def sanitize_filename(filename):
    from pathlib import Path
    clean = Path(filename).name
    if not clean or clean.startswith("."):
        raise ValueError("Invalid filename")
    return clean
