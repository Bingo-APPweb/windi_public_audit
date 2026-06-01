#!/usr/bin/env python3
"""
S01 Generation v2 — O Registo da Vida (Guardian Spec)
WINDI-HIOS Cinema · O Peso do Eco v2

Guardian specification (31 Mai 2026):
- Allgäu Alps, native spruce forest, alpine valley, golden sunset
- Elisa (~30), content creator, selfie-POV, vibrant energy
- Marcus sedan parked on trail behind her (proof chain S01→S02→S16)
- German speech: post-production (TTS + lip-sync)
- WINDI Ledger indicator: post-production overlay (§296)

Canonical line (pós): "Hallo meine Lieben! Ich zeige euch heute
einen atemberaubenden Blick auf die Alpen — hier in meiner
Lieblingsregion, dem Allgäu."

Sealed: §139 31 Mai 2026
Invariants: I9, I11, I14
"""
import os
import base64
import time
from datetime import datetime

# API Key
os.environ["RUNWAYML_API_SECRET"] = os.getenv("RUNWAY_API_KEY", "key_3831dff2c3ffdbda5363f300b320422be856d0acd6f99459baa6ed9c869b125f2dc9a6d25a4e282bb453b7890946cfb685153faa4fb027d60fa50b29616d0d85")

from runwayml import RunwayML

# First-frame: Elisa v2 anchor
ELISA_ANCHOR = "/opt/windi/hios/cinema/obras/o-peso-do-eco2/thumbs/elisa_anchor_v2_1280x720.png"

# Output directory
OUTPUT_DIR = "/opt/windi/hios/cinema/obras/o-peso-do-eco2/production/renders"
os.makedirs(OUTPUT_DIR, exist_ok=True)

print("=" * 60)
print("S01 v2 — O REGISTO DA VIDA (Guardian Spec)")
print("WINDI-HIOS Cinema · O Peso do Eco v2")
print("=" * 60)

# Load first-frame image
with open(ELISA_ANCHOR, "rb") as f:
    elisa_b64 = base64.b64encode(f.read()).decode()
elisa_uri = f"data:image/png;base64,{elisa_b64}"

print(f"\n🎬 First-frame: Elisa v2 anchor")
print(f"   Image size: {len(elisa_b64):,} bytes (base64)")

# PROMPT — Guardian spec, prioritized for jurisdiction (max 1000 chars)
# Priority: (1) Allgäu/Alps/golden hour, (2) Elisa selfie/vlog, (3) sedan
PROMPT = """Allgäu Alps, Bavaria. Golden sunset through native spruce forest. Alpine valley visible in background, mountain silhouettes against orange sky.

Young blonde woman (from reference, Elisa, early 30s) records selfie vlog on smartphone. Holds phone at arm's length, talks warmly to camera with genuine smile. Content creator energy - vibrant, confident, gestures with free hand.

Autumn leaves on forest trail. Warm golden light on her face. She turns slightly, showing the alpine view behind her.

Background detail: dark sedan parked on forest trail behind her, partially obscured by trees. Easy to miss.

Cinematic warmth. German alpine setting. Life and light."""

print(f"\n📝 Prompt ({len(PROMPT)} chars):")
print(PROMPT)

# Initialize client
client = RunwayML()

try:
    print("\n⏳ Submitting generation request (image-to-video)...")

    task = client.image_to_video.create(
        model="gen3a_turbo",
        prompt_image=elisa_uri,
        prompt_text=PROMPT,
        ratio="1280:768",
        duration=5
    )

    print(f"\n✅ Task created: {task.id}")

    # Poll for completion
    print("\n⏳ Waiting for generation...")
    start_time = time.time()

    while True:
        task_status = client.tasks.retrieve(task.id)
        status = task_status.status
        print(f"   Status: {status}")

        if status == "SUCCEEDED":
            elapsed = time.time() - start_time
            print(f"\n🎬 Task complete in {elapsed:.1f}s!")

            # Get output URL
            output_url = None
            if hasattr(task_status, 'output') and task_status.output:
                output_url = task_status.output[0] if isinstance(task_status.output, list) else task_status.output

            if output_url:
                print(f"\n📥 Output URL: {output_url}")

                # Download video
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_file = f"{OUTPUT_DIR}/S01_guardian_v2_{timestamp}.mp4"

                import urllib.request
                urllib.request.urlretrieve(output_url, output_file)
                print(f"✅ Downloaded: {output_file}")

                # Save metadata
                metadata = {
                    "scene": "S01",
                    "title": "O Registo da Vida",
                    "version": "v2-guardian",
                    "method": "image-to-video (first-frame)",
                    "task_id": task.id,
                    "status": "GENERATED",
                    "prompt": PROMPT,
                    "first_frame": ELISA_ANCHOR,
                    "output_file": output_file,
                    "output_url": output_url,
                    "timestamp": timestamp,
                    "duration_seconds": elapsed,
                    "canonical_line_de": "Hallo meine Lieben! Ich zeige euch heute einen atemberaubenden Blick auf die Alpen — hier in meiner Lieblingsregion, dem Allgäu.",
                    "validation_required": [
                        "Allgäu Alps setting (spruce forest, alpine valley)",
                        "Golden sunset light (warm, autumn)",
                        "Elisa content creator energy (vibrant, genuine)",
                        "Selfie-POV (phone at arm's length)",
                        "Marcus sedan visible on trail (proof chain)",
                        "NO tropical vegetation, NO eucalyptus"
                    ],
                    "post_production_notes": [
                        "Add German voice-over with canonical line (TTS/dubbing)",
                        "Add WINDI Ledger indicator to phone screen (§296 overlay)",
                        "Verify sedan visible for S16 continuity (proof chain)",
                        "Colour grade for golden hour warmth"
                    ]
                }

                import json
                meta_file = f"{OUTPUT_DIR}/S01_guardian_v2_{timestamp}.json"
                with open(meta_file, "w") as f:
                    json.dump(metadata, f, indent=2)

                print(f"\n📄 Metadata saved: {meta_file}")
                print(f"\n🔍 VALIDATION CHECKLIST:")
                for item in metadata["validation_required"]:
                    print(f"   [ ] {item}")

                print(f"\n📝 POST-PRODUCTION:")
                for item in metadata["post_production_notes"]:
                    print(f"   • {item}")
            else:
                print("⚠️ No output URL in response")
                print(f"   Task status: {task_status}")

            break

        elif status == "FAILED":
            print(f"\n❌ Generation failed")
            if hasattr(task_status, 'failure'):
                print(f"   Failure: {task_status.failure}")
            break

        else:
            time.sleep(10)  # Poll every 10 seconds

    print(f"\n✅ S01 v2 generation complete. Awaiting Human Dragon validation (I9).")

except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
