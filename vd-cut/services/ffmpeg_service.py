"""
W-VD-CUT-001 — FFmpeg Service
Video processing commands and presets

Liga IA+H · Kempten, Bavaria · 2026
"""

import os
import json
import asyncio
import logging
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional, List

log = logging.getLogger("w-vd-cut-001.ffmpeg")

# FFmpeg presets for different output types
PRESETS = {
    "story_clean": {
        "description": "Full quality vertical story",
        "resolution": "1080x1920",
        "crf": 23,
        "preset": "medium",
        "audio_bitrate": "128k"
    },
    "story_light": {
        "description": "Fast/lightweight vertical",
        "resolution": "720x1280",
        "crf": 26,
        "preset": "fast",
        "audio_bitrate": "96k"
    },
    "bts": {
        "description": "Behind the scenes",
        "resolution": "720x1280",
        "crf": 28,
        "preset": "faster",
        "audio_bitrate": "96k"
    }
}


def check_ffmpeg() -> bool:
    """Check if FFmpeg is available."""
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True,
            timeout=5
        )
        return result.returncode == 0
    except Exception:
        return False


async def probe_video(file_path: Path) -> Dict[str, Any]:
    """
    Probe video file using FFprobe.
    Returns metadata: duration, width, height, codec, fps.
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
            return {
                "error": True,
                "message": f"FFprobe failed: {stderr.decode()[:200]}"
            }

        data = json.loads(stdout.decode())

        # Find video stream
        video_stream = None
        for stream in data.get("streams", []):
            if stream.get("codec_type") == "video":
                video_stream = stream
                break

        if not video_stream:
            return {"error": True, "message": "No video stream found"}

        # Extract metadata
        duration = float(data.get("format", {}).get("duration", 0))
        width = video_stream.get("width", 0)
        height = video_stream.get("height", 0)
        codec = video_stream.get("codec_name", "unknown")

        # Calculate FPS from frame rate
        fps_str = video_stream.get("r_frame_rate", "30/1")
        try:
            num, den = fps_str.split("/")
            fps = float(num) / float(den) if float(den) > 0 else 30.0
        except Exception:
            fps = 30.0

        return {
            "duration": duration,
            "width": width,
            "height": height,
            "codec": codec,
            "fps": fps,
            "bitrate": int(data.get("format", {}).get("bit_rate", 0)),
            "size": int(data.get("format", {}).get("size", 0))
        }

    except asyncio.TimeoutError:
        return {"error": True, "message": "FFprobe timeout"}
    except json.JSONDecodeError as e:
        return {"error": True, "message": f"Invalid probe output: {e}"}
    except Exception as e:
        log.error(f"Probe error: {e}")
        return {"error": True, "message": str(e)}


async def encode_video(
    input_path: Path,
    output_path: Path,
    edl: List[Dict[str, float]],
    preset_name: str = "story_clean",
    progress_callback: Optional[callable] = None
) -> Dict[str, Any]:
    """
    Encode video according to EDL (Edit Decision List).

    Args:
        input_path: Source video file
        output_path: Output file path
        edl: List of segments [{in: float, out: float}, ...]
        preset_name: Preset to use (story_clean, story_light, bts)
        progress_callback: Optional async callback(percent: int)

    Returns:
        Result dict with success/error
    """
    if not input_path.exists():
        return {"error": True, "message": "Input file not found"}

    preset = PRESETS.get(preset_name, PRESETS["story_clean"])

    try:
        # Probe input for duration
        probe = await probe_video(input_path)
        if probe.get("error"):
            return probe

        total_duration = probe["duration"]

        # Build filter complex for segment extraction
        if len(edl) == 1:
            # Single segment - use simple trim
            seg = edl[0]
            start = seg.get("in", 0)
            end = seg.get("out", total_duration)
            duration = end - start

            cmd = [
                "ffmpeg", "-y",
                "-ss", str(start),
                "-i", str(input_path),
                "-t", str(duration),
                "-c:v", "libx264",
                "-preset", preset["preset"],
                "-crf", str(preset["crf"]),
                "-c:a", "aac",
                "-b:a", preset["audio_bitrate"],
                "-movflags", "+faststart",
                "-progress", "pipe:1",
                str(output_path)
            ]
        else:
            # Multiple segments - use filter_complex with concat
            filter_parts = []
            concat_inputs = []

            for i, seg in enumerate(edl):
                start = seg.get("in", 0)
                end = seg.get("out", total_duration)
                duration = end - start

                # Trim each segment
                filter_parts.append(
                    f"[0:v]trim=start={start}:end={end},setpts=PTS-STARTPTS[v{i}]"
                )
                filter_parts.append(
                    f"[0:a]atrim=start={start}:end={end},asetpts=PTS-STARTPTS[a{i}]"
                )
                concat_inputs.append(f"[v{i}][a{i}]")

            # Concat all segments
            filter_parts.append(
                f"{''.join(concat_inputs)}concat=n={len(edl)}:v=1:a=1[outv][outa]"
            )

            filter_complex = ";".join(filter_parts)

            cmd = [
                "ffmpeg", "-y",
                "-i", str(input_path),
                "-filter_complex", filter_complex,
                "-map", "[outv]",
                "-map", "[outa]",
                "-c:v", "libx264",
                "-preset", preset["preset"],
                "-crf", str(preset["crf"]),
                "-c:a", "aac",
                "-b:a", preset["audio_bitrate"],
                "-movflags", "+faststart",
                "-progress", "pipe:1",
                str(output_path)
            ]

        log.info(f"Encoding: {input_path.name} -> {output_path.name}")
        log.debug(f"FFmpeg command: {' '.join(cmd)}")

        # Run FFmpeg
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        # Calculate expected output duration
        expected_duration = sum(
            (seg.get("out", total_duration) - seg.get("in", 0))
            for seg in edl
        )

        # Monitor progress
        last_progress = 0
        while True:
            line = await proc.stdout.readline()
            if not line:
                break

            line = line.decode().strip()
            if line.startswith("out_time_ms="):
                try:
                    out_time_ms = int(line.split("=")[1])
                    out_time_sec = out_time_ms / 1000000.0
                    progress = min(99, int((out_time_sec / expected_duration) * 100))

                    if progress > last_progress and progress_callback:
                        await progress_callback(progress)
                        last_progress = progress
                except Exception:
                    pass

        await proc.wait()

        if proc.returncode != 0:
            stderr = await proc.stderr.read()
            return {
                "error": True,
                "message": f"FFmpeg failed: {stderr.decode()[:500]}"
            }

        # Verify output exists
        if not output_path.exists():
            return {"error": True, "message": "Output file not created"}

        # Probe output
        output_probe = await probe_video(output_path)
        if output_probe.get("error"):
            return output_probe

        log.info(f"Encoding complete: {output_path.name}, duration={output_probe['duration']:.1f}s")

        return {
            "success": True,
            "output_path": str(output_path),
            "duration": output_probe["duration"],
            "width": output_probe["width"],
            "height": output_probe["height"],
            "file_size": output_path.stat().st_size
        }

    except asyncio.TimeoutError:
        return {"error": True, "message": "Encoding timeout"}
    except Exception as e:
        log.error(f"Encoding error: {e}")
        return {"error": True, "message": str(e)}


async def generate_thumbnail(
    video_path: Path,
    output_path: Path,
    timestamp: float = 1.0,
    size: str = "320x568"
) -> Dict[str, Any]:
    """
    Generate thumbnail from video.

    Args:
        video_path: Source video
        output_path: Output JPEG path
        timestamp: Time in seconds for thumbnail
        size: Output dimensions (default 320x568 for 9:16)
    """
    if not video_path.exists():
        return {"error": True, "message": "Video not found"}

    try:
        cmd = [
            "ffmpeg", "-y",
            "-ss", str(timestamp),
            "-i", str(video_path),
            "-vframes", "1",
            "-s", size,
            "-f", "image2",
            str(output_path)
        ]

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        _, stderr = await asyncio.wait_for(proc.communicate(), timeout=30)

        if proc.returncode != 0:
            return {
                "error": True,
                "message": f"Thumbnail generation failed: {stderr.decode()[:200]}"
            }

        if not output_path.exists():
            return {"error": True, "message": "Thumbnail not created"}

        return {
            "success": True,
            "path": str(output_path),
            "size": output_path.stat().st_size
        }

    except asyncio.TimeoutError:
        return {"error": True, "message": "Thumbnail timeout"}
    except Exception as e:
        log.error(f"Thumbnail error: {e}")
        return {"error": True, "message": str(e)}


async def generate_preview(
    video_path: Path,
    output_path: Path,
    timestamp: float = 1.0
) -> Dict[str, Any]:
    """
    Generate full-size preview frame from video.

    Unlike thumbnail, this preserves original resolution.
    Used for detailed preview in dashboard.

    Args:
        video_path: Source video
        output_path: Output JPEG path
        timestamp: Time in seconds for frame extraction
    """
    if not video_path.exists():
        return {"error": True, "message": "Video not found"}

    try:
        # Extract frame at original resolution (no -s flag)
        cmd = [
            "ffmpeg", "-y",
            "-ss", str(timestamp),
            "-i", str(video_path),
            "-vframes", "1",
            "-q:v", "2",  # High quality JPEG
            "-f", "image2",
            str(output_path)
        ]

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        _, stderr = await asyncio.wait_for(proc.communicate(), timeout=30)

        if proc.returncode != 0:
            return {
                "error": True,
                "message": f"Preview generation failed: {stderr.decode()[:200]}"
            }

        if not output_path.exists():
            return {"error": True, "message": "Preview not created"}

        return {
            "success": True,
            "path": str(output_path),
            "size": output_path.stat().st_size
        }

    except asyncio.TimeoutError:
        return {"error": True, "message": "Preview timeout"}
    except Exception as e:
        log.error(f"Preview error: {e}")
        return {"error": True, "message": str(e)}


async def normalize_audio(
    input_path: Path,
    output_path: Path,
    target_loudness: float = -16.0
) -> Dict[str, Any]:
    """
    Normalize audio loudness using FFmpeg loudnorm filter.
    Optional post-processing step.
    """
    try:
        # Two-pass loudness normalization
        # First pass: analyze
        cmd_analyze = [
            "ffmpeg",
            "-i", str(input_path),
            "-af", f"loudnorm=I={target_loudness}:print_format=json",
            "-f", "null",
            "-"
        ]

        proc = await asyncio.create_subprocess_exec(
            *cmd_analyze,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        _, stderr = await asyncio.wait_for(proc.communicate(), timeout=60)

        # For now, just use single-pass normalization
        cmd_normalize = [
            "ffmpeg", "-y",
            "-i", str(input_path),
            "-af", f"loudnorm=I={target_loudness}",
            "-c:v", "copy",
            "-c:a", "aac",
            "-b:a", "128k",
            str(output_path)
        ]

        proc = await asyncio.create_subprocess_exec(
            *cmd_normalize,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        await asyncio.wait_for(proc.communicate(), timeout=120)

        if proc.returncode != 0:
            return {"error": True, "message": "Audio normalization failed"}

        return {"success": True, "path": str(output_path)}

    except Exception as e:
        log.error(f"Audio normalization error: {e}")
        return {"error": True, "message": str(e)}
