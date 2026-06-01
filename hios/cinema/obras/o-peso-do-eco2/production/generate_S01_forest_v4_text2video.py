#!/usr/bin/env python3
"""
S01 Generation v4 — O Registo da Vida (TEXT-TO-VIDEO)
WINDI-HIOS Cinema · O Peso do Eco v2

Abordagem diferente: text-to-video SEM first-frame
Para obter floresta densa no background (não preservar lago da âncora)

Human Dragon feedback: "A Cena precisa ser perfeita, atriz simpatica
e um ambiente de floresta e um carro se vê sutilmente atras"

Sealed: §139 31 Mai 2026
Invariants: I9, I11, I14
"""
import os
import time
from datetime import datetime

os.environ["RUNWAYML_API_SECRET"] = os.getenv("RUNWAY_API_KEY", "key_3831dff2c3ffdbda5363f300b320422be856d0acd6f99459baa6ed9c869b125f2dc9a6d25a4e282bb453b7890946cfb685153faa4fb027d60fa50b29616d0d85")

from runwayml import RunwayML

OUTPUT_DIR = "/opt/windi/hios/cinema/obras/o-peso-do-eco2/production/renders"
os.makedirs(OUTPUT_DIR, exist_ok=True)

print("=" * 60)
print("S01 v4 — O REGISTO DA VIDA (TEXT-TO-VIDEO)")
print("WINDI-HIOS Cinema · O Peso do Eco v2")
print("=" * 60)
print("\n🎬 Modo: TEXT-TO-VIDEO (sem first-frame)")
print("   Objectivo: Floresta densa + Elisa + sedan hint")

# PROMPT — Muito detalhado para compensar falta de first-frame
# Prioridade: (1) Floresta densa escura, (2) Elisa simpática, (3) sedan hint
PROMPT = """Dense dark Bavarian forest. Tall spruce and fir trees close together, shadows between trunks. Narrow forest trail. Moody atmosphere, late afternoon golden light filtering through canopy.

Young blonde woman (Elisa, early 30s, German) records selfie vlog on smartphone. Warm genuine smile, vibrant content creator energy, talks to camera with enthusiasm. She wears casual autumn clothes.

Behind her through the trees: dark sedan barely visible, parked on forest trail. Cinematic thriller atmosphere. German woodland setting."""

print(f"\n📝 Prompt ({len(PROMPT)} chars):")
print(PROMPT)

client = RunwayML()

try:
    print("\n⏳ Submitting text-to-video request...")

    # Text-to-video (sem prompt_image)
    task = client.text_to_video.create(
        model="gen3a_turbo",
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
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_file = f"{OUTPUT_DIR}/S01_forest_v4_text2video_{timestamp}.mp4"

                import urllib.request
                urllib.request.urlretrieve(output_url, output_file)
                print(f"✅ Downloaded: {output_file}")

                metadata = {
                    "scene": "S01",
                    "title": "O Registo da Vida",
                    "version": "v4-text2video",
                    "method": "text-to-video (NO first-frame)",
                    "task_id": task.id,
                    "prompt": PROMPT,
                    "output_file": output_file,
                    "timestamp": timestamp,
                    "validation_required": [
                        "DENSE FOREST (spruce/fir, trees close together)",
                        "Forest trail visible",
                        "Elisa: blonde, warm smile, content creator energy",
                        "Selfie-POV (phone held toward camera)",
                        "Sedan hint in background (proof chain)",
                        "Moody atmosphere (thriller setup)"
                    ],
                    "note": "Text-to-video approach - no first-frame anchor used"
                }

                import json
                meta_file = f"{OUTPUT_DIR}/S01_forest_v4_text2video_{timestamp}.json"
                with open(meta_file, "w") as f:
                    json.dump(metadata, f, indent=2)

                print(f"\n📄 Metadata: {meta_file}")
                print(f"\n🔍 VALIDATION:")
                for item in metadata["validation_required"]:
                    print(f"   [ ] {item}")
            break

        elif status == "FAILED":
            print(f"\n❌ Generation failed")
            if hasattr(task_status, 'failure'):
                print(f"   Failure: {task_status.failure}")
            break
        else:
            time.sleep(10)

    print(f"\n✅ S01 v4 complete. Awaiting Human Dragon validation (I9).")

except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
