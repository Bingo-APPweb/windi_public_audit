#!/usr/bin/env python3
"""
Imagen 4 Anchor Generator — WINDI-HIOS Character Portraits
Generates static character anchors using Google Imagen 4 API.

Usage:
    python3 imagen_anchor.py "prompt" --out output.png

Author: Liga IA+H · WINDI Publishing House
Date: 2026-06-01
"""

import argparse
import base64
import json
import os
import sys
from pathlib import Path

import requests

# =============================================================================
# Configuration
# =============================================================================

API_BASE = "https://generativelanguage.googleapis.com/v1beta"
MODEL = "imagen-4.0-generate-001"  # Standard Imagen 4


def load_api_key() -> str:
    """Load Gemini API key."""
    # Try environment variable first
    key = os.environ.get("GEMINI_API_KEY")
    if key:
        return key

    # Try .env.keys file
    env_file = Path("/opt/windi/.env.keys")
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                if line.startswith("GEMINI_API_KEY="):
                    return line.strip().split("=", 1)[1]

    print("ERROR: GEMINI_API_KEY not found")
    sys.exit(1)


def generate_image(prompt: str, output_path: str):
    """Generate image using Imagen 4 API."""

    api_key = load_api_key()
    url = f"{API_BASE}/models/{MODEL}:predict?key={api_key}"

    payload = {
        "instances": [
            {"prompt": prompt}
        ],
        "parameters": {
            "sampleCount": 1,
            "aspectRatio": "1:1",
            "outputOptions": {
                "mimeType": "image/png"
            }
        }
    }

    print("=" * 60)
    print("IMAGEN 4 — Anchor Generator")
    print("=" * 60)
    print(f"Model:  {MODEL}")
    print(f"Prompt: {prompt[:80]}...")
    print(f"Output: {output_path}")
    print("-" * 60)
    print("Generating...")

    response = requests.post(url, json=payload, timeout=120)

    if response.status_code != 200:
        print(f"ERROR: API Error {response.status_code}")
        print(response.text[:500])
        sys.exit(1)

    result = response.json()

    # Debug
    # print(f"Response keys: {list(result.keys())}")

    # Extract image data
    try:
        predictions = result.get("predictions", [])
        if not predictions:
            print(f"ERROR: No predictions in response")
            print(json.dumps(result, indent=2)[:500])
            sys.exit(1)

        # The image is base64 encoded
        image_b64 = predictions[0].get("bytesBase64Encoded")
        if not image_b64:
            # Try alternative field names
            image_b64 = predictions[0].get("image", {}).get("bytesBase64Encoded")

        if not image_b64:
            print(f"ERROR: Could not extract image data")
            print(f"Prediction keys: {list(predictions[0].keys())}")
            sys.exit(1)

    except (KeyError, IndexError) as e:
        print(f"ERROR: Failed to parse response: {e}")
        print(json.dumps(result, indent=2)[:500])
        sys.exit(1)

    # Decode and save
    image_data = base64.b64decode(image_b64)

    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, "wb") as f:
        f.write(image_data)

    size_kb = output_file.stat().st_size / 1024
    print(f"SAVED: {output_path} ({size_kb:.0f} KB)")
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description="Imagen 4 Anchor Generator")
    parser.add_argument("prompt", help="Image generation prompt")
    parser.add_argument("--out", "-o", required=True, help="Output file path")

    args = parser.parse_args()
    generate_image(args.prompt, args.out)


if __name__ == "__main__":
    main()
