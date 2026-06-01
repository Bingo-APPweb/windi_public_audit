#!/usr/bin/env python3
"""
WINDI Veo Producer — Automated Video Generation Pipeline
=========================================================
Uses Google Veo 3.x API with optional reference images for character continuity.

Usage:
    python veo_producer.py "prompt text" --ref image.png --output video.mp4
    python veo_producer.py "prompt text" --model veo-3.1-fast

Author: Liga IA+H · WINDI Publishing House
Date: 2026-05-22
"""

import argparse
import base64
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from datetime import datetime
from typing import Optional, Tuple

import requests

# Lei da Proveniência Inseparável — import provenance module
from provenance import (
    ProvenanceWriter,
    TransformationRecorder,
    compute_file_hash,
    get_provenance_path
)

# =============================================================================
# Configuration
# =============================================================================

API_BASE = "https://generativelanguage.googleapis.com/v1beta"
DEFAULT_MODEL = "veo-3.1-generate-preview"

AVAILABLE_MODELS = {
    "veo-2": "veo-2.0-generate-001",
    "veo-3": "veo-3.0-generate-001",
    "veo-3-fast": "veo-3.0-fast-generate-001",
    "veo-3.1": "veo-3.1-generate-preview",
    "veo-3.1-fast": "veo-3.1-fast-generate-preview",
    "veo-3.1-lite": "veo-3.1-lite-generate-preview",
}

OUTPUT_DIR = Path("/opt/windi/hios/visual/producer/output")
FRAMES_DIR = Path("/opt/windi/hios/visual/producer/frames")


# =============================================================================
# API Key Management
# =============================================================================

def load_api_key(key_num: int = 1) -> str:
    """Load API key from .env.keys file.

    Args:
        key_num: Which key to load (1 = .env.keys, 2 = .env.keys.2, 3 = .env.keys.3)
    """
    if key_num == 3:
        env_file = Path("/opt/windi/.env.keys.3")
    elif key_num == 2:
        env_file = Path("/opt/windi/.env.keys.2")
    else:
        env_file = Path("/opt/windi/.env.keys")

    if not env_file.exists():
        print(f"❌ API key file not found: {env_file}")
        print("   Create it with: echo 'GEMINI_API_KEY=your-key' > /opt/windi/.env.keys")
        sys.exit(1)

    with open(env_file) as f:
        for line in f:
            if line.startswith("GEMINI_API_KEY="):
                return line.strip().split("=", 1)[1]

    print(f"❌ GEMINI_API_KEY not found in {env_file}")
    sys.exit(1)


# =============================================================================
# Image Handling
# =============================================================================

def load_image_base64(image_path: Path) -> tuple[str, str]:
    """Load image and return (base64_data, mime_type)."""
    suffix = image_path.suffix.lower()
    mime_types = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
    }

    if suffix not in mime_types:
        print(f"❌ Unsupported image format: {suffix}")
        print(f"   Supported: {list(mime_types.keys())}")
        sys.exit(1)

    mime_type = mime_types[suffix]

    with open(image_path, "rb") as f:
        data = base64.b64encode(f.read()).decode("utf-8")

    return data, mime_type


# =============================================================================
# Veo API Functions
# =============================================================================

def submit_video_job(
    api_key: str,
    prompt: str,
    model: str,
    reference_image: Path | None = None,
    aspect_ratio: str = "16:9",
) -> str:
    """Submit video generation job and return operation name."""

    url = f"{API_BASE}/models/{model}:predictLongRunning?key={api_key}"

    # Build request payload
    instance = {"prompt": prompt}

    if reference_image:
        image_data, mime_type = load_image_base64(reference_image)
        instance["referenceImages"] = [
            {
                "image": {
                    "bytesBase64Encoded": image_data,
                    "mimeType": mime_type,
                },
                "referenceType": "asset",
            }
        ]

    payload = {
        "instances": [instance],
        "parameters": {
            "aspectRatio": aspect_ratio,
            "sampleCount": 1,
        },
    }

    print(f"📤 Submitting to {model}...")
    if reference_image:
        print(f"   Reference: {reference_image.name}")

    response = requests.post(url, json=payload, timeout=60)

    if response.status_code != 200:
        print(f"❌ API Error {response.status_code}:")
        print(response.text)
        sys.exit(1)

    result = response.json()

    if "error" in result:
        print(f"❌ API Error: {result['error']['message']}")
        sys.exit(1)

    operation_name = result.get("name")
    if not operation_name:
        print(f"❌ No operation name in response: {result}")
        sys.exit(1)

    print(f"✅ Job submitted: {operation_name.split('/')[-1]}")
    return operation_name


def poll_operation(api_key: str, operation_name: str, max_wait: int = 300) -> dict:
    """Poll operation until complete or timeout."""

    url = f"{API_BASE}/{operation_name}?key={api_key}"
    start_time = time.time()
    poll_interval = 5

    print("⏳ Processing", end="", flush=True)

    while True:
        elapsed = time.time() - start_time
        if elapsed > max_wait:
            print(f"\n❌ Timeout after {max_wait}s")
            sys.exit(1)

        response = requests.get(url, timeout=30)
        result = response.json()

        if result.get("done"):
            print(f" ✅ ({int(elapsed)}s)")
            return result

        print(".", end="", flush=True)
        time.sleep(poll_interval)


def download_video(api_key: str, video_uri: str, output_path: Path) -> None:
    """Download generated video."""

    # Add API key to URI
    if "?" in video_uri:
        download_url = f"{video_uri}&key={api_key}"
    else:
        download_url = f"{video_uri}?key={api_key}"

    print(f"📥 Downloading video...")

    response = requests.get(download_url, timeout=120)

    if response.status_code != 200:
        print(f"❌ Download failed: {response.status_code}")
        sys.exit(1)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "wb") as f:
        f.write(response.content)

    size_mb = len(response.content) / (1024 * 1024)
    print(f"✅ Saved: {output_path} ({size_mb:.1f} MB)")


def extract_preview_frames(video_path: Path, num_frames: int = 4) -> list[Path]:
    """Extract preview frames using ffmpeg."""

    frames_dir = FRAMES_DIR / video_path.stem
    frames_dir.mkdir(parents=True, exist_ok=True)

    # Get video duration
    probe_cmd = [
        "ffprobe", "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(video_path)
    ]

    try:
        duration = float(subprocess.check_output(probe_cmd).decode().strip())
    except (subprocess.CalledProcessError, ValueError):
        duration = 8.0  # Default

    # Calculate frame positions
    fps = 24
    total_frames = int(duration * fps)
    frame_positions = [int(i * total_frames / num_frames) for i in range(num_frames)]

    # Build select filter
    select_expr = "+".join([f"eq(n,{pos})" for pos in frame_positions])

    output_pattern = str(frames_dir / "frame_%02d.png")

    cmd = [
        "ffmpeg", "-y",
        "-i", str(video_path),
        "-vf", f"select='{select_expr}'",
        "-vsync", "vfr",
        output_pattern
    ]

    subprocess.run(cmd, capture_output=True)

    frames = sorted(frames_dir.glob("frame_*.png"))
    print(f"🖼️  Extracted {len(frames)} preview frames → {frames_dir}/")

    return frames


def get_video_info(video_path: Path) -> dict:
    """Get video metadata using ffprobe."""

    cmd = [
        "ffprobe", "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height,r_frame_rate,duration,bit_rate",
        "-of", "json",
        str(video_path)
    ]

    try:
        output = subprocess.check_output(cmd).decode()
        data = json.loads(output)
        stream = data.get("streams", [{}])[0]

        # Parse frame rate
        fps_str = stream.get("r_frame_rate", "24/1")
        if "/" in fps_str:
            num, den = fps_str.split("/")
            fps = int(num) / int(den)
        else:
            fps = float(fps_str)

        return {
            "width": stream.get("width", 0),
            "height": stream.get("height", 0),
            "fps": fps,
            "duration": float(stream.get("duration", 0)),
            "bitrate": int(stream.get("bit_rate", 0)),
        }
    except Exception as e:
        return {"error": str(e)}


# =============================================================================
# Main Pipeline
# =============================================================================

def generate_video(
    prompt: str,
    model: str = DEFAULT_MODEL,
    reference_image: Path | None = None,
    output: Path | None = None,
    aspect_ratio: str = "16:9",
    extract_frames: bool = True,
    key_num: int = 1,
    # WINDI provenance metadata (Lei da Proveniência Inseparável)
    project: str | None = None,
    scene: str | None = None,
    character: str | None = None,
    purpose: str = "scene",
) -> Tuple[Path, Path]:
    """
    Main video generation pipeline with atomic provenance.

    Returns (video_path, provenance_path).

    Lei da Proveniência Inseparável: generation and receipt are atomic.
    The provenance sidecar is written BEFORE any post-processing.
    """

    # Load API key
    api_key = load_api_key(key_num)

    # Generate output filename if not provided
    if output is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        model_short = model.split("-")[0] + model.split("-")[1]
        output = OUTPUT_DIR / f"windi_{model_short}_{timestamp}.mp4"

    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("🎬 WINDI Veo Producer (with Provenance)")
    print("=" * 60)
    print(f"Model:  {model}")
    print(f"Prompt: {prompt[:80]}{'...' if len(prompt) > 80 else ''}")
    print(f"Output: {output}")
    print("-" * 60)

    # Initialize provenance writer (Lei da Proveniência Inseparável)
    prov_writer = ProvenanceWriter(
        generator="veo",
        model=model,
        elo_number=2,
        elo_type="generated_video",
        project=project,
        scene=scene,
        character=character,
        purpose=purpose
    )
    prov_writer.set_prompt(prompt)
    prov_writer.set_parameters(aspect_ratio=aspect_ratio)

    # Handle reference image
    if reference_image:
        ref_path = Path(reference_image)
        ref_hash = compute_file_hash(ref_path)
        prov_writer.set_reference_images([(ref_path.name, ref_hash, "character")])

    # Track timing
    start_time = time.time()

    # Submit job
    operation_name = submit_video_job(
        api_key=api_key,
        prompt=prompt,
        model=model,
        reference_image=reference_image,
        aspect_ratio=aspect_ratio,
    )

    # Poll for completion
    result = poll_operation(api_key, operation_name)

    # Extract video URI
    try:
        video_uri = result["response"]["generateVideoResponse"]["generatedSamples"][0]["video"]["uri"]
    except (KeyError, IndexError):
        print(f"❌ Could not extract video URI from response:")
        print(json.dumps(result, indent=2))
        sys.exit(1)

    # Download video
    download_video(api_key, video_uri, output)

    # Record API response metadata
    elapsed = time.time() - start_time
    prov_writer.set_api_response(
        operation_id=operation_name.split("/")[-1] if "/" in operation_name else operation_name,
        duration_seconds=elapsed,
        status="completed"
    )

    # SEAL PROVENANCE IMMEDIATELY — before any post-processing
    # This is the core of Lei da Proveniência Inseparável
    provenance_path = prov_writer.seal(output)
    print(f"📜 Provenance sealed: {provenance_path.name}")

    # Get video info
    info = get_video_info(output)
    print(f"📊 Video: {info.get('width')}x{info.get('height')} @ {info.get('fps')}fps, {info.get('duration'):.1f}s")

    # Extract preview frames (post-processing — provenance already sealed)
    if extract_frames:
        extract_preview_frames(output)

    print("-" * 60)
    print(f"✅ Complete: {output}")
    print(f"📜 Provenance: {provenance_path}")
    print("=" * 60)

    return output, provenance_path


# =============================================================================
# CLI Interface
# =============================================================================

def list_models():
    """List available models."""
    print("\n📋 Available Models:\n")
    for alias, full_name in AVAILABLE_MODELS.items():
        marker = "→" if alias == "veo-3.1" else " "
        print(f"  {marker} {alias:15} {full_name}")
    print(f"\n  Default: veo-3.1\n")


def main():
    parser = argparse.ArgumentParser(
        description="WINDI Veo Producer — Automated Video Generation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s "A dragon flying over mountains"
  %(prog)s "Man walking in city" --ref character.png
  %(prog)s "Fast action scene" --model veo-3.1-fast
  %(prog)s --list-models
        """,
    )

    parser.add_argument(
        "prompt",
        nargs="?",
        help="Video generation prompt",
    )

    parser.add_argument(
        "--ref", "-r",
        type=Path,
        help="Reference image for character/style continuity",
    )

    parser.add_argument(
        "--model", "-m",
        default="veo-3.1",
        choices=list(AVAILABLE_MODELS.keys()),
        help="Model to use (default: veo-3.1)",
    )

    parser.add_argument(
        "--output", "-o",
        type=Path,
        help="Output video path (auto-generated if not specified)",
    )

    parser.add_argument(
        "--aspect", "-a",
        default="16:9",
        choices=["16:9", "9:16", "1:1"],
        help="Aspect ratio (default: 16:9)",
    )

    parser.add_argument(
        "--no-frames",
        action="store_true",
        help="Skip frame extraction",
    )

    parser.add_argument(
        "--list-models",
        action="store_true",
        help="List available models",
    )

    parser.add_argument(
        "--key", "-k",
        type=int,
        default=1,
        choices=[1, 2, 3],
        help="Which API key to use (1 = primary, 2 = secondary, 3 = tertiary)",
    )

    # WINDI provenance metadata
    parser.add_argument(
        "--project",
        help="Project name for provenance (e.g., 'o-peso-do-eco')",
    )

    parser.add_argument(
        "--scene",
        help="Scene identifier for provenance (e.g., 'S14')",
    )

    parser.add_argument(
        "--character",
        help="Character name for anchor provenance (e.g., 'helena')",
    )

    parser.add_argument(
        "--purpose",
        default="scene",
        choices=["anchor", "scene", "test", "reference"],
        help="Purpose of this generation (default: scene)",
    )

    args = parser.parse_args()

    if args.list_models:
        list_models()
        return

    if not args.prompt:
        parser.print_help()
        print("\n❌ Error: prompt is required")
        sys.exit(1)

    # Validate reference image if provided
    if args.ref and not args.ref.exists():
        print(f"❌ Reference image not found: {args.ref}")
        sys.exit(1)

    # Resolve model name
    model = AVAILABLE_MODELS.get(args.model, args.model)

    # Run pipeline (now returns tuple with provenance)
    video_path, prov_path = generate_video(
        prompt=args.prompt,
        model=model,
        reference_image=args.ref,
        output=args.output,
        aspect_ratio=args.aspect,
        extract_frames=not args.no_frames,
        key_num=args.key,
        project=args.project,
        scene=args.scene,
        character=args.character,
        purpose=args.purpose,
    )

    # Print final provenance info
    print(f"\n🔐 Lei da Proveniência Inseparável: artifact born with provenance")
    print(f"   Video: {video_path}")
    print(f"   Sidecar: {prov_path}")


if __name__ == "__main__":
    main()
