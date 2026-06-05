#!/usr/bin/env python3
"""
ANCHOR REGENERATION — Vance v2 (Likeness-Clean)
================================================
Regenerate Marcus Vance anchor with explicit divergence from real persons.

Prompt engineering to avoid celebrity likeness:
- Asymmetric features
- Unique combination of traits
- Explicit "not resembling any real person"

Liga IA+H · WINDI Publishing House · 05 Jun 2026
Constitutional: I9, I11, I14, I19 + Likeness Gate
"""

import os
import sys
import json
import time
import base64
import hashlib
from pathlib import Path
from datetime import datetime

import requests

# === PATHS ===
OUTPUT_DIR = Path("/home/windi/hios/cinema/obras/w-hios-forensic-unit/anchors/vance_v2_candidates")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def load_runway_key():
    env_file = Path("/opt/windi/.env")
    for line in env_file.read_text().splitlines():
        if line.startswith("RUNWAY_API_KEY="):
            return line.strip().split("=", 1)[1]
    return None

def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}")
    sys.stdout.flush()

# DIVERGENT PROMPT — designed to avoid convergence to any real person
VANCE_V2_PROMPT = """Portrait photograph of a fictional middle-aged male character.

REQUIRED UNIQUE FEATURES (do NOT resemble any real actor):
- Slightly asymmetric face with distinctive brow ridge
- Grey hair with natural recession at temples, NOT slicked back
- Short grey stubble (3-day beard), NOT clean-shaven
- Prominent nose with slight aquiline curve
- Deep-set eyes with heterochromia: one grey, one hazel
- Small scar above left eyebrow
- Weathered skin texture, outdoor complexion

WARDROBE:
- Dark charcoal suit, slightly rumpled
- No tie, open collar white shirt
- Silver lapel pin (small eagle)

LIGHTING & STYLE:
- Professional corporate portrait
- Neutral grey background
- Soft directional light from camera-left
- 4K quality, shallow depth of field

CHARACTER: Interpol senior inspector, late 50s, German-Austrian heritage.
This is a COMPLETELY FICTIONAL character for a film production.
Must NOT resemble any real celebrity, actor, or public figure."""

def generate_vance_v2():
    """Generate new Vance anchor with divergence from real persons."""

    log("=" * 70)
    log("ANCHOR REGENERATION — Vance v2 (Likeness-Clean)")
    log("=" * 70)

    api_key = load_runway_key()
    if not api_key:
        log("FATAL: No Runway API key")
        return None

    log(f"API Key: {api_key[:20]}...{api_key[-8:]}")

    # Using Runway for image generation (text-to-image)
    # Note: Runway Gen-4 is video, we need an image generator
    # Let's use the Gemini for image generation instead

    log("Using Gemini for image generation...")

    gemini_key = None
    env_file = Path("/opt/windi/.env")
    for line in env_file.read_text().splitlines():
        if line.startswith("GEMINI_API_KEY="):
            gemini_key = line.strip().split("=", 1)[1]
            break

    if not gemini_key:
        log("FATAL: No Gemini API key")
        return None

    log(f"Gemini Key: {gemini_key[:15]}...")

    # Use Gemini Imagen for image generation
    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=gemini_key)

        log("Generating image with Imagen...")
        log(f"Prompt (divergent): {VANCE_V2_PROMPT[:100]}...")

        response = client.models.generate_content(
            model="gemini-2.0-flash-preview-image-generation",
            contents=VANCE_V2_PROMPT,
            config=types.GenerateContentConfig(
                response_modalities=['IMAGE', 'TEXT']
            )
        )

        # Extract image from response
        for part in response.candidates[0].content.parts:
            if hasattr(part, 'inline_data') and part.inline_data:
                image_data = part.inline_data.data
                mime_type = part.inline_data.mime_type

                # Save image
                ext = "png" if "png" in mime_type else "jpg"
                timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                output_path = OUTPUT_DIR / f"vance_v2_candidate_{timestamp}.{ext}"

                with open(output_path, "wb") as f:
                    f.write(image_data)

                # Calculate hash
                img_hash = hashlib.sha256(image_data).hexdigest()

                log(f"Generated: {output_path.name}")
                log(f"Hash: sha256:{img_hash[:16]}...")

                # Save provenance
                provenance = {
                    "anchor_id": f"marcus.vance.anchor.v2.candidate.{timestamp}",
                    "character": "Marcus Vance",
                    "version": "v2-likeness-clean",
                    "source": {
                        "generator": "Gemini Imagen",
                        "model": "gemini-2.0-flash-preview-image-generation",
                        "prompt": VANCE_V2_PROMPT,
                        "generation_date": datetime.utcnow().isoformat() + "Z"
                    },
                    "likeness_gate": {
                        "status": "PENDING_VEO_TEST",
                        "reason": "v1 flagged by Veo celebrity filter",
                        "divergence_features": [
                            "heterochromia",
                            "asymmetric_face",
                            "stubble_not_clean_shaven",
                            "natural_hair_not_slicked",
                            "scar_above_eyebrow"
                        ]
                    },
                    "hash": f"sha256:{img_hash}",
                    "invariants": ["I9", "I11", "I14", "I19"],
                    "created": datetime.utcnow().isoformat() + "Z"
                }

                prov_path = OUTPUT_DIR / f"vance_v2_candidate_{timestamp}.provenance.json"
                with open(prov_path, "w") as f:
                    json.dump(provenance, f, indent=2)

                log(f"Provenance: {prov_path.name}")

                return output_path

        log("ERROR: No image in response")
        log(f"Response: {response}")
        return None

    except Exception as e:
        log(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_veo_filter(image_path: Path) -> bool:
    """Test if image passes Veo celebrity filter."""

    log("\n" + "=" * 50)
    log("TESTING VEO CELEBRITY FILTER")
    log("=" * 50)

    veo_key = None
    env_file = Path("/opt/windi/.env")
    for line in env_file.read_text().splitlines():
        if line.startswith("VEO_API_KEY="):
            veo_key = line.strip().split("=", 1)[1]
            break

    if not veo_key:
        log("No VEO key, skipping filter test")
        return None

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=veo_key)

        with open(image_path, "rb") as f:
            image_bytes = f.read()

        image_obj = types.Image(
            image_bytes=image_bytes,
            mime_type="image/png"
        )

        log("Submitting to Veo for filter test...")

        operation = client.models.generate_videos(
            model="veo-3.1-generate-preview",
            prompt="Person standing still, minimal movement, 2 seconds",
            image=image_obj,
        )

        # Wait for result
        start = time.time()
        while not operation.done and time.time() - start < 60:
            time.sleep(5)
            operation = client.operations.get(operation)

        # Check result
        if hasattr(operation, 'response'):
            resp = operation.response
            if hasattr(resp, 'rai_media_filtered_reasons') and resp.rai_media_filtered_reasons:
                log(f"❌ BLOCKED: {resp.rai_media_filtered_reasons}")
                return False
            elif hasattr(resp, 'generated_videos') and resp.generated_videos:
                log("✅ PASSED VEO FILTER")
                return True

        log("⚠️ Inconclusive result")
        return None

    except Exception as e:
        log(f"Filter test error: {e}")
        return None

def main():
    # Generate new anchor
    image_path = generate_vance_v2()

    if not image_path:
        log("Generation failed")
        return

    # Test Veo filter
    passed = test_veo_filter(image_path)

    log("\n" + "=" * 70)
    if passed is True:
        log("✅ VANCE V2 CANDIDATE: LIKENESS-CLEAN")
        log("Ready for extraction and SPINE validation")
    elif passed is False:
        log("❌ VANCE V2 CANDIDATE: STILL FLAGGED")
        log("Need to investigate or try different divergence")
    else:
        log("⚠️ VEO FILTER TEST INCONCLUSIVE")
        log("Manual review required")
    log("=" * 70)

if __name__ == "__main__":
    main()
