"""
W-VD-CUT-001 — Transcribe Service
Speech-to-text with synchronized timestamps using OpenAI Whisper

Enables:
- Cut by text selection → timestamp → FFmpeg cut
- Legal subtitle generation
- Searchable video archives

Liga IA+H · Kempten, Bavaria · 2026
"AI processes. Human decides. WINDI guarantees."
"""

import os
import json
import asyncio
import logging
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone

log = logging.getLogger("w-vd-cut-001.transcribe")

# Whisper model cache (lazy load)
_model_cache = {}

# Model tiers - balancing speed vs accuracy
MODELS = {
    "tiny": {"size": "39M", "speed": "~32x realtime", "accuracy": "basic"},
    "base": {"size": "74M", "speed": "~16x realtime", "accuracy": "good"},
    "small": {"size": "244M", "speed": "~6x realtime", "accuracy": "better"},
    "medium": {"size": "769M", "speed": "~2x realtime", "accuracy": "high"},
}

# Default model - balance of speed and accuracy
DEFAULT_MODEL = "base"


def get_model(model_name: str = DEFAULT_MODEL):
    """
    Get or load Whisper model (cached).

    First call downloads the model if not present.
    Subsequent calls use cached instance.
    """
    global _model_cache

    if model_name not in MODELS:
        log.warning(f"Unknown model {model_name}, using {DEFAULT_MODEL}")
        model_name = DEFAULT_MODEL

    if model_name not in _model_cache:
        log.info(f"Loading Whisper model: {model_name}")
        import whisper
        _model_cache[model_name] = whisper.load_model(model_name)
        log.info(f"Whisper model {model_name} loaded")

    return _model_cache[model_name]


async def transcribe_video(
    video_path: Path,
    model_name: str = DEFAULT_MODEL,
    language: Optional[str] = None
) -> Dict[str, Any]:
    """
    Transcribe video audio with word-level timestamps.

    Args:
        video_path: Path to video file
        model_name: Whisper model to use (tiny/base/small/medium)
        language: Force specific language (None = auto-detect)

    Returns:
        {
            "text": "Full transcription text",
            "language": "detected_language",
            "segments": [
                {
                    "id": 0,
                    "start": 0.0,
                    "end": 2.5,
                    "text": "Segment text",
                    "words": [
                        {"word": "Hello", "start": 0.0, "end": 0.5},
                        ...
                    ]
                }
            ],
            "duration_seconds": 120.5,
            "model_used": "base",
            "transcribed_at": "2026-04-05T..."
        }
    """
    if not video_path.exists():
        return {"error": True, "message": f"File not found: {video_path}"}

    log.info(f"Transcribing: {video_path.name} with model {model_name}")

    try:
        # Run in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            _sync_transcribe,
            str(video_path),
            model_name,
            language
        )
        return result

    except Exception as e:
        log.error(f"Transcription failed: {e}")
        return {"error": True, "message": str(e)}


def _sync_transcribe(
    video_path: str,
    model_name: str,
    language: Optional[str]
) -> Dict[str, Any]:
    """
    Synchronous transcription (called from executor).
    """
    import whisper

    model = get_model(model_name)

    # Transcribe with word timestamps
    result = model.transcribe(
        video_path,
        language=language,
        word_timestamps=True,
        verbose=False
    )

    # Build structured response
    segments = []
    for seg in result.get("segments", []):
        segment_data = {
            "id": seg.get("id", 0),
            "start": round(seg.get("start", 0), 3),
            "end": round(seg.get("end", 0), 3),
            "text": seg.get("text", "").strip()
        }

        # Word-level timestamps if available
        if "words" in seg:
            segment_data["words"] = [
                {
                    "word": w.get("word", "").strip(),
                    "start": round(w.get("start", 0), 3),
                    "end": round(w.get("end", 0), 3)
                }
                for w in seg["words"]
            ]

        segments.append(segment_data)

    # Calculate duration from last segment
    duration = 0
    if segments:
        duration = segments[-1]["end"]

    return {
        "text": result.get("text", "").strip(),
        "language": result.get("language", "unknown"),
        "segments": segments,
        "duration_seconds": round(duration, 3),
        "model_used": model_name,
        "transcribed_at": datetime.now(timezone.utc).isoformat()
    }


def text_to_cuts(
    transcription: Dict[str, Any],
    selected_text: str
) -> List[Dict[str, Any]]:
    """
    Find timestamps for selected text in transcription.

    Used for "cut by text" feature:
    1. User sees transcription
    2. User selects text portion
    3. This function finds corresponding timestamps
    4. FFmpeg cuts at those timestamps

    Args:
        transcription: Result from transcribe_video()
        selected_text: Text user wants to cut

    Returns:
        List of {start, end, text} for matching segments
    """
    if "error" in transcription:
        return []

    matches = []
    selected_lower = selected_text.lower().strip()

    # Search in segments
    for seg in transcription.get("segments", []):
        seg_text = seg.get("text", "").lower()

        if selected_lower in seg_text:
            matches.append({
                "start": seg["start"],
                "end": seg["end"],
                "text": seg["text"],
                "segment_id": seg["id"]
            })

    # If no segment match, try word-level matching
    if not matches:
        words_selected = selected_lower.split()
        if len(words_selected) >= 2:
            # Find word sequence
            for seg in transcription.get("segments", []):
                words = seg.get("words", [])
                for i in range(len(words) - len(words_selected) + 1):
                    window = [w["word"].lower().strip() for w in words[i:i+len(words_selected)]]
                    if window == words_selected:
                        matches.append({
                            "start": words[i]["start"],
                            "end": words[i+len(words_selected)-1]["end"],
                            "text": " ".join(w["word"] for w in words[i:i+len(words_selected)]),
                            "segment_id": seg["id"],
                            "word_match": True
                        })

    return matches


def generate_srt(
    transcription: Dict[str, Any],
    output_path: Optional[Path] = None
) -> str:
    """
    Generate SRT subtitle file from transcription.

    Args:
        transcription: Result from transcribe_video()
        output_path: Optional path to write .srt file

    Returns:
        SRT content as string
    """
    if "error" in transcription:
        return ""

    lines = []
    for i, seg in enumerate(transcription.get("segments", []), 1):
        start = _format_srt_time(seg["start"])
        end = _format_srt_time(seg["end"])
        text = seg["text"]

        lines.append(f"{i}")
        lines.append(f"{start} --> {end}")
        lines.append(text)
        lines.append("")

    srt_content = "\n".join(lines)

    if output_path:
        output_path.write_text(srt_content, encoding="utf-8")
        log.info(f"SRT written: {output_path}")

    return srt_content


def _format_srt_time(seconds: float) -> str:
    """Format seconds as SRT timestamp: HH:MM:SS,mmm"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


# ----- Legal Overlay (Watermark) -----

def _escape_drawtext(text: str) -> str:
    """
    Escape text for FFmpeg drawtext filter.

    FFmpeg drawtext requires special escaping for:
    - : (colon) → \\:
    - ' (quote) → \\'
    - \\ (backslash) → \\\\
    """
    # Order matters: escape backslashes first
    text = text.replace("\\", "\\\\")
    text = text.replace(":", "\\:")
    text = text.replace("'", "\\'")
    return text


async def add_legal_overlay(
    input_path: Path,
    output_path: Path,
    case_ref: str,
    court: Optional[str] = None,
    timestamp: Optional[str] = None
) -> Dict[str, Any]:
    """
    Add legal watermark overlay to video.

    Args:
        input_path: Source video
        output_path: Output video with overlay
        case_ref: Case reference number (e.g., "123/2026")
        court: Optional court name
        timestamp: Optional timestamp text

    Returns:
        {status, output_path, overlay_text}
    """
    if not input_path.exists():
        return {"error": True, "message": "Input file not found"}

    # Build overlay text
    overlay_lines = [f"Ref\\: {case_ref}"]
    if court:
        overlay_lines.append(court)
    if timestamp:
        overlay_lines.append(timestamp)
    else:
        overlay_lines.append(datetime.now(timezone.utc).strftime("%Y-%m-%d %H\\:%M UTC"))

    overlay_text = " | ".join(overlay_lines)

    # Escape special characters for drawtext
    escaped_text = _escape_drawtext(overlay_text)

    # FFmpeg drawtext filter
    # Semi-transparent background, white text, bottom-left position
    filter_complex = (
        f"drawtext=text='{escaped_text}':"
        f"fontsize=14:"
        f"fontcolor=white:"
        f"x=10:y=h-th-10:"
        f"box=1:boxcolor=black@0.5:boxborderw=5"
    )

    cmd = [
        "ffmpeg", "-y",
        "-i", str(input_path),
        "-vf", filter_complex,
        "-c:a", "copy",
        str(output_path)
    ]

    log.info(f"Adding legal overlay: {case_ref}")

    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()

        if proc.returncode != 0:
            return {
                "error": True,
                "message": f"FFmpeg failed: {stderr.decode()[-500:]}"
            }

        return {
            "status": "ok",
            "output_path": str(output_path),
            "overlay_text": overlay_text
        }

    except Exception as e:
        log.error(f"Legal overlay failed: {e}")
        return {"error": True, "message": str(e)}
