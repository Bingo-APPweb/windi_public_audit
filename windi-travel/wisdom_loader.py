"""
wisdom_loader.py — Carregador de Wisdom Blocks para Agentes WINDI
═══════════════════════════════════════════════════════════════════════════════
§148 — Wisdom Block Injection Protocol

"Blocos são memória comprimida. O agente sabe sem precisar de ser explicado."

Prioridade de injecção para MARIA:
  1. WB-PERS-64b01072 (maria-presence)
  2. WB-PERS-9249c7d5 (liga-iah-identity)
  3. WB-PERS-461b337c (communication-limits)
  4. Restantes WB-PERS por weight decrescente

Author: Liga IA+H · Kempten · 08 Abril 2026
═══════════════════════════════════════════════════════════════════════════════
"""

import json
import os
import logging
from typing import List, Dict, Optional
from pathlib import Path

log = logging.getLogger("wisdom-loader")

# ── PATHS ────────────────────────────────────────────────────────────────────
WISDOM_BASE = Path("/opt/windi/engine/wisdom")
BLOCKS_DIR = WISDOM_BASE / "blocks"
MANIFEST_PATH = WISDOM_BASE / "manifest.json"

# ── PRIORITY ORDER FOR MARIA ─────────────────────────────────────────────────
MARIA_PRIORITY = [
    "WB-PERS-64b01072",  # maria-presence (most critical)
    "WB-PERS-9249c7d5",  # liga-iah-identity
    "WB-PERS-461b337c",  # communication-limits
]


def load_manifest() -> Dict:
    """Load the wisdom block manifest."""
    if not MANIFEST_PATH.exists():
        log.warning(f"[Wisdom] Manifest not found: {MANIFEST_PATH}")
        return {"blocks": []}

    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def load_block(block_path: str) -> Optional[Dict]:
    """Load a single wisdom block from disk."""
    path = Path(block_path)
    if not path.exists():
        log.warning(f"[Wisdom] Block not found: {block_path}")
        return None

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_pers_blocks(max_blocks: int = 5) -> List[Dict]:
    """
    Get WB-PERS blocks in priority order for MARIA.

    Returns list of blocks with essence, id, and metadata.
    """
    manifest = load_manifest()
    blocks = []
    seen_ids = set()

    # First: Load priority blocks
    for priority_id in MARIA_PRIORITY:
        for entry in manifest.get("blocks", []):
            if entry.get("id") == priority_id:
                block = load_block(entry.get("path", ""))
                if block:
                    blocks.append({
                        "id": entry["id"],
                        "essence": block.get("essence", ""),
                        "subdomain": entry.get("shelf", {}).get("N2", "unknown"),
                        "weight": block.get("weight", {}).get("effective", 0.5) if isinstance(block.get("weight"), dict) else 0.5
                    })
                    seen_ids.add(entry["id"])
                break

    # Then: Load remaining WB-PERS blocks by weight
    remaining = []
    for entry in manifest.get("blocks", []):
        if entry["id"].startswith("WB-PERS-") and entry["id"] not in seen_ids:
            block = load_block(entry.get("path", ""))
            if block:
                weight = block.get("weight", {}).get("effective", 0.5) if isinstance(block.get("weight"), dict) else 0.5
                remaining.append({
                    "id": entry["id"],
                    "essence": block.get("essence", ""),
                    "subdomain": entry.get("shelf", {}).get("N2", "unknown"),
                    "weight": weight
                })

    # Sort remaining by weight descending
    remaining.sort(key=lambda x: x["weight"], reverse=True)

    # Add remaining blocks up to max_blocks
    for block in remaining:
        if len(blocks) >= max_blocks:
            break
        blocks.append(block)

    return blocks


def format_wisdom_injection(blocks: List[Dict], lang: str = "EN") -> str:
    """
    Format wisdom blocks for injection into system prompt.

    Format:
    [WISDOM — Identidade Estável]
    • {essence 1}
    • {essence 2}
    ...
    """
    if not blocks:
        return ""

    headers = {
        "PT": "[WISDOM — Identidade Estável]",
        "DE": "[WISDOM — Stabile Identität]",
        "EN": "[WISDOM — Stable Identity]"
    }

    lang_key = lang.upper()[:2] if lang else "EN"
    header = headers.get(lang_key, headers["EN"])

    lines = [header]
    for block in blocks:
        # Truncate essence if too long (shouldn't happen with 280 limit)
        essence = block["essence"]
        if len(essence) > 300:
            essence = essence[:297] + "..."
        lines.append(f"• {essence}")

    return "\n".join(lines)


def inject_wisdom_for_maria(base_prompt: str, lang: str = "EN", max_blocks: int = 3) -> str:
    """
    Inject wisdom blocks into MARIA's system prompt.

    Blocks are injected AFTER the canonical identity but BEFORE
    the provider-specific instructions.

    Args:
        base_prompt: The base system prompt (MARIA_CONSTITUTION)
        lang: Language code (PT, DE, EN)
        max_blocks: Maximum number of blocks to inject

    Returns:
        Enriched system prompt with wisdom blocks
    """
    blocks = get_pers_blocks(max_blocks)

    if not blocks:
        log.info("[Wisdom] No WB-PERS blocks found to inject")
        return base_prompt

    wisdom_text = format_wisdom_injection(blocks, lang)

    log.info(f"[Wisdom] Injecting {len(blocks)} WB-PERS blocks ({len(wisdom_text)} chars)")

    # Inject after the first major section break
    # Looking for the MOTOR DE ESPELHO / SPIEGELMOTOR / MIRROR ENGINE section
    markers = {
        "PT": "MOTOR DE ESPELHO",
        "DE": "SPIEGELMOTOR",
        "EN": "MIRROR ENGINE"
    }

    lang_key = lang.upper()[:2] if lang else "EN"
    marker = markers.get(lang_key, markers["EN"])

    # Find insertion point (before MOTOR DE ESPELHO)
    if marker in base_prompt:
        idx = base_prompt.index(marker)
        # Go back to find the previous newline
        while idx > 0 and base_prompt[idx-1] != '\n':
            idx -= 1

        return base_prompt[:idx] + "\n" + wisdom_text + "\n\n" + base_prompt[idx:]

    # Fallback: append at the end of the canonical identity section
    return base_prompt + "\n\n" + wisdom_text


# ── STATS ────────────────────────────────────────────────────────────────────

def get_wisdom_stats() -> Dict:
    """Get statistics about loaded wisdom blocks."""
    manifest = load_manifest()

    total = len(manifest.get("blocks", []))
    by_category = {}

    for entry in manifest.get("blocks", []):
        n1 = entry.get("shelf", {}).get("N1", "unknown")
        by_category[n1] = by_category.get(n1, 0) + 1

    pers_blocks = get_pers_blocks(max_blocks=10)

    return {
        "total_blocks": total,
        "by_category": by_category,
        "pers_blocks_available": len(pers_blocks),
        "manifest_path": str(MANIFEST_PATH),
        "blocks_dir": str(BLOCKS_DIR)
    }


if __name__ == "__main__":
    # Test the loader
    import sys

    print("=== WISDOM LOADER TEST ===\n")

    stats = get_wisdom_stats()
    print(f"Total blocks: {stats['total_blocks']}")
    print(f"By category: {stats['by_category']}")
    print(f"WB-PERS available: {stats['pers_blocks_available']}\n")

    blocks = get_pers_blocks(max_blocks=3)
    print("Priority blocks for MARIA:")
    for b in blocks:
        print(f"  [{b['id']}] ({b['subdomain']}, w={b['weight']:.2f})")
        print(f"    → {b['essence'][:80]}...")

    print("\n=== INJECTION TEST ===\n")

    test_prompt = """You are MARIA.
You are useful, discreet, sovereign presence.

CANONICAL IDENTITY
MARIA does not speak to impress.

MIRROR ENGINE — 4 REGISTERS
Before replying, internally align."""

    injected = inject_wisdom_for_maria(test_prompt, "EN", 3)
    print(injected)
