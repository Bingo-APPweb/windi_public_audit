#!/usr/bin/env python3
"""
WINDI ISP Resolver — Template Matching Engine
===============================================
Matches communiqué body text against ISP template keywords.
Scores as percentage: keyword_matches / total_keywords * 100.

Thresholds (from ISP profile):
  - 100%: auto-apply (if configured)
  - >=70%: suggest template (human confirms)
  - <70%: manual select

Principle: "AI processes. Human decides. WINDI guarantees."
"""

import json
import os
import re

ISP_PROFILE_PATH = "/opt/windi/isp/communique/profile.json"

_cached_profile = None
_cached_mtime = 0


def _load_profile():
    """Load ISP communiqué profile with file-level caching."""
    global _cached_profile, _cached_mtime

    if not os.path.exists(ISP_PROFILE_PATH):
        return None

    mtime = os.path.getmtime(ISP_PROFILE_PATH)
    if _cached_profile and mtime == _cached_mtime:
        return _cached_profile

    with open(ISP_PROFILE_PATH, "r", encoding="utf-8") as f:
        _cached_profile = json.load(f)
        _cached_mtime = mtime

    return _cached_profile


def get_templates():
    """Return list of templates with id, code, names, keywords, fields count."""
    profile = _load_profile()
    if not profile:
        return []

    templates = []
    for t in profile.get("templates", []):
        templates.append({
            "id": t["id"],
            "code": t["code"],
            "name_de": t["name_de"],
            "name_en": t["name_en"],
            "name_pt": t["name_pt"],
            "description_en": t["description_en"],
            "governance_level": t["governance_level"],
            "requires_review": t["requires_review"],
            "requires_seal": t["requires_seal"],
            "sge_keywords": t["sge_keywords"],
            "form_fields_count": len(t.get("form_fields", [])),
        })
    return templates


def get_full_profile():
    """Return the full ISP profile metadata."""
    profile = _load_profile()
    if not profile:
        return None
    return {
        "profile_id": profile["isp_profile"]["id"],
        "name": profile["isp_profile"]["name"],
        "version": profile["isp_profile"]["version"],
        "governance_level": profile["isp_profile"]["governance"]["level"],
        "template_count": len(profile.get("templates", [])),
        "resolver": profile.get("resolver", {}),
        "trilingual": profile["isp_profile"].get("version", "1.0.0"),
        "languages": profile.get("audit", {}).get("languages", ["de", "en", "pt"]),
    }


def resolve(body_text, title_text=""):
    """
    Match body + title text against all template keywords.
    Returns ranked suggestions.

    Returns:
        {
            "suggestions": [
                {
                    "template_id": "ISP-COM-04",
                    "code": "security_advisory",
                    "name_en": "Security Advisory",
                    "score": 73.3,
                    "matched_keywords": ["vulnerability", "security", ...],
                    "total_keywords": 15,
                    "action": "suggest"  # or "auto_apply" or "manual"
                },
                ...
            ],
            "best_match": { ... } or null,
            "resolver_version": "1.0.0"
        }
    """
    profile = _load_profile()
    if not profile:
        return {"suggestions": [], "best_match": None, "resolver_version": "1.0.0"}

    resolver_config = profile.get("resolver", {})
    auto_threshold = resolver_config.get("thresholds", {}).get("auto_apply", 100)
    suggest_threshold = resolver_config.get("thresholds", {}).get("human_confirms", 70)

    # Combine body and title for matching (case-insensitive)
    combined_text = f"{title_text} {body_text}".lower()

    suggestions = []
    for t in profile.get("templates", []):
        keywords = t.get("sge_keywords", [])
        if not keywords:
            continue

        matched = []
        for kw in keywords:
            # Word-boundary match to avoid partial matches
            pattern = re.escape(kw.lower())
            if re.search(r'\b' + pattern + r'\b', combined_text):
                matched.append(kw)

        total = len(keywords)
        score = (len(matched) / total * 100) if total > 0 else 0

        if score > 0:
            action = "manual"
            if score >= auto_threshold:
                action = "auto_apply"
            elif score >= suggest_threshold:
                action = "suggest"

            suggestions.append({
                "template_id": t["id"],
                "code": t["code"],
                "name_en": t["name_en"],
                "name_de": t["name_de"],
                "score": round(score, 1),
                "matched_keywords": matched,
                "total_keywords": total,
                "action": action,
            })

    # Sort by score descending
    suggestions.sort(key=lambda x: x["score"], reverse=True)

    best = suggestions[0] if suggestions and suggestions[0]["score"] >= suggest_threshold else None

    return {
        "suggestions": suggestions,
        "best_match": best,
        "resolver_version": resolver_config.get("version", "1.0.0"),
    }


def is_connected():
    """Check if ISP profile is accessible."""
    return os.path.exists(ISP_PROFILE_PATH)


def get_status():
    """Return ISP status for /health endpoint."""
    profile = _load_profile()
    connected = profile is not None
    template_count = len(profile.get("templates", [])) if profile else 0
    resolver_version = profile.get("resolver", {}).get("version", "1.0.0") if profile else "0.0.0"

    return {
        "isp_connected": connected,
        "templates_loaded": template_count,
        "resolver_version": resolver_version,
    }
