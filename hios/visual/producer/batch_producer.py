#!/usr/bin/env python3
"""
WINDI Batch Producer — Controlled Scene Production
===================================================
Generates scenes from a queue with rate limiting to avoid quota exhaustion.

Usage:
    python batch_producer.py --scenes 3      # Generate next 3 pending scenes
    python batch_producer.py --list          # List pending scenes
    python batch_producer.py --status        # Show production status

Author: Liga IA+H · WINDI Publishing House
Date: 2026-05-25
"""

import argparse
import json
import os
import subprocess
import time
from datetime import datetime
from pathlib import Path

# =============================================================================
# Configuration
# =============================================================================

PRODUCER_DIR = Path("/opt/windi/hios/visual/producer")
OBRA_DIR = PRODUCER_DIR / "obras/die-entscheidung"
OUTPUT_DIR = OBRA_DIR / "output"
ANCHORS_DIR = OBRA_DIR / "anchors"
PROGRESS_FILE = OBRA_DIR / ".batch_progress.json"

# Rate limiting
DELAY_BETWEEN_SCENES = 60  # seconds
MODEL = "veo-3.1"  # Use standard for quality, veo-3.1-lite for economy

# =============================================================================
# Scene Definitions (from PRODUCTION_QUEUE.md)
# =============================================================================

SCENES = {
    # ACT 2A COLD (remaining)
    "S15": {
        "name": "klein_fecha",
        "prompt": "Tight close-up of KLEIN's face, a 40-year-old auditor with neat short hair and grey suit. He closes the dossier slowly. Not angry — contained frustration, a man who wanted to believe. He holds the look, then lowers his eyes. COLD fluorescent lighting.",
        "ref": "anchor_final_klein.png",
        "grade": "COLD"
    },
    "S16": {
        "name": "klein_sai",
        "prompt": "KLEIN, a 40-year-old auditor in grey suit, stands, picks up the closed dossier, pauses at the door. COLD grade, his shadow long on the wall. Documentary realism.",
        "ref": "anchor_final_klein.png",
        "grade": "COLD"
    },

    # ACT 2B WARM
    "S17": {
        "name": "maria_aprova_warm",
        "prompt": "MARIA, a 48-year-old bank advisor with short dark-blonde hair and navy blazer, clicks approve; the system prompts her; she reads, thinks, types a fuller reason. Calm, in control. WARM grade: natural window light from the side, eye-level, stable. Documentary realism.",
        "ref": "anchor_final_maria.png",
        "grade": "WARM"
    },
    "S18": {
        "name": "maria_scan",
        "prompt": "MARIA, a 48-year-old bank advisor, places the paper contract on a desktop scanner, the light bar sweeps, she attaches the file. A small, quiet act of care. WARM natural light. Documentary realism.",
        "ref": "anchor_final_maria.png",
        "grade": "WARM"
    },
    "S19": {
        "name": "klein_warm",
        "prompt": "Audit room with WARM natural light, eye-level. KLEIN, a 40-year-old auditor in grey suit, with the dossier, looks up. Documentary realism.",
        "ref": "anchor_final_klein.png",
        "grade": "WARM"
    },
    "S20": {
        "name": "maria_mostra",
        "prompt": "MARIA, a 48-year-old bank advisor, calmly turns her monitor toward Klein. No defensiveness. WARM natural light. Documentary realism.",
        "ref": "anchor_final_maria.png",
        "grade": "WARM"
    },
    "S21": {
        "name": "klein_le_ouro",
        "prompt": "Tight close-up of KLEIN's face, a 40-year-old auditor, as he reads the screen (screen never shown). His expression travels: focus, then understanding, then a faint almost imperceptible nod of respect. WARM light on his face. Shallow depth of field. No dialogue. Pure visual acting.",
        "ref": "anchor_final_klein.png",
        "grade": "WARM_GOLD"
    },
    "S22": {
        "name": "klein_confirma",
        "prompt": "KLEIN, a 40-year-old auditor in grey suit, still reading, taps the screen lightly with one finger as he registers each item. WARM natural light. Documentary realism.",
        "ref": "anchor_final_klein.png",
        "grade": "WARM"
    },
    "S23": {
        "name": "klein_handshake",
        "prompt": "KLEIN, a 40-year-old auditor, closes the dossier with quiet satisfaction, stands, and extends his hand across the table to MARIA, a 48-year-old bank advisor. WARM natural light, eye-level, stable. Documentary realism.",
        "ref": "anchor_final_klein.png",
        "grade": "WARM"
    },

    # EPILOGUE
    "S24": {
        "name": "maria_fim_dia",
        "prompt": "End of day. MARIA, a 48-year-old bank advisor, tidies her desk in the empty branch. Warm alpine evening light floods sideways through the window, long soft shadows. Slow static camera. Documentary realism.",
        "ref": "anchor_final_maria.png",
        "grade": "GOLDEN"
    },
    "S25": {
        "name": "maria_jornal",
        "prompt": "MARIA, a 48-year-old bank advisor, pauses, looks at the old folded newspaper still on the corner of her desk. Close-up of her hand resting on it. Golden evening light. Documentary realism.",
        "ref": "anchor_final_maria.png",
        "grade": "GOLDEN"
    },
    "S26": {
        "name": "maria_close_final",
        "prompt": "Close-up of MARIA's face, a 48-year-old bank advisor, in the golden evening light, calm, at peace with her work. She looks toward the window. Shallow depth of field. Documentary realism.",
        "ref": "anchor_final_maria.png",
        "grade": "GOLDEN"
    },
}

# =============================================================================
# Progress Management
# =============================================================================

def load_progress():
    """Load production progress from file."""
    if PROGRESS_FILE.exists():
        with open(PROGRESS_FILE) as f:
            return json.load(f)
    return {"completed": [], "failed": [], "last_run": None}

def save_progress(progress):
    """Save production progress to file."""
    with open(PROGRESS_FILE, 'w') as f:
        json.dump(progress, f, indent=2)

def get_pending_scenes():
    """Get list of scenes not yet generated."""
    progress = load_progress()
    completed = set(progress.get("completed", []))

    # Also check filesystem
    for scene_id in SCENES:
        output_file = OUTPUT_DIR / f"{scene_id}_{SCENES[scene_id]['name']}.mp4"
        if output_file.exists():
            completed.add(scene_id)

    pending = [s for s in SCENES if s not in completed]
    return sorted(pending, key=lambda x: int(x[1:]))  # Sort by number

def get_completed_scenes():
    """Get list of completed scenes."""
    completed = []
    for scene_id in SCENES:
        output_file = OUTPUT_DIR / f"{scene_id}_{SCENES[scene_id]['name']}.mp4"
        if output_file.exists():
            size_mb = output_file.stat().st_size / (1024 * 1024)
            completed.append((scene_id, SCENES[scene_id]['name'], size_mb))
    return sorted(completed, key=lambda x: int(x[0][1:]))

# =============================================================================
# Production
# =============================================================================

def generate_scene(scene_id, model="veo-3.1", key=1):
    """Generate a single scene using veo_producer.py."""
    scene = SCENES[scene_id]
    output_file = OUTPUT_DIR / f"{scene_id}_{scene['name']}.mp4"
    ref_file = ANCHORS_DIR / scene['ref']

    print(f"\n{'='*60}")
    print(f"🎬 Generating {scene_id}: {scene['name']}")
    print(f"   Grade: {scene['grade']}")
    print(f"   Model: {model}")
    print(f"   API Key: {key}")
    print(f"{'='*60}")

    cmd = [
        "python3", str(PRODUCER_DIR / "veo_producer.py"),
        scene['prompt'],
        "--ref", str(ref_file),
        "--output", str(output_file),
        "--model", model,
        "--key", str(key)
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

        if result.returncode == 0 and output_file.exists():
            size_mb = output_file.stat().st_size / (1024 * 1024)
            print(f"✅ {scene_id} complete: {size_mb:.1f} MB")
            return True
        else:
            print(f"❌ {scene_id} failed:")
            print(result.stderr or result.stdout)
            return False

    except subprocess.TimeoutExpired:
        print(f"❌ {scene_id} timeout (5 min)")
        return False
    except Exception as e:
        print(f"❌ {scene_id} error: {e}")
        return False

def run_batch(num_scenes, model="veo-3.1", delay=60, key=1):
    """Generate a batch of scenes with rate limiting."""
    pending = get_pending_scenes()

    if not pending:
        print("✅ All scenes complete!")
        return

    to_generate = pending[:num_scenes]
    progress = load_progress()

    print(f"\n🎬 WINDI Batch Producer")
    print(f"   Scenes to generate: {len(to_generate)}")
    print(f"   Model: {model}")
    print(f"   API Key: {key}")
    print(f"   Delay between: {delay}s")
    print(f"   Queue: {', '.join(to_generate)}")

    for i, scene_id in enumerate(to_generate):
        if i > 0:
            print(f"\n⏳ Waiting {delay}s before next scene...")
            time.sleep(delay)

        success = generate_scene(scene_id, model, key)

        if success:
            progress["completed"].append(scene_id)
        else:
            progress["failed"].append(scene_id)

        progress["last_run"] = datetime.now().isoformat()
        save_progress(progress)

    # Summary
    print(f"\n{'='*60}")
    print("📊 BATCH SUMMARY")
    print(f"{'='*60}")
    completed = get_completed_scenes()
    pending = get_pending_scenes()
    print(f"   Completed: {len(completed)}/26")
    print(f"   Pending: {len(pending)}")
    if pending:
        print(f"   Next: {', '.join(pending[:3])}")

def show_status():
    """Show current production status."""
    completed = get_completed_scenes()
    pending = get_pending_scenes()
    progress = load_progress()

    print(f"\n{'='*60}")
    print("📊 DIE ENTSCHEIDUNG — Production Status")
    print(f"{'='*60}")

    print(f"\n✅ COMPLETED ({len(completed)}/26):")
    for scene_id, name, size in completed:
        print(f"   {scene_id}: {name} ({size:.1f} MB)")

    print(f"\n⏳ PENDING ({len(pending)}):")
    for scene_id in pending:
        scene = SCENES[scene_id]
        print(f"   {scene_id}: {scene['name']} [{scene['grade']}]")

    if progress.get("failed"):
        print(f"\n❌ FAILED:")
        for scene_id in progress["failed"]:
            print(f"   {scene_id}")

    if progress.get("last_run"):
        print(f"\n⏱️  Last run: {progress['last_run']}")

def list_pending():
    """List pending scenes with prompts."""
    pending = get_pending_scenes()

    print(f"\n📋 PENDING SCENES ({len(pending)}):\n")
    for scene_id in pending:
        scene = SCENES[scene_id]
        print(f"{scene_id}: {scene['name']}")
        print(f"   Grade: {scene['grade']}")
        print(f"   Ref: {scene['ref']}")
        print(f"   Prompt: {scene['prompt'][:80]}...")
        print()

# =============================================================================
# Main
# =============================================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="WINDI Batch Producer")
    parser.add_argument("--scenes", "-n", type=int, default=3,
                       help="Number of scenes to generate (default: 3)")
    parser.add_argument("--model", "-m", default="veo-3.1",
                       choices=["veo-3.1", "veo-3.1-lite", "veo-3.1-fast"],
                       help="Model to use")
    parser.add_argument("--delay", "-d", type=int, default=60,
                       help="Seconds between generations (default: 60)")
    parser.add_argument("--key", "-k", type=int, default=1, choices=[1, 2, 3],
                       help="API key to use (1=primary, 2=secondary, 3=tertiary)")
    parser.add_argument("--list", "-l", action="store_true",
                       help="List pending scenes")
    parser.add_argument("--status", "-s", action="store_true",
                       help="Show production status")

    args = parser.parse_args()

    if args.list:
        list_pending()
    elif args.status:
        show_status()
    else:
        run_batch(args.scenes, args.model, args.delay, args.key)
