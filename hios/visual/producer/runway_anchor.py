#!/usr/bin/env python3
"""
Runway Gen-4 Anchor Generator — WINDI-HIOS Character Videos
Generates video anchors using Runway Gen-4 with image reference.

Usage:
    python3 runway_anchor.py "prompt" --ref reference.png --out output.mp4

Author: Liga IA+H · WINDI Publishing House
Date: 2026-06-01
"""

import argparse
import base64
import json
import os
import sys
import time
from pathlib import Path

import requests

# =============================================================================
# Configuration
# =============================================================================

API_BASE = "https://api.dev.runwayml.com/v1"
API_VERSION = "2024-11-06"


def load_api_key() -> str:
    """Load Runway API key."""
    # Try environment variable first
    key = os.environ.get("RUNWAY_API_KEY")
    if key:
        return key

    # Try .env file
    env_file = Path("/opt/windi/.env")
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                if line.startswith("RUNWAY_API_KEY="):
                    return line.strip().split("=", 1)[1]

    print("ERROR: RUNWAY_API_KEY not found")
    sys.exit(1)


def load_image_base64(image_path: Path) -> str:
    """Load image and return base64 data URI."""
    suffix = image_path.suffix.lower()
    mime_types = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
    }

    if suffix not in mime_types:
        print(f"ERROR: Unsupported image format: {suffix}")
        sys.exit(1)

    mime_type = mime_types[suffix]

    with open(image_path, "rb") as f:
        data = base64.b64encode(f.read()).decode("utf-8")

    return f"data:{mime_type};base64,{data}"


def create_generation(api_key: str, prompt: str, image_path: Path, duration: int = 5) -> str:
    """Create a video generation task and return task ID."""

    url = f"{API_BASE}/image_to_video"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "X-Runway-Version": API_VERSION,
        "Content-Type": "application/json",
    }

    # Load image as base64 data URI
    image_data = load_image_base64(image_path)

    payload = {
        "model": "gen4_turbo",
        "promptImage": image_data,
        "promptText": prompt,
        "duration": duration,
        "ratio": "1280:720",
    }

    print("=" * 60)
    print("RUNWAY GEN-4 — Anchor Generator")
    print("=" * 60)
    print(f"Model:     gen4_turbo")
    print(f"Reference: {image_path.name}")
    print(f"Duration:  {duration}s")
    print(f"Prompt:    {prompt[:60]}...")
    print("-" * 60)
    print("Submitting job...")

    response = requests.post(url, headers=headers, json=payload, timeout=60)

    if response.status_code == 401:
        print("ERROR: Authentication failed - check API key")
        sys.exit(1)

    if response.status_code != 200 and response.status_code != 201:
        print(f"ERROR: API Error {response.status_code}")
        print(response.text[:500])
        sys.exit(1)

    result = response.json()
    task_id = result.get("id")

    if not task_id:
        print(f"ERROR: No task ID in response")
        print(json.dumps(result, indent=2)[:500])
        sys.exit(1)

    print(f"Job submitted: {task_id}")
    return task_id


def poll_task(api_key: str, task_id: str, max_wait: int = 600) -> dict:
    """Poll task until complete."""

    url = f"{API_BASE}/tasks/{task_id}"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "X-Runway-Version": API_VERSION,
    }

    start_time = time.time()
    poll_interval = 5

    print("Processing", end="", flush=True)

    while True:
        elapsed = time.time() - start_time
        if elapsed > max_wait:
            print(f"\nERROR: Timeout after {max_wait}s")
            sys.exit(1)

        response = requests.get(url, headers=headers, timeout=30)
        result = response.json()

        status = result.get("status")

        if status == "SUCCEEDED":
            print(f" DONE ({int(elapsed)}s)")
            return result

        if status == "FAILED":
            print(f"\nERROR: Task failed")
            print(json.dumps(result, indent=2)[:500])
            sys.exit(1)

        print(".", end="", flush=True)
        time.sleep(poll_interval)


def download_video(video_url: str, output_path: Path) -> None:
    """Download the generated video."""

    print("Downloading video...")

    response = requests.get(video_url, timeout=120)

    if response.status_code != 200:
        print(f"ERROR: Download failed: {response.status_code}")
        sys.exit(1)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "wb") as f:
        f.write(response.content)

    size_mb = len(response.content) / (1024 * 1024)
    print(f"SAVED: {output_path} ({size_mb:.1f} MB)")


def generate_video(prompt: str, reference_image: Path, output_path: Path, duration: int = 5):
    """Main generation pipeline."""

    api_key = load_api_key()

    # Create generation task
    task_id = create_generation(api_key, prompt, reference_image, duration)

    # Poll for completion
    result = poll_task(api_key, task_id)

    # Extract video URL
    output_urls = result.get("output", [])
    if not output_urls:
        print("ERROR: No output URLs in result")
        print(json.dumps(result, indent=2)[:500])
        sys.exit(1)

    video_url = output_urls[0]

    # Download video
    download_video(video_url, output_path)

    print("=" * 60)
    print(f"COMPLETE: {output_path}")
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description="Runway Gen-4 Anchor Generator")
    parser.add_argument("prompt", help="Video generation prompt")
    parser.add_argument("--ref", "-r", type=Path, required=True, help="Reference image")
    parser.add_argument("--out", "-o", type=Path, required=True, help="Output video path")
    parser.add_argument("--duration", "-d", type=int, default=5, choices=[5, 10], help="Duration in seconds")

    args = parser.parse_args()

    if not args.ref.exists():
        print(f"ERROR: Reference image not found: {args.ref}")
        sys.exit(1)

    generate_video(args.prompt, args.ref, args.out, args.duration)


if __name__ == "__main__":
    main()
