#!/usr/bin/env python3
"""
§296 UI Compositor — Plate + Overlay Vetorial
==============================================
Compõe a plate do gerador (Veo) com o overlay SVG da UI WINDI.

O gerador faz o mundo. A prova faz-se em pós.

Uso:
    python3 compose_windi_ui.py S14 /path/to/plate.mp4
    python3 compose_windi_ui.py S15 /path/to/plate.mp4 --receipt WINDI-xxx --hash abc123...

Liga IA+H · WINDI Publishing House · 30 Mai 2026
"""
import os
import sys
import json
import subprocess
import hashlib
from datetime import datetime
from pathlib import Path

# Paths
OVERLAYS_DIR = Path("/opt/windi/hios/cinema/obras/o-peso-do-eco/production/overlays")
OUTPUT_DIR = Path("/opt/windi/hios/cinema/obras/o-peso-do-eco/scenes/s295_renders")
PRODUCTION_DIR = Path("/opt/windi/hios/cinema/obras/o-peso-do-eco/production")

# Overlay mappings
OVERLAY_MAP = {
    "S14": "WINDI-UI-S14-MATCH.svg",
    "S15": "WINDI-UI-S15-INTEGRITY.svg",
    "S16": "WINDI-UI-S14-MATCH.svg",  # Smaller version, corner
    "S20": "WINDI-UI-S15-INTEGRITY.svg",  # Courtroom display
}


def sha256_file(filepath: str) -> str:
    """Compute SHA-256 hash of a file."""
    h = hashlib.sha256()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()


def inject_real_values(svg_content: str, receipt_id: str = None, content_hash: str = None) -> str:
    """
    Inject real Ledger values into SVG placeholders.
    This transforms decorative props into real proof.
    """
    if receipt_id:
        svg_content = svg_content.replace("{{RECEIPT_ID}}", receipt_id)
    if content_hash:
        # Show first 48 chars of hash for readability
        hash_display = content_hash[:48] + "…" if len(content_hash) > 48 else content_hash
        svg_content = svg_content.replace("{{HASH}}", hash_display)
    return svg_content


def svg_to_png(svg_path: str, png_path: str, width: int = 1920, height: int = 1080) -> bool:
    """Convert SVG to PNG using Inkscape or rsvg-convert."""
    # Try rsvg-convert first (faster)
    try:
        cmd = [
            "rsvg-convert",
            "-w", str(width),
            "-h", str(height),
            "-o", png_path,
            svg_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            return True
    except FileNotFoundError:
        pass

    # Fallback to Inkscape
    try:
        cmd = [
            "inkscape",
            "--export-type=png",
            f"--export-filename={png_path}",
            f"--export-width={width}",
            f"--export-height={height}",
            svg_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.returncode == 0
    except FileNotFoundError:
        print("[ERROR] Neither rsvg-convert nor inkscape found. Install one of them.")
        return False


def compose_video(plate_path: str, overlay_png: str, output_path: str,
                  overlay_x: int = 0, overlay_y: int = 0, opacity: float = 0.95) -> bool:
    """
    Compose plate video with PNG overlay using FFmpeg.

    For full-screen UI (S14, S15): overlay_x=0, overlay_y=0
    For corner UI (S16, S20): adjust coordinates
    """
    # FFmpeg filter for overlay with opacity
    filter_complex = f"[1:v]format=rgba,colorchannelmixer=aa={opacity}[overlay];[0:v][overlay]overlay={overlay_x}:{overlay_y}"

    cmd = [
        "ffmpeg",
        "-i", plate_path,
        "-i", overlay_png,
        "-filter_complex", filter_complex,
        "-c:v", "libx264",
        "-crf", "18",
        "-preset", "slow",
        "-c:a", "copy",
        "-y",
        output_path
    ]

    print(f"[COMPOSE] Running FFmpeg...")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"[ERROR] FFmpeg failed: {result.stderr}")
        return False

    return True


def compose_scene(scene_id: str, plate_path: str, receipt_id: str = None, content_hash: str = None) -> dict:
    """
    Full composition pipeline for a windi_on_screen scene.
    """
    result = {
        "scene": scene_id,
        "timestamp": datetime.now().isoformat(),
        "plate": plate_path,
        "status": "PENDING",
    }

    if scene_id not in OVERLAY_MAP:
        result["status"] = "ERROR"
        result["error"] = f"Unknown scene: {scene_id}"
        return result

    # 1. Load and process SVG
    svg_file = OVERLAYS_DIR / OVERLAY_MAP[scene_id]
    if not svg_file.exists():
        result["status"] = "ERROR"
        result["error"] = f"Overlay not found: {svg_file}"
        return result

    print(f"[{scene_id}] Loading overlay: {svg_file.name}")

    with open(svg_file, 'r') as f:
        svg_content = f.read()

    # 2. Inject real values if provided (S15, S20)
    if receipt_id or content_hash:
        print(f"[{scene_id}] Injecting real values: {receipt_id[:30] if receipt_id else 'none'}...")
        svg_content = inject_real_values(svg_content, receipt_id, content_hash)
        result["receipt_id"] = receipt_id
        result["injected_hash"] = content_hash[:16] + "..." if content_hash else None

    # 3. Convert SVG to PNG
    temp_svg = f"/tmp/compose_{scene_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.svg"
    temp_png = temp_svg.replace('.svg', '.png')

    with open(temp_svg, 'w') as f:
        f.write(svg_content)

    print(f"[{scene_id}] Converting SVG to PNG...")
    if not svg_to_png(temp_svg, temp_png):
        result["status"] = "ERROR"
        result["error"] = "SVG to PNG conversion failed"
        return result

    # 4. Compose video
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / f"{scene_id}_composed_{datetime.now().strftime('%Y%m%d%H%M%S')}.mp4"

    print(f"[{scene_id}] Composing plate + overlay...")
    if not compose_video(plate_path, temp_png, str(output_path)):
        result["status"] = "ERROR"
        result["error"] = "Video composition failed"
        return result

    # 5. Compute hash of composed video
    result["output_path"] = str(output_path)
    result["output_hash"] = sha256_file(str(output_path))
    result["status"] = "COMPOSED"

    print(f"[{scene_id}] SUCCESS: {output_path}")
    print(f"[{scene_id}] Hash: {result['output_hash'][:16]}...")

    # Cleanup temp files
    os.remove(temp_svg)
    os.remove(temp_png)

    return result


def main():
    if len(sys.argv) < 3:
        print("Usage: python3 compose_windi_ui.py <scene_id> <plate_path> [--receipt ID] [--hash HASH]")
        print("       scene_id: S14, S15, S16, S20")
        print("       --receipt: Real receipt ID from Ledger (for S15, S20)")
        print("       --hash: Real content hash from Ledger (for S15, S20)")
        sys.exit(1)

    scene_id = sys.argv[1].upper()
    plate_path = sys.argv[2]

    # Parse optional arguments
    receipt_id = None
    content_hash = None

    for i, arg in enumerate(sys.argv):
        if arg == "--receipt" and i + 1 < len(sys.argv):
            receipt_id = sys.argv[i + 1]
        elif arg == "--hash" and i + 1 < len(sys.argv):
            content_hash = sys.argv[i + 1]

    if not os.path.exists(plate_path):
        print(f"[ERROR] Plate not found: {plate_path}")
        sys.exit(1)

    print("\n" + "="*60)
    print("§296 UI COMPOSITOR — Plate + Overlay Vetorial")
    print("="*60)
    print(f"Scene: {scene_id}")
    print(f"Plate: {plate_path}")
    print(f"Overlay: {OVERLAY_MAP.get(scene_id, 'unknown')}")
    print()

    result = compose_scene(scene_id, plate_path, receipt_id, content_hash)

    # Save result
    result_path = PRODUCTION_DIR / f"composition_{scene_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.json"
    with open(result_path, 'w') as f:
        json.dump(result, f, indent=2)
    print(f"\nResult saved: {result_path}")

    print("\n" + "="*60)
    print(f"STATUS: {result['status']}")
    if result['status'] == 'COMPOSED':
        print(f"Output: {result.get('output_path')}")
        print(f"Hash: {result.get('output_hash', 'N/A')[:32]}...")
    else:
        print(f"Error: {result.get('error', 'Unknown')}")
    print("="*60 + "\n")

    sys.exit(0 if result['status'] == 'COMPOSED' else 1)


if __name__ == "__main__":
    main()
