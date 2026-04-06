"""
W-CLASSIFY-001 — Sensibility Layer
Intelligent content classification for module routing

Liga IA+H · Kempten, Bavaria · 2026
"AI processes. Human decides. WINDI guarantees."

This service analyzes incoming media files and suggests
appropriate processing modules WITHOUT making autonomous
decisions. I9 Gate remains the final human checkpoint.
"""

import json
import asyncio
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime, timezone

log = logging.getLogger("w-vd-cut-001.classify")


@dataclass
class ModuleSuggestion:
    """A suggested processing module with rationale."""
    target: str           # Module ID (e.g., "W-WHISPER", "W-VISION-FRAME")
    action: str           # Endpoint to call (e.g., "/transcribe")
    reason: str           # Human-readable explanation
    confidence: float     # 0.0 to 1.0
    priority: int         # Lower = higher priority


@dataclass
class ClassificationResult:
    """Result of content classification."""
    project_id: str
    asset_id: str
    analysis_ms: float                     # Time taken for analysis
    analyzed_at: str                       # ISO timestamp
    recommendations: List[Dict[str, Any]]  # Module suggestions
    metadata_summary: Dict[str, Any]       # Key metadata extracted
    can_proceed_to_seal: bool              # Always True (modules are optional)
    sensibility_version: str = "1.0.0"


async def probe_extended(file_path: Path) -> Dict[str, Any]:
    """
    Extended ffprobe that extracts all streams and encoder metadata.
    Returns detailed info for classification heuristics.
    """
    if not file_path.exists():
        return {"error": True, "message": "File not found"}

    try:
        cmd = [
            "ffprobe",
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            str(file_path)
        ]

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=30)

        if proc.returncode != 0:
            return {"error": True, "message": f"FFprobe failed: {stderr.decode()[:200]}"}

        data = json.loads(stdout.decode())

        # Extract all streams
        video_stream = None
        audio_stream = None

        for stream in data.get("streams", []):
            if stream.get("codec_type") == "video" and not video_stream:
                video_stream = stream
            elif stream.get("codec_type") == "audio" and not audio_stream:
                audio_stream = stream

        if not video_stream:
            return {"error": True, "message": "No video stream found"}

        # Extract format metadata
        format_info = data.get("format", {})
        tags = format_info.get("tags", {})

        # Calculate FPS
        fps_str = video_stream.get("r_frame_rate", "30/1")
        try:
            num, den = fps_str.split("/")
            fps = float(num) / float(den) if float(den) > 0 else 30.0
        except Exception:
            fps = 30.0

        # Build extended metadata
        result = {
            # Video info
            "duration": float(format_info.get("duration", 0)),
            "width": video_stream.get("width", 0),
            "height": video_stream.get("height", 0),
            "video_codec": video_stream.get("codec_name", "unknown"),
            "fps": fps,
            "bitrate": int(format_info.get("bit_rate", 0)),
            "size_bytes": int(format_info.get("size", 0)),

            # Audio info
            "has_audio": audio_stream is not None,
            "audio_codec": audio_stream.get("codec_name") if audio_stream else None,
            "audio_channels": audio_stream.get("channels", 0) if audio_stream else 0,
            "audio_sample_rate": int(audio_stream.get("sample_rate", 0)) if audio_stream else 0,

            # Encoder metadata (for OBS/vMix detection)
            "encoder": tags.get("encoder", tags.get("ENCODER", "")),
            "creation_time": tags.get("creation_time", ""),
            "handler_name": video_stream.get("tags", {}).get("handler_name", ""),

            # GPS/Location (common in mobile recordings)
            "has_gps": any(k.lower() in ["location", "gps", "com.apple.quicktime.location.iso6709"]
                         for k in tags.keys()),

            # Format name
            "format_name": format_info.get("format_name", ""),

            # Raw tags for advanced analysis
            "raw_tags": tags
        }

        return result

    except asyncio.TimeoutError:
        return {"error": True, "message": "FFprobe timeout"}
    except json.JSONDecodeError as e:
        return {"error": True, "message": f"Invalid probe output: {e}"}
    except Exception as e:
        log.error(f"Extended probe error: {e}")
        return {"error": True, "message": str(e)}


def detect_encoder_origin(metadata: Dict[str, Any]) -> Optional[str]:
    """
    Detect if video came from streaming/production software.
    Returns: "OBS", "vMix", "Streamlabs", "Mobile", "Unknown"
    """
    encoder = metadata.get("encoder", "").lower()
    handler = metadata.get("handler_name", "").lower()
    format_name = metadata.get("format_name", "").lower()

    # OBS Studio detection
    if "obs" in encoder or "obs" in handler:
        return "OBS"

    # vMix detection
    if "vmix" in encoder:
        return "vMix"

    # Streamlabs detection
    if "streamlabs" in encoder:
        return "Streamlabs"

    # Mobile detection (common patterns)
    if any(x in encoder for x in ["apple", "iphone", "android", "samsung", "xiaomi"]):
        return "Mobile"

    # Check creation time format (mobile often has timezone)
    if metadata.get("creation_time") and "+" in metadata.get("creation_time", ""):
        return "Mobile"

    return "Unknown"


def analyze_content(metadata: Dict[str, Any]) -> List[ModuleSuggestion]:
    """
    Apply classification heuristics to generate module suggestions.

    Rules are ordered by relevance and confidence.
    """
    suggestions = []

    # --- Rule 1: Audio Detection → Whisper ---
    if metadata.get("has_audio"):
        duration = metadata.get("duration", 0)

        if duration >= 5:  # At least 5 seconds of potential speech
            confidence = min(0.9, 0.5 + (duration / 60) * 0.4)  # Higher for longer videos
            suggestions.append(ModuleSuggestion(
                target="W-WHISPER",
                action="/vd-cut/transcribe",
                reason=f"Audio detectado ({duration:.1f}s). Transcrição pode revelar conteúdo verbal.",
                confidence=confidence,
                priority=1
            ))

    # --- Rule 2: Live/Production Origin → OBS Gate ---
    encoder_origin = detect_encoder_origin(metadata)

    if encoder_origin in ["OBS", "vMix", "Streamlabs"]:
        suggestions.append(ModuleSuggestion(
            target="W-OBS-GATE",
            action="/vd-cut/joe/render",
            reason=f"Origem de produção detectada ({encoder_origin}). Composição estética disponível.",
            confidence=0.75,
            priority=2
        ))

    # --- Rule 3: High Resolution → Mass Optimization ---
    width = metadata.get("width", 0)
    height = metadata.get("height", 0)
    resolution = max(width, height)

    if resolution > 2160:  # 4K+
        size_mb = metadata.get("size_bytes", 0) / (1024 * 1024)
        suggestions.append(ModuleSuggestion(
            target="W-VD-MASS-001",
            action="/vd-mass/batch/submit",
            reason=f"Resolução alta ({width}x{height}, {size_mb:.1f}MB). Optimização para distribuição recomendada.",
            confidence=0.7,
            priority=3
        ))

    # --- Rule 4: Missing Metadata → Forensic Description ---
    has_gps = metadata.get("has_gps", False)
    creation_time = metadata.get("creation_time", "")

    if not has_gps and not creation_time:
        suggestions.append(ModuleSuggestion(
            target="W-VISION-001",
            action="/vd-cut/describe",  # Future endpoint
            reason="Metadados de origem ausentes. Descrição forense pode enriquecer contexto.",
            confidence=0.6,
            priority=4
        ))

    # --- Rule 5: Frame Integrity (always suggested for critical content) ---
    # This is a lighter suggestion, always available
    if metadata.get("duration", 0) > 0:
        suggestions.append(ModuleSuggestion(
            target="W-FRAME-INTEGRITY",
            action="/vd-cut/seal-edit-frames",
            reason="Análise de integridade de frames disponível para prova forense.",
            confidence=0.5,
            priority=5
        ))

    # Sort by priority
    suggestions.sort(key=lambda x: x.priority)

    return suggestions


async def classify_content(
    file_path: Path,
    project_id: str,
    asset_id: str
) -> ClassificationResult:
    """
    Main classification function.

    Analyzes file and returns module suggestions.
    Never blocks the upload pipeline - if analysis fails,
    returns empty suggestions and allows direct seal.
    """
    start_time = datetime.now(timezone.utc)

    try:
        # Extended probe
        metadata = await probe_extended(file_path)

        if metadata.get("error"):
            # Analysis failed - allow direct seal
            log.warning(f"Classification probe failed for {asset_id}: {metadata.get('message')}")
            return ClassificationResult(
                project_id=project_id,
                asset_id=asset_id,
                analysis_ms=0,
                analyzed_at=start_time.isoformat(),
                recommendations=[],
                metadata_summary={"error": metadata.get("message")},
                can_proceed_to_seal=True  # Never block
            )

        # Generate suggestions
        suggestions = analyze_content(metadata)

        # Calculate analysis time
        end_time = datetime.now(timezone.utc)
        analysis_ms = (end_time - start_time).total_seconds() * 1000

        # Build metadata summary (safe subset)
        metadata_summary = {
            "duration": metadata.get("duration"),
            "resolution": f"{metadata.get('width')}x{metadata.get('height')}",
            "has_audio": metadata.get("has_audio"),
            "encoder_origin": detect_encoder_origin(metadata),
            "has_gps": metadata.get("has_gps"),
            "size_mb": round(metadata.get("size_bytes", 0) / (1024 * 1024), 2)
        }

        log.info(f"Classified {asset_id}: {len(suggestions)} suggestions in {analysis_ms:.1f}ms")

        return ClassificationResult(
            project_id=project_id,
            asset_id=asset_id,
            analysis_ms=round(analysis_ms, 2),
            analyzed_at=start_time.isoformat(),
            recommendations=[asdict(s) for s in suggestions],
            metadata_summary=metadata_summary,
            can_proceed_to_seal=True  # Always true - modules are optional
        )

    except Exception as e:
        log.error(f"Classification error for {asset_id}: {e}")

        # Never block on error
        return ClassificationResult(
            project_id=project_id,
            asset_id=asset_id,
            analysis_ms=0,
            analyzed_at=start_time.isoformat(),
            recommendations=[],
            metadata_summary={"error": str(e)},
            can_proceed_to_seal=True
        )
