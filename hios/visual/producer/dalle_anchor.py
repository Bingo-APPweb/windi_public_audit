#!/usr/bin/env python3
"""
DALL-E 3 Anchor Generator — WINDI-HIOS Character Portraits
Generates static character anchors for video production.

Usage:
    python3 dalle_anchor.py "prompt" --out output.png

Requires:
    export OPENAI_API_KEY="sk-..."
"""

import os
import sys
import argparse
import requests
from pathlib import Path

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")


def generate_image(prompt: str, output_path: str, size: str = "1024x1024", quality: str = "hd"):
    """Generate image using DALL-E 3 API."""

    if not OPENAI_API_KEY:
        print("❌ OPENAI_API_KEY not set")
        sys.exit(1)

    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "gpt-image-2",
        "prompt": prompt,
        "n": 1,
        "size": size,
        "quality": quality
    }

    print(f"🎨 Generating with DALL-E 3...")
    print(f"   Size: {size} | Quality: {quality}")
    print(f"   Prompt: {prompt[:100]}...")

    response = requests.post(
        "https://api.openai.com/v1/images/generations",
        headers=headers,
        json=payload,
        timeout=300
    )

    if response.status_code == 429:
        print("⚠️  429 RATE LIMITED")
        sys.exit(1)

    if response.status_code != 200:
        print(f"❌ API Error {response.status_code}: {response.text[:500]}")
        sys.exit(1)

    data = response.json()

    # Debug: print response structure
    print(f"   📋 Response keys: {list(data.keys())}")

    # Handle different response formats
    if "data" in data and len(data["data"]) > 0:
        item = data["data"][0]
        image_url = item.get("url") or item.get("b64_json")
        revised_prompt = item.get("revised_prompt", "")
        is_base64 = "b64_json" in item
    else:
        print(f"❌ Unexpected response: {str(data)[:500]}")
        sys.exit(1)

    if revised_prompt:
        print(f"   📝 Revised: {revised_prompt[:80]}...")

    # Download/decode image
    print(f"📥 Saving to {output_path}...")

    if is_base64:
        import base64
        img_data = base64.b64decode(image_url)
        with open(output_path, "wb") as f:
            f.write(img_data)
    else:
        img_response = requests.get(image_url, timeout=60)
        with open(output_path, "wb") as f:
            f.write(img_response.content)

    size_kb = Path(output_path).stat().st_size / 1024
    print(f"✅ Saved: {output_path} ({size_kb:.0f} KB)")


def main():
    parser = argparse.ArgumentParser(description="DALL-E 3 Anchor Generator")
    parser.add_argument("prompt", help="Image generation prompt")
    parser.add_argument("--out", "-o", required=True, help="Output file path")
    parser.add_argument("--size", default="1024x1024",
                        choices=["1024x1024", "1792x1024", "1024x1792"])
    parser.add_argument("--quality", default="high", choices=["low", "medium", "high", "auto"])

    args = parser.parse_args()
    generate_image(args.prompt, args.out, args.size, args.quality)


if __name__ == "__main__":
    main()
