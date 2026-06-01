#!/usr/bin/env python3
"""
§295 Scene Generation — Runway Gen-3 Alpha Turbo
=================================================
Gera as 4 cenas windi_on_screen usando Runway como motor único.

INVARIANTE DE TEXTURA: Mesmo motor para toda a linhagem de continuidade.
INVARIANTE I9: Cada cena requer aprovação antes de selar.

Uso:
    python3 generate_s295_scenes.py S14          # Gera S14
    python3 generate_s295_scenes.py S14 --dry    # Dry run (mostra prompt)
    python3 generate_s295_scenes.py all          # Gera todas sequencialmente

Liga IA+H · WINDI Publishing House · 30 Mai 2026
"""
import os
import sys
import json
import time
import hashlib
from datetime import datetime
from pathlib import Path

# Runway SDK
try:
    from runwayml import RunwayML
except ImportError:
    print("[ERROR] runwayml not installed. Run: pip install runwayml")
    sys.exit(1)

# ============================================================
# CONFIGURATION
# ============================================================

OUTPUT_DIR = Path("/opt/windi/hios/cinema/obras/o-peso-do-eco/scenes/s295_renders")
PRODUCTION_DIR = Path("/opt/windi/hios/cinema/obras/o-peso-do-eco/production")

# Motor único para invariante de textura
# Modelos disponíveis: gen4.5, veo3.1, veo3.1_fast, veo3
GENERATOR_ENGINE = "veo3.1"
GENERATOR_MODEL = "veo3.1"

# Duração das cenas (6 segundos cada por timecode)
SCENE_DURATION = 6  # seconds

# ============================================================
# SCENE PROMPTS (§296 — NEUTRAL UI ZONE — text added in post)
# ============================================================
# §296 Invariant: Generator makes the world. Proof is made in post.
# All UI text is BLURRED/ABSTRACTED in plate. Overlay adds legible text.

SCENE_PROMPTS = {
    "S14": {
        # S14 plate already generated and composed. Kept for reference.
        "prompt": """A computer monitor in a modern forensic laboratory displaying a dark professional UI interface. The screen shows abstract verification elements with green indicators, but any text is INTENTIONALLY BLURRED or OUT OF FOCUS. A placeholder zone exists where text will be added in post-production. Monitor-lit lab environment, cold blue lighting. Cinematic, realistic.""",
        "characters": [],
        "windi_on_screen": True,
        "plate_gate": ["monitor visible", "dark UI theme", "green accents", "blurred text zone"],
    },
    "S15": {
        "prompt": """A computer monitor in a modern forensic laboratory displaying a verification interface. The screen shows a dark professional UI with glowing elements — but any text is BLURRED or OUT OF FOCUS, creating a placeholder zone where text will be added in post-production. The monitor displays: a shield or checkmark icon (green glow), abstract data visualization elements, receipt/hash area visible but TEXT INTENTIONALLY BLURRED. Monitor-lit lab environment, cold blue ambient lighting. The screen is the hero element. Cinematic, realistic. IMPORTANT: DO NOT render legible text. All text elements should be decoratively blurred or abstracted. Clean dark UI theme with green accents.""",
        "characters": [],
        "windi_on_screen": True,
        "plate_gate": ["monitor visible", "dark UI theme", "green accents", "blurred text zone", "shield/checkmark icon"],
    },
    "S16": {
        "prompt": """A blonde woman detective (Helena) in her early 40s stands in a modern forensic laboratory, pointing at a computer monitor. She wears a dark navy wool coat over professional attire. Her blonde hair is pulled back in a professional updo. She has angular features and a focused expression. On the monitor screen, footage shows a dark sedan car in the background — this is crucial evidence. The car should be a dark (black or very dark grey) luxury sedan, clearly visible in what appears to be analysed video footage. The main WINDI UI elements on the monitor are BLURRED or ABSTRACTED — placeholder zones for post-production text overlay. Only the CAR FOOTAGE should be clearly visible. Cold blue lighting, multiple monitors. Bavaria, Germany forensic lab. Cinematic, realistic.""",
        "characters": ["HELENA-§293"],
        "windi_on_screen": True,
        "continuity": ["navy coat", "blonde hair pulled back", "dark sedan visible on monitor", "UI text blurred"],
    },
    "S20": {
        "prompt": """A Bavarian regional courtroom (Landgericht Kempten). Dark oak wood panelling, tall windows with cold natural daylight streaming in. German flag and Bavarian flag visible on the bench area. Helena (blonde woman detective in her early 40s) stands addressing the court. She wears a dark navy wool coat, her blonde hair pulled back professionally. She gestures toward a large courtroom display screen. The display screen shows: evidence footage of a dark sedan (same car from previous scenes), WINDI verification interface — but TEXT IS BLURRED/ABSTRACTED, green verification indicators visible (icons, not text). The atmosphere is tense, clinical. This is the climactic evidence presentation. Cinematic, realistic. Bavaria, Germany, 2026.""",
        "characters": ["HELENA-§293"],
        "windi_on_screen": True,
        "continuity": ["navy coat", "dark oak", "DE flag", "Bavaria flag", "car footage", "UI text blurred"],
    },
}

# ============================================================
# HELPER FUNCTIONS
# ============================================================

def get_runway_client():
    """Initialize Runway client with API key from .env"""
    env_path = Path("/opt/windi/.env")
    api_key = None

    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                if line.startswith("RUNWAY_API_KEY="):
                    api_key = line.strip().split("=", 1)[1]
                    break

    if not api_key:
        raise ValueError("RUNWAY_API_KEY not found in /opt/windi/.env")

    return RunwayML(api_key=api_key)


def sha256_file(filepath: str) -> str:
    """Compute SHA-256 hash of a file."""
    h = hashlib.sha256()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()


def generate_scene(scene_id: str, dry_run: bool = False) -> dict:
    """
    Generate a single scene using Runway Gen-3 Alpha Turbo.
    Returns generation result with metadata.
    """
    if scene_id not in SCENE_PROMPTS:
        return {"error": f"Unknown scene: {scene_id}"}

    scene = SCENE_PROMPTS[scene_id]
    prompt = scene["prompt"]

    result = {
        "scene": scene_id,
        "timestamp": datetime.now().isoformat(),
        "generator": GENERATOR_ENGINE,
        "model": GENERATOR_MODEL,
        "prompt": prompt[:200] + "..." if len(prompt) > 200 else prompt,
        "full_prompt": prompt,
        "windi_on_screen": scene.get("windi_on_screen", False),
        "characters": scene.get("characters", []),
        "continuity_checks": scene.get("continuity", scene.get("ui_requirements", [])),
    }

    if dry_run:
        result["status"] = "DRY_RUN"
        result["message"] = "Prompt prepared but not executed"
        return result

    print(f"\n[{scene_id}] Starting generation with Runway Gen-3 Alpha Turbo...")
    print(f"[{scene_id}] Prompt: {prompt[:100]}...")

    try:
        client = get_runway_client()

        # Create text-to-video task
        task = client.text_to_video.create(
            model=GENERATOR_MODEL,
            prompt_text=prompt,
            duration=SCENE_DURATION,
            ratio="1280:720",  # Landscape HD
        )

        task_id = task.id
        result["task_id"] = task_id
        print(f"[{scene_id}] Task created: {task_id}")

        # Poll for completion
        max_wait = 300  # 5 minutes max
        poll_interval = 5
        elapsed = 0

        while elapsed < max_wait:
            task_status = client.tasks.retrieve(task_id)
            status = task_status.status
            print(f"[{scene_id}] Status: {status} ({elapsed}s)")

            if status == "SUCCEEDED":
                # Download video
                output_url = task_status.output[0] if task_status.output else None
                if output_url:
                    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
                    output_path = OUTPUT_DIR / f"{scene_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.mp4"

                    # Download
                    import urllib.request
                    urllib.request.urlretrieve(output_url, str(output_path))

                    result["status"] = "GENERATED"
                    result["output_path"] = str(output_path)
                    result["output_hash"] = sha256_file(str(output_path))
                    result["message"] = f"Video saved to {output_path}"
                    print(f"[{scene_id}] SUCCESS: {output_path}")
                    return result
                else:
                    result["status"] = "ERROR"
                    result["message"] = "No output URL in task result"
                    return result

            elif status == "FAILED":
                result["status"] = "FAILED"
                result["message"] = f"Task failed: {task_status.failure or 'unknown'}"
                result["failure_reason"] = str(task_status.failure) if task_status.failure else "unknown"
                print(f"[{scene_id}] FAILED: {result['message']}")
                return result

            elif status == "CANCELLED":
                result["status"] = "CANCELLED"
                result["message"] = "Task was cancelled"
                return result

            time.sleep(poll_interval)
            elapsed += poll_interval

        result["status"] = "TIMEOUT"
        result["message"] = f"Task timed out after {max_wait}s"
        return result

    except Exception as e:
        result["status"] = "ERROR"
        result["message"] = str(e)
        print(f"[{scene_id}] ERROR: {e}")
        return result


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 generate_s295_scenes.py <scene_id|all> [--dry]")
        print("       scene_id: S14, S15, S16, S20, or 'all'")
        print("       --dry: Show prompt without executing")
        sys.exit(1)

    target = sys.argv[1].upper()
    dry_run = "--dry" in sys.argv

    print("\n" + "="*60)
    print("§295 SCENE GENERATION — Runway Gen-3 Alpha Turbo")
    print("="*60)
    print(f"Generator: {GENERATOR_ENGINE}")
    print(f"Model: {GENERATOR_MODEL}")
    print(f"Invariante de textura: ACTIVE (mesmo motor para toda linhagem)")
    print(f"Dry run: {dry_run}")
    print()

    if target == "ALL":
        scenes = ["S14", "S15", "S16", "S20"]
    else:
        scenes = [target]

    results = []
    for scene_id in scenes:
        if scene_id not in SCENE_PROMPTS:
            print(f"[ERROR] Unknown scene: {scene_id}")
            continue

        result = generate_scene(scene_id, dry_run=dry_run)
        results.append(result)

        # Save individual result
        result_path = PRODUCTION_DIR / f"generation_{scene_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.json"
        with open(result_path, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"[{scene_id}] Result saved: {result_path}")
        print()

    # Summary
    print("="*60)
    print("SUMMARY")
    print("="*60)
    for r in results:
        status = r.get("status", "UNKNOWN")
        scene = r.get("scene", "?")
        if status == "GENERATED":
            print(f"  {scene}: ✅ {r.get('output_path')}")
        elif status == "DRY_RUN":
            print(f"  {scene}: 🔍 DRY RUN (prompt ready)")
        else:
            print(f"  {scene}: ❌ {status} - {r.get('message', '')[:50]}")

    print()
    print("Next step: Run validation with validate_s295_render.py")
    print("="*60)


if __name__ == "__main__":
    main()
