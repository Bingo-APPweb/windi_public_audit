#!/usr/bin/env python3
"""
S09 Generation v2 — Marcus Intocável
WINDI-HIOS Cinema · O Peso do Eco v2

Scene: Elegant restaurant. Marcus dines with associates. Confident. Calm.
       Receives call, looks at screen, dismisses, continues eating.

Speech (DE): "Noch einen Wein, bitte" (lip-sync frontal)
Speech register: controlled, entitled (per CONTINUITY-BIBLE-001)

Problem to fix: v1 had Marcus speaking English frontally
Solution: Generate with German speech focus for post lip-sync

Anchor: Marcus_anchor_v2.jpg (restaurant, wine, suit, watch)
Sealed: §139 31 Mai 2026
Invariants: I9, I11, I14
"""
import os
import base64
import time
from datetime import datetime

os.environ["RUNWAYML_API_SECRET"] = os.getenv("RUNWAY_API_KEY", "key_3831dff2c3ffdbda5363f300b320422be856d0acd6f99459baa6ed9c869b125f2dc9a6d25a4e282bb453b7890946cfb685153faa4fb027d60fa50b29616d0d85")

from runwayml import RunwayML

# First-frame: Marcus v2 anchor (restaurant setting already present)
MARCUS_ANCHOR = "/opt/windi/hios/cinema/obras/o-peso-do-eco2/thumbs/Marcus_anchor_v2.jpg"

OUTPUT_DIR = "/opt/windi/hios/cinema/obras/o-peso-do-eco2/production/renders"
os.makedirs(OUTPUT_DIR, exist_ok=True)

print("=" * 60)
print("S09 v2 — MARCUS INTOCÁVEL")
print("WINDI-HIOS Cinema · O Peso do Eco v2")
print("=" * 60)

# Load first-frame image
with open(MARCUS_ANCHOR, "rb") as f:
    marcus_b64 = base64.b64encode(f.read()).decode()
marcus_uri = f"data:image/jpeg;base64,{marcus_b64}"

print(f"\n🎬 First-frame: Marcus v2 anchor")
print(f"   Image size: {len(marcus_b64):,} bytes (base64)")

# PROMPT — Restaurant scene, Marcus confident and dismissive
# Focus: subtle mouth movement, controlled demeanor, entitled air
# Post-production will add German voice "Noch einen Wein, bitte"
PROMPT = """Elegant upscale restaurant interior. Warm candlelight. Bokeh background.

Distinguished man (Marcus, from reference) in dark pinstripe suit, white shirt. Silver watch on wrist. Holds wine glass confidently.

He takes a sip of red wine. Sets glass down. Signals to waiter with subtle gesture. Speaks briefly to waiter. Controlled, calm demeanor. Entitled air.

Other diners in soft focus background. Crystal chandeliers. Rich dark wood and warm tones.

Cinematic thriller atmosphere. German high society. Confident and untouchable."""

print(f"\n📝 Prompt ({len(PROMPT)} chars):")
print(PROMPT)

client = RunwayML()

try:
    print("\n⏳ Submitting generation request (image-to-video)...")

    task = client.image_to_video.create(
        model="gen3a_turbo",
        prompt_image=marcus_uri,
        prompt_text=PROMPT,
        ratio="1280:768",
        duration=5
    )

    print(f"\n✅ Task created: {task.id}")
    print("\n⏳ Waiting for generation...")
    start_time = time.time()

    while True:
        task_status = client.tasks.retrieve(task.id)
        status = task_status.status
        print(f"   Status: {status}")

        if status == "SUCCEEDED":
            elapsed = time.time() - start_time
            print(f"\n🎬 Task complete in {elapsed:.1f}s!")

            output_url = None
            if hasattr(task_status, 'output') and task_status.output:
                output_url = task_status.output[0] if isinstance(task_status.output, list) else task_status.output

            if output_url:
                print(f"\n📥 Output URL: {output_url}")

                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_file = f"{OUTPUT_DIR}/S09_marcus_v2_{timestamp}.mp4"

                import urllib.request
                urllib.request.urlretrieve(output_url, output_file)
                print(f"✅ Downloaded: {output_file}")

                metadata = {
                    "scene": "S09",
                    "title": "Marcus Intocável",
                    "version": "v2",
                    "method": "image-to-video (first-frame)",
                    "task_id": task.id,
                    "status": "GENERATED",
                    "prompt": PROMPT,
                    "first_frame": MARCUS_ANCHOR,
                    "output_file": output_file,
                    "output_url": output_url,
                    "timestamp": timestamp,
                    "duration_seconds": elapsed,
                    "canonical_line_de": "Noch einen Wein, bitte",
                    "canonical_line_en": "Another wine, please",
                    "validation_required": [
                        "Marcus likeness preserved (anchor)",
                        "Restaurant setting (elegant, candles, chandeliers)",
                        "Dark pinstripe suit, white shirt",
                        "Silver watch visible",
                        "Wine glass interaction",
                        "Controlled, confident demeanor",
                        "Subtle mouth movement (for lip-sync)"
                    ],
                    "post_production_notes": [
                        "Add German voice-over: 'Noch einen Wein, bitte'",
                        "Lip-sync with Wav2Lip or similar",
                        "Colour grade for warm restaurant atmosphere",
                        "Verify silver watch visible (CONTINUITY-BIBLE)"
                    ],
                    "continuity_bible_ref": "MARCUS-§293",
                    "speech_register": "controlled, entitled"
                }

                import json
                meta_file = f"{OUTPUT_DIR}/S09_marcus_v2_{timestamp}.json"
                with open(meta_file, "w") as f:
                    json.dump(metadata, f, indent=2)

                print(f"\n📄 Metadata saved: {meta_file}")
                print(f"\n🔍 VALIDATION CHECKLIST:")
                for item in metadata["validation_required"]:
                    print(f"   [ ] {item}")

                print(f"\n📝 POST-PRODUCTION:")
                for item in metadata["post_production_notes"]:
                    print(f"   • {item}")

                print(f"\n🎤 CANONICAL LINE (DE): \"{metadata['canonical_line_de']}\"")
            else:
                print("⚠️ No output URL in response")

            break

        elif status == "FAILED":
            print(f"\n❌ Generation failed")
            if hasattr(task_status, 'failure'):
                print(f"   Failure: {task_status.failure}")
            break

        else:
            time.sleep(10)

    print(f"\n✅ S09 v2 complete. Awaiting Human Dragon validation (I9).")

except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
