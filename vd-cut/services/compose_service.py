"""
W-OBS-GATE — Cloud-Side Composition Service
FFmpeg-based video composition with sovereign overlays

Liga IA+H · Kempten, Bavaria · 2026
"AI processes. Human decides. WINDI guarantees."

Architecture:
- Scene templates define composition layouts
- FFmpeg filter_complex for real-time composition
- Overlays: QR code, timestamp, verdict badge, WINDI logo
- No external OBS dependency (100% local FFmpeg)

Future: Can upgrade to libobs-headless for advanced scenes
"""

import os
import json
import asyncio
import hashlib
import logging
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime, timezone

log = logging.getLogger("w-vd-cut-001.compose")

# Paths
BASE_DIR = Path("/opt/windi/vd-cut")
ASSETS_DIR = BASE_DIR / "assets" / "overlays"
TEMP_DIR = Path("/tmp/windi-compose")

# Ensure directories exist
ASSETS_DIR.mkdir(parents=True, exist_ok=True)
TEMP_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class SceneTemplate:
    """Definition of a composition scene."""
    name: str
    description: str
    overlay_position: str     # "top-left", "top-right", "bottom-left", "bottom-right"
    show_timestamp: bool
    show_qr: bool
    show_verdict: bool
    show_logo: bool
    text_color: str           # Hex color
    background_opacity: float  # 0.0-1.0 for overlay backgrounds


# Pre-defined scene templates
SCENES: Dict[str, SceneTemplate] = {
    "berlin_pitch": SceneTemplate(
        name="Berlin Pitch Mode",
        description="Professional presentation layout with verification badge",
        overlay_position="bottom-right",
        show_timestamp=True,
        show_qr=True,
        show_verdict=True,
        show_logo=True,
        text_color="#C4A35A",  # WINDI Gold
        background_opacity=0.7
    ),
    "forensic": SceneTemplate(
        name="Forensic Mode",
        description="Full forensic data overlay for legal/audit purposes",
        overlay_position="bottom-left",
        show_timestamp=True,
        show_qr=True,
        show_verdict=True,
        show_logo=True,
        text_color="#FFFFFF",
        background_opacity=0.85
    ),
    "clean": SceneTemplate(
        name="Clean Mode",
        description="Minimal overlay - just QR verification",
        overlay_position="bottom-right",
        show_timestamp=False,
        show_qr=True,
        show_verdict=False,
        show_logo=False,
        text_color="#FFFFFF",
        background_opacity=0.5
    ),
    "broadcast": SceneTemplate(
        name="Broadcast Mode",
        description="TV-ready with persistent lower-third",
        overlay_position="bottom-left",
        show_timestamp=True,
        show_qr=False,
        show_verdict=True,
        show_logo=True,
        text_color="#F5F0E0",  # WINDI Parchment
        background_opacity=0.8
    ),
    "social": SceneTemplate(
        name="Social Media Mode",
        description="Optimized for vertical/square social formats",
        overlay_position="top-right",
        show_timestamp=False,
        show_qr=True,
        show_verdict=False,
        show_logo=True,
        text_color="#C4A35A",
        background_opacity=0.6
    )
}


@dataclass
class CompositionResult:
    """Result of video composition."""
    project_id: str
    asset_id: str
    scene_name: str
    output_path: str
    output_hash: str
    composition_ms: float
    composed_at: str
    overlays_applied: List[str]
    success: bool
    error: Optional[str] = None


def get_overlay_position_coords(position: str, video_width: int, video_height: int,
                                 overlay_width: int = 200, overlay_height: int = 80) -> tuple:
    """Calculate x,y coordinates for overlay position."""
    margin = 20

    positions = {
        "top-left": (margin, margin),
        "top-right": (video_width - overlay_width - margin, margin),
        "bottom-left": (margin, video_height - overlay_height - margin),
        "bottom-right": (video_width - overlay_width - margin, video_height - overlay_height - margin),
        "center": ((video_width - overlay_width) // 2, (video_height - overlay_height) // 2)
    }

    return positions.get(position, positions["bottom-right"])


def hex_to_ffmpeg_color(hex_color: str) -> str:
    """Convert hex color to FFmpeg format."""
    # Remove # if present
    hex_color = hex_color.lstrip('#')
    # FFmpeg uses format like 0xRRGGBB or color names
    return f"0x{hex_color}"


def escape_ffmpeg_text(text: str) -> str:
    """
    Escape text for FFmpeg drawtext filter.

    FFmpeg drawtext uses : as option separator, so colons in text must be escaped.
    Also escapes other special characters.
    """
    # Escape backslashes first
    text = text.replace('\\', '\\\\')
    # Escape colons (FFmpeg option separator)
    text = text.replace(':', '\\:')
    # Escape single quotes
    text = text.replace("'", "\\'")
    return text


async def generate_qr_overlay(
    receipt_id: str,
    verify_url: str,
    output_path: Path,
    size: int = 150
) -> bool:
    """
    Generate QR code overlay image.

    Uses Python qrcode library if available, otherwise creates placeholder.
    """
    try:
        import qrcode
        from qrcode.image.pure import PyPNGImage

        qr = qrcode.QRCode(version=1, box_size=10, border=2)
        qr.add_data(verify_url)
        qr.make(fit=True)

        img = qr.make_image(fill_color="white", back_color="transparent")
        img.save(str(output_path))
        return True

    except ImportError:
        log.warning("qrcode library not available, creating placeholder")
        # Create a simple placeholder using FFmpeg
        cmd = [
            "ffmpeg", "-y",
            "-f", "lavfi",
            "-i", f"color=c=white:s={size}x{size}:d=1",
            "-vframes", "1",
            str(output_path)
        ]
        result = subprocess.run(cmd, capture_output=True, timeout=10)
        return result.returncode == 0

    except Exception as e:
        log.error(f"QR generation failed: {e}")
        return False


def build_filter_complex(
    scene: SceneTemplate,
    video_width: int,
    video_height: int,
    receipt_id: str,
    verdict: str,
    timestamp: str,
    qr_path: Optional[Path] = None
) -> str:
    """
    Build FFmpeg filter_complex string for composition.

    Creates a layered composition with:
    - Base video
    - Semi-transparent background box
    - Text overlays (timestamp, verdict, receipt)
    - QR code overlay (if enabled)
    - Logo overlay (if enabled)
    """
    filters = []
    overlay_applied = []

    # Get position coordinates
    x, y = get_overlay_position_coords(
        scene.overlay_position,
        video_width, video_height,
        overlay_width=300, overlay_height=100
    )

    # Color conversion
    text_color = hex_to_ffmpeg_color(scene.text_color)

    # Start with input video
    current_stream = "[0:v]"

    # Add semi-transparent background box if we have overlays
    if scene.show_timestamp or scene.show_verdict or scene.show_qr:
        bg_alpha = scene.background_opacity
        # Draw rectangle for text background
        filters.append(
            f"{current_stream}drawbox=x={x-10}:y={y-10}:w=320:h=120:"
            f"color=black@{bg_alpha}:t=fill[bg]"
        )
        current_stream = "[bg]"
        overlay_applied.append("background_box")

    # Add timestamp text
    if scene.show_timestamp:
        ts_escaped = escape_ffmpeg_text(timestamp)
        filters.append(
            f"{current_stream}drawtext="
            f"text='{ts_escaped}':"
            f"fontcolor={text_color}:"
            f"fontsize=16:"
            f"x={x}:y={y}:"
            f"font=monospace[ts]"
        )
        current_stream = "[ts]"
        overlay_applied.append("timestamp")

    # Add verdict badge
    if scene.show_verdict:
        verdict_y = y + 25 if scene.show_timestamp else y
        verdict_color = "0x6DBF80" if "AUTHENTIC" in verdict else "0xFFCC00" if "REVIEW" in verdict else "0xFF4444"
        verdict_escaped = escape_ffmpeg_text(verdict)
        filters.append(
            f"{current_stream}drawtext="
            f"text='{verdict_escaped}':"
            f"fontcolor={verdict_color}:"
            f"fontsize=14:"
            f"x={x}:y={verdict_y}:"
            f"font=monospace[vd]"
        )
        current_stream = "[vd]"
        overlay_applied.append("verdict")

    # Add receipt ID
    receipt_y = y + 50 if scene.show_timestamp else y + 25
    if scene.show_verdict:
        receipt_y += 25
    receipt_text = f"ID: {receipt_id[:20]}..."
    receipt_escaped = escape_ffmpeg_text(receipt_text)
    filters.append(
        f"{current_stream}drawtext="
        f"text='{receipt_escaped}':"
        f"fontcolor={text_color}@0.8:"
        f"fontsize=12:"
        f"x={x}:y={receipt_y}:"
        f"font=monospace[rid]"
    )
    current_stream = "[rid]"
    overlay_applied.append("receipt_id")

    # Add QR overlay if enabled and available
    if scene.show_qr and qr_path and qr_path.exists():
        qr_x = x + 220  # Position QR to the right of text
        qr_y = y
        # Scale QR and overlay
        filters.append(f"[1:v]scale=80:80[qr]")
        filters.append(f"{current_stream}[qr]overlay={qr_x}:{qr_y}[qrov]")
        current_stream = "[qrov]"
        overlay_applied.append("qr_code")

    # Add WINDI watermark/logo if enabled
    if scene.show_logo:
        logo_text = escape_ffmpeg_text("WINDI VERIFIED")
        logo_y = video_height - 30
        filters.append(
            f"{current_stream}drawtext="
            f"text='{logo_text}':"
            f"fontcolor={text_color}@0.5:"
            f"fontsize=12:"
            f"x=10:y={logo_y}:"
            f"font=monospace[logo]"
        )
        current_stream = "[logo]"
        overlay_applied.append("logo")

    # Build final filter string
    # If we used QR (input 1), we need different syntax
    if scene.show_qr and qr_path:
        filter_string = ";".join(filters)
    else:
        filter_string = ";".join(filters)

    return filter_string, current_stream, overlay_applied


async def compose_video(
    input_path: Path,
    output_path: Path,
    scene_name: str,
    receipt_id: str,
    verdict: str,
    verify_url: str,
    project_id: str,
    asset_id: str
) -> CompositionResult:
    """
    Compose video with sovereign overlays.

    Applies scene template to create broadcast-ready output
    with verification elements embedded.
    """
    start_time = datetime.now(timezone.utc)
    timestamp = start_time.strftime("%Y-%m-%d %H:%M UTC")

    # Get scene template
    scene = SCENES.get(scene_name, SCENES["clean"])

    # Probe video dimensions
    try:
        probe_cmd = [
            "ffprobe", "-v", "quiet",
            "-select_streams", "v:0",
            "-show_entries", "stream=width,height",
            "-of", "json",
            str(input_path)
        ]
        result = subprocess.run(probe_cmd, capture_output=True, timeout=10)
        probe_data = json.loads(result.stdout.decode())
        streams = probe_data.get("streams", [{}])
        video_width = streams[0].get("width", 1920)
        video_height = streams[0].get("height", 1080)
    except Exception as e:
        log.warning(f"Probe failed, using defaults: {e}")
        video_width, video_height = 1920, 1080

    # Generate QR code if needed
    qr_path = None
    if scene.show_qr:
        qr_path = TEMP_DIR / f"{asset_id}_qr.png"
        await generate_qr_overlay(receipt_id, verify_url, qr_path)

    # Build filter complex
    filter_string, output_stream, overlays_applied = build_filter_complex(
        scene=scene,
        video_width=video_width,
        video_height=video_height,
        receipt_id=receipt_id,
        verdict=verdict,
        timestamp=timestamp,
        qr_path=qr_path
    )

    # Build FFmpeg command
    cmd = ["ffmpeg", "-y", "-i", str(input_path)]

    # Add QR as second input if needed
    if scene.show_qr and qr_path and qr_path.exists():
        cmd.extend(["-i", str(qr_path)])

    # Add filter complex
    cmd.extend([
        "-filter_complex", filter_string,
        "-map", output_stream,
        "-map", "0:a?",  # Copy audio if present
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "23",
        "-c:a", "aac",
        "-b:a", "128k",
        str(output_path)
    ])

    try:
        log.info(f"Composing video with scene '{scene_name}'")
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=300)

        if proc.returncode != 0:
            error_msg = stderr.decode()[:500]
            log.error(f"Composition failed: {error_msg}")
            return CompositionResult(
                project_id=project_id,
                asset_id=asset_id,
                scene_name=scene_name,
                output_path="",
                output_hash="",
                composition_ms=0,
                composed_at=start_time.isoformat(),
                overlays_applied=[],
                success=False,
                error=error_msg
            )

        # Compute output hash
        output_hash = ""
        if output_path.exists():
            sha256 = hashlib.sha256()
            with open(output_path, "rb") as f:
                for chunk in iter(lambda: f.read(65536), b""):
                    sha256.update(chunk)
            output_hash = f"sha256:{sha256.hexdigest()}"

        # Calculate composition time
        end_time = datetime.now(timezone.utc)
        composition_ms = (end_time - start_time).total_seconds() * 1000

        # Cleanup temp files
        if qr_path and qr_path.exists():
            qr_path.unlink(missing_ok=True)

        log.info(f"Composition complete: {scene_name}, {len(overlays_applied)} overlays, {composition_ms:.0f}ms")

        return CompositionResult(
            project_id=project_id,
            asset_id=asset_id,
            scene_name=scene_name,
            output_path=str(output_path),
            output_hash=output_hash,
            composition_ms=round(composition_ms, 2),
            composed_at=start_time.isoformat(),
            overlays_applied=overlays_applied,
            success=True
        )

    except asyncio.TimeoutError:
        return CompositionResult(
            project_id=project_id,
            asset_id=asset_id,
            scene_name=scene_name,
            output_path="",
            output_hash="",
            composition_ms=0,
            composed_at=start_time.isoformat(),
            overlays_applied=[],
            success=False,
            error="Composition timeout (5 min limit)"
        )
    except Exception as e:
        log.error(f"Composition error: {e}")
        return CompositionResult(
            project_id=project_id,
            asset_id=asset_id,
            scene_name=scene_name,
            output_path="",
            output_hash="",
            composition_ms=0,
            composed_at=start_time.isoformat(),
            overlays_applied=[],
            success=False,
            error=str(e)
        )


def list_available_scenes() -> List[Dict[str, Any]]:
    """Return list of available scene templates."""
    return [
        {
            "id": scene_id,
            "name": scene.name,
            "description": scene.description,
            "features": {
                "timestamp": scene.show_timestamp,
                "qr_code": scene.show_qr,
                "verdict_badge": scene.show_verdict,
                "logo": scene.show_logo
            }
        }
        for scene_id, scene in SCENES.items()
    ]
