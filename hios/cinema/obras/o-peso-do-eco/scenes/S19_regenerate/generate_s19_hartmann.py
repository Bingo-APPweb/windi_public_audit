#!/usr/bin/env python3
"""
S19 Regeneration with Hartmann Identity Continuity
Scene: Dr. Hartmann (defense lawyer) addresses the court - "Der Einspruch"
Reference: S11 Hartmann anchor (with distinctive round glasses)

WINDI-HIOS · W-GENERATOR-001 · I9 Gate Required

Usage:
    python generate_s19_hartmann.py           # Show command (dry run)
    python generate_s19_hartmann.py --execute # Run generation
"""
import subprocess
import sys
from pathlib import Path

# Paths
VEO_PRODUCER = "/opt/windi/hios/visual/producer/veo_producer.py"
HARTMANN_REF = "/opt/windi/hios/visual/producer/obras/o-peso-do-eco/_forense/frames/S11_advogado_01.jpg"
OUTPUT = "/opt/windi/hios/cinema/obras/o-peso-do-eco/scenes/S19_regenerate/S19_hartmann_v2.mp4"

# Scene prompt - S19 "Der Einspruch" (The Objection)
PROMPT = """German courtroom, wood-paneled walls, natural lighting from high windows.

The distinguished older lawyer from the reference image stands at the defense table,
addressing the court with conviction. He wears his characteristic round spectacles,
silver hair swept back, grey pinstripe suit. His expression is intense but controlled
as he raises an objection.

The judge (elderly man in black robes) is visible but blurred in the background.
Focus remains on the lawyer's face and gesturing hands.

Cinematic documentary style, shallow depth of field, warm courtroom lighting.
The lawyer's round glasses must be clearly visible - they are his defining feature."""

def main():
    # Ensure output directory exists
    Path(OUTPUT).parent.mkdir(parents=True, exist_ok=True)

    # Build command
    cmd = [
        "python3", VEO_PRODUCER,
        PROMPT,
        "--ref", HARTMANN_REF,
        "--output", OUTPUT,
        "--model", "veo-3.1"
    ]

    print("=" * 60)
    print("S19 REGENERATION — HARTMANN IDENTITY CONTINUITY")
    print("=" * 60)
    print(f"\nReference: {HARTMANN_REF}")
    print(f"Output:    {OUTPUT}")
    print(f"\nPrompt:\n{PROMPT[:150]}...")
    print("\n" + "=" * 60)

    if len(sys.argv) > 1 and sys.argv[1] == "--execute":
        print("\n🎬 Executing generation...\n")
        result = subprocess.run(cmd)

        if result.returncode == 0:
            print("\n" + "=" * 60)
            print("NEXT STEP: Validate with SPINE-CAST")
            print("=" * 60)
            print(f"\n  1. Extract frames from {OUTPUT}")
            print("  2. Run SPINE-CAST against Hartmann anchor")
            print("  3. Verify cosine >= 0.65 (OPERATIONAL) or >= 0.75 (FORENSIC)")
            print("  4. If PASS → seal; if FAIL → regenerate (max 3 attempts)")

        sys.exit(result.returncode)
    else:
        print("\n⚠️  I9 GATE: Human approval required")
        print("\nCommand to execute:")
        print(f"  python {__file__} --execute")
        print("\nOr run directly:")
        print(f"  python {VEO_PRODUCER} \\")
        print(f"    \"{PROMPT[:60]}...\" \\")
        print(f"    --ref {HARTMANN_REF} \\")
        print(f"    --output {OUTPUT}")

if __name__ == "__main__":
    main()
