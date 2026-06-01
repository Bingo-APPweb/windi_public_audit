#!/usr/bin/env python3
"""
S08 Generation v2 — Colheita de Pistas
WINDI-HIOS Cinema · O Peso do Eco v2

Scene: Helena kneels in mud, latex gloves, collects car fragments.
       Finds Elisa's broken phone. Places in evidence bag.

Location: FOREST-CRIMESCENE (same as S07)
Character: HELENA-§293 (dark navy wool coat, blonde hair pulled back)
Speech (DE): "Das Handy... vielleicht unsere einzige Chance"

Anchor: Helena_anchor_v2.png (crime scene, forensic team, misty forest)
Continuity: Same location as S07 (Bavarian forest crime scene)

Sealed: §139 01 Jun 2026
Invariants: I9, I11, I14
"""
import os
import base64
import time
from datetime import datetime

os.environ["RUNWAYML_API_SECRET"] = os.getenv("RUNWAY_API_KEY", "key_3831dff2c3ffdbda5363f300b320422be856d0acd6f99459baa6ed9c869b125f2dc9a6d25a4e282bb453b7890946cfb685153faa4fb027d60fa50b29616d0d85")

from runwayml import RunwayML

# First-frame: Helena v2 anchor (crime scene setting already present)
HELENA_ANCHOR = "/opt/windi/hios/cinema/obras/o-peso-do-eco2/thumbs/Helena_anchor_v2.png"

OUTPUT_DIR = "/opt/windi/hios/cinema/obras/o-peso-do-eco2/production/renders"
os.makedirs(OUTPUT_DIR, exist_ok=True)

print("=" * 60)
print("S08 v2 — COLHEITA DE PISTAS")
print("WINDI-HIOS Cinema · O Peso do Eco v2")
print("=" * 60)

# Load first-frame image
with open(HELENA_ANCHOR, "rb") as f:
    helena_b64 = base64.b64encode(f.read()).decode()
helena_uri = f"data:image/png;base64,{helena_b64}"

print(f"\n🎬 First-frame: Helena v2 anchor")
print(f"   Image size: {len(helena_b64):,} bytes (base64)")

# PROMPT — Evidence collection at crime scene
# Focus: kneeling, latex gloves, finding phone, evidence bag
PROMPT = """Cold misty Bavarian forest crime scene. Blue forensic atmosphere.

Woman detective (Helena, from reference, dark navy coat, blonde hair pulled back) kneels carefully on muddy forest floor. Wears blue latex gloves.

She examines something on the ground. Picks up a broken smartphone carefully. Holds it up, examines it. Places it in clear evidence bag.

Forensic team in white suits visible in misty background. Autumn leaves on wet ground. Professional, methodical investigation.

Cinematic thriller. German police procedure. Cold blue tones."""

print(f"\n📝 Prompt ({len(PROMPT)} chars):")
print(PROMPT)

client = RunwayML()

try:
    print("\n⏳ Submitting generation request (image-to-video)...")

    task = client.image_to_video.create(
        model="gen3a_turbo",
        prompt_image=helena_uri,
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
                output_file = f"{OUTPUT_DIR}/S08_evidence_v2_{timestamp}.mp4"

                import urllib.request
                urllib.request.urlretrieve(output_url, output_file)
                print(f"✅ Downloaded: {output_file}")

                metadata = {
                    "scene": "S08",
                    "title": "Colheita de Pistas",
                    "version": "v2",
                    "method": "image-to-video (first-frame)",
                    "task_id": task.id,
                    "status": "GENERATED",
                    "prompt": PROMPT,
                    "first_frame": HELENA_ANCHOR,
                    "output_file": output_file,
                    "output_url": output_url,
                    "timestamp": timestamp,
                    "duration_seconds": elapsed,
                    "canonical_line_de": "Das Handy... vielleicht unsere einzige Chance",
                    "canonical_line_en": "The phone... maybe our only chance",
                    "validation_required": [
                        "Helena likeness preserved (anchor)",
                        "Dark navy wool coat visible",
                        "Blonde hair pulled back",
                        "Crime scene setting (misty forest)",
                        "Kneeling/evidence collection motion",
                        "Latex gloves visible (blue)",
                        "Phone/evidence interaction",
                        "Forensic team in background"
                    ],
                    "post_production_notes": [
                        "Add German voice-over: 'Das Handy... vielleicht unsere einzige Chance'",
                        "Verify continuity with S07 (same forest location)",
                        "Colour grade for cold blue forensic atmosphere",
                        "Add phone screen detail if needed (post overlay)"
                    ],
                    "continuity_bible_ref": "HELENA-§293",
                    "continuity_with": ["S07"],
                    "speech_register": "calm, precise, low"
                }

                import json
                meta_file = f"{OUTPUT_DIR}/S08_evidence_v2_{timestamp}.json"
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

    print(f"\n✅ S08 v2 complete. Awaiting Human Dragon validation (I9).")

except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
