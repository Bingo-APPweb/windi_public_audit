#!/usr/bin/env python3
"""
HARTMANN v2 — Anchor Generation (Helena Process)
=================================================
Generate clean portrait of Dr. Hartmann for anchor extraction.
Controlled lighting, frontal face, no background distractions.

WINDI-HIOS · W-GENERATOR-001 · I9 Gate Required
"""
import subprocess
import sys
from pathlib import Path

# Paths
VEO_PRODUCER = "/opt/windi/hios/visual/producer/veo_producer.py"
OUTPUT_DIR = Path("/opt/windi/hios/cinema/obras/o-peso-do-eco/scenes/hartmann_v2")
OUTPUT = OUTPUT_DIR / "hartmann_v2_anchor_source.mp4"

# Hartmann canonical appearance prompt - isolated portrait for anchor
PROMPT = """Close-up portrait of a distinguished German defense lawyer in his early 60s.

FACE (critical for identity):
- Silver-white hair, swept back elegantly
- Round gold-rimmed spectacles (distinctive feature)
- Well-groomed short grey beard
- Intelligent, confident expression
- Direct gaze at camera

ATTIRE:
- Dark grey pinstripe suit
- White dress shirt
- Navy blue tie with subtle pattern

SETTING:
- Neutral warm background (law office ambiance)
- Soft professional lighting from front-left
- Shallow depth of field, face in sharp focus

STYLE:
- Professional headshot quality
- Documentary realism
- Face fills 60% of frame
- No other people visible

This is Dr. Hartmann, a seasoned defense attorney. His round spectacles are his most distinctive feature."""

def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    cmd = [
        "python3", VEO_PRODUCER,
        PROMPT,
        "--output", str(OUTPUT),
        "--model", "veo-3.1"
    ]

    print("=" * 60)
    print("HARTMANN v2 — ANCHOR GENERATION")
    print("=" * 60)
    print(f"\nOutput: {OUTPUT}")
    print(f"\nPrompt (portrait for anchor):\n{PROMPT[:200]}...")
    print("\n" + "=" * 60)

    if len(sys.argv) > 1 and sys.argv[1] == "--execute":
        print("\n🎬 Generating Hartmann v2 portrait...\n")
        result = subprocess.run(cmd)

        if result.returncode == 0:
            print("\n" + "=" * 60)
            print("NEXT STEPS:")
            print("=" * 60)
            print(f"\n  1. Extract best frame from {OUTPUT}")
            print("  2. Copy frame to Server B")
            print("  3. Extract anchor embedding")
            print("  4. Validate anchor stability (self-similarity)")
            print("  5. Generate S11 + S19 with --ref")
            print("  6. Validate both with SPINE-CAST")

        sys.exit(result.returncode)
    else:
        print("\n⚠️  I9 GATE: Human approval required")
        print(f"\n  python3 {__file__} --execute")

if __name__ == "__main__":
    main()
