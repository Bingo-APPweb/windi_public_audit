#!/usr/bin/env python3
"""
S21 Generation with Veo 3.1 via Runway SDK
Scene: Marcus in courtroom with Elisa photo on screen
"""
import os
import base64
import time
from runwayml import RunwayML

# Set API key
os.environ["RUNWAYML_API_SECRET"] = "key_3831dff2c3ffdbda5363f300b320422be856d0acd6f99459baa6ed9c869b125f2dc9a6d25a4e282bb453b7890946cfb685153faa4fb027d60fa50b29616d0d85"

# Marcus reference image
MARCUS_IMG = "/opt/windi/hios/visual/producer/obras/o-peso-do-eco/thumbs/S09_marcus_intocavel.jpg"

# Convert to base64 data URI
with open(MARCUS_IMG, "rb") as f:
    marcus_b64 = base64.b64encode(f.read()).decode()
marcus_uri = f"data:image/jpeg;base64,{marcus_b64}"

print(f"🎬 Generating S21 with Veo 3.1 via Runway")
print(f"   Reference: Marcus (S09)")
print(f"   Image size: {len(marcus_b64)} bytes (base64)")

client = RunwayML()

prompt = """German courtroom, dramatic lighting.
The man from the reference image sits at the defendant's table, face clearly visible toward camera, serious expression.
Large courtroom screen behind him displays a photo of a young woman with ash-blonde hair.
Both faces clearly visible. Documentary realism, cinematic lighting."""

print(f"\n📝 Prompt: {prompt[:100]}...")

try:
    task = client.image_to_video.create(
        model="veo3.1",
        prompt_image=[{
            "uri": marcus_uri,
            "position": "first"
        }],
        prompt_text=prompt,
        ratio="1280:720",
        duration=4
    )

    print(f"\n✅ Task created: {task.id}")
    print(f"   Status: {task.status}")

    # Wait for completion
    print("\n⏳ Waiting for generation...")
    result = task.wait_for_task_output()

    print(f"\n🎬 Task complete!")
    print(f"   Output: {result}")

except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
