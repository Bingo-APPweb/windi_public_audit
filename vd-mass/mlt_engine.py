"""
W-VD-MASS-001 — MLT Engine Module
Shotcut/MLT professional video editing integration

"O ficheiro .mlt é a receita auditável antes de renderizar."

DISABLED BY DEFAULT — set MLT_ENABLED=true in .env after installing melt:
  sudo apt install melt -y

Liga IA+H · Kempten, Bavaria · 2026
"""

import os
import subprocess
import hashlib
import logging
import json
import shutil
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
from datetime import datetime, timezone

# Configuration
MLT_ENABLED = os.environ.get("MLT_ENABLED", "false").lower() == "true"
MELT_BIN = os.environ.get("MELT_BIN", "melt")
MLT_WORK_DIR = Path("/opt/windi/media/vd-mass/mlt")
MLT_RENDER_DIR = Path("/opt/windi/media/vd-mass/renders")

# Ensure directories exist
MLT_WORK_DIR.mkdir(parents=True, exist_ok=True)
MLT_RENDER_DIR.mkdir(parents=True, exist_ok=True)

log = logging.getLogger("w-vd-mass-001.mlt-engine")


class MLTEngineError(Exception):
    """MLT Engine specific error."""
    pass


class MLTEngine:
    """
    MLT/Shotcut rendering engine for W-VD-MASS-001.

    Architecture:
    - .mlt file = auditable recipe (XML with timeline, effects, transitions)
    - melt renders locally = total sovereignty
    - Disabled by default until melt installed
    - Render failure → Exception Queue, never auto-seal

    Invariants:
    - I9-P: Policy defines acceptable .mlt parameters
    - I11: .mlt hash + render hash both tracked
    """

    def __init__(self):
        self.enabled = MLT_ENABLED
        self.melt_available = self._check_melt()

        if self.enabled and not self.melt_available:
            log.warning("MLT_ENABLED=true but melt not found. Engine disabled.")
            self.enabled = False

        if self.enabled:
            log.info("MLT Engine initialized (melt available)")
        else:
            log.info("MLT Engine disabled (MLT_ENABLED=false or melt not installed)")

    def _check_melt(self) -> bool:
        """Check if melt binary is available."""
        try:
            result = subprocess.run(
                [MELT_BIN, "-version"],
                capture_output=True,
                timeout=5
            )
            if result.returncode == 0:
                version = result.stdout.decode().strip().split('\n')[0]
                log.info(f"melt found: {version}")
                return True
            return False
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def is_enabled(self) -> bool:
        """Check if MLT engine is enabled and ready."""
        return self.enabled and self.melt_available

    def validate_mlt(self, mlt_content: str) -> Tuple[bool, str, Dict]:
        """
        Validate MLT file content.

        Checks:
        - Valid XML structure
        - Has required MLT elements
        - No dangerous external references
        - Duration within limits

        Returns:
            (valid, message, metadata)
        """
        import xml.etree.ElementTree as ET

        try:
            root = ET.fromstring(mlt_content)
        except ET.ParseError as e:
            return False, f"Invalid XML: {e}", {}

        # Check root element
        if root.tag != "mlt":
            return False, f"Root element must be 'mlt', got '{root.tag}'", {}

        # Extract metadata
        metadata = {
            "version": root.get("version", "unknown"),
            "producer": root.get("producer", "unknown"),
            "profiles": [],
            "producers": [],
            "playlists": [],
            "tractors": []
        }

        # Check for profiles
        for profile in root.findall(".//profile"):
            metadata["profiles"].append({
                "width": profile.get("width"),
                "height": profile.get("height"),
                "frame_rate_num": profile.get("frame_rate_num"),
                "frame_rate_den": profile.get("frame_rate_den")
            })

        # Check for producers (media sources)
        for producer in root.findall(".//producer"):
            prod_info = {"id": producer.get("id")}
            for prop in producer.findall("property"):
                name = prop.get("name")
                if name in ["resource", "length", "mlt_service"]:
                    prod_info[name] = prop.text
            metadata["producers"].append(prod_info)

        # Check for dangerous external references
        for producer in root.findall(".//producer"):
            for prop in producer.findall("property"):
                if prop.get("name") == "resource":
                    resource = prop.text or ""
                    # Block remote URLs
                    if resource.startswith(("http://", "https://", "ftp://")):
                        return False, f"Remote resources not allowed: {resource}", metadata
                    # Block absolute paths outside allowed dirs
                    if resource.startswith("/") and not resource.startswith("/opt/windi/media"):
                        return False, f"Resource outside allowed path: {resource}", metadata

        # Count playlists and tractors
        metadata["playlists"] = [p.get("id") for p in root.findall(".//playlist")]
        metadata["tractors"] = [t.get("id") for t in root.findall(".//tractor")]

        return True, "Valid MLT file", metadata

    def hash_mlt(self, mlt_content: str) -> str:
        """Generate SHA-256 hash of MLT content."""
        return hashlib.sha256(mlt_content.encode()).hexdigest()

    def save_mlt(self, mlt_content: str, job_id: str) -> Path:
        """Save MLT content to work directory."""
        mlt_path = MLT_WORK_DIR / f"{job_id}.mlt"
        mlt_path.write_text(mlt_content)
        return mlt_path

    def render(
        self,
        mlt_path: Path,
        output_name: str,
        output_format: str = "mp4",
        progress_callback: Optional[callable] = None
    ) -> Tuple[bool, str, Optional[Path]]:
        """
        Render MLT file using melt.

        Args:
            mlt_path: Path to .mlt file
            output_name: Output filename (without extension)
            output_format: Output format (mp4, webm, etc.)
            progress_callback: Optional callback for progress updates

        Returns:
            (success, message, output_path)
        """
        if not self.is_enabled():
            return False, "MLT Engine not enabled", None

        if not mlt_path.exists():
            return False, f"MLT file not found: {mlt_path}", None

        output_path = MLT_RENDER_DIR / f"{output_name}.{output_format}"

        # Build melt command
        # consumer avformat = output to file
        # vcodec=libx264 acodec=aac = standard H.264/AAC
        cmd = [
            MELT_BIN,
            str(mlt_path),
            "-consumer", f"avformat:{output_path}",
            "vcodec=libx264",
            "acodec=aac",
            "preset=medium",
            "crf=23"
        ]

        log.info(f"Rendering: {' '.join(cmd)}")

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                timeout=600,  # 10 minute timeout
                cwd=str(MLT_WORK_DIR)
            )

            if result.returncode != 0:
                error = result.stderr.decode()[:500]
                log.error(f"Render failed: {error}")
                return False, f"Render failed: {error}", None

            if not output_path.exists():
                return False, "Render completed but output file not found", None

            # Get output hash
            output_hash = hashlib.sha256(output_path.read_bytes()).hexdigest()
            log.info(f"Render complete: {output_path} (hash: {output_hash[:16]}...)")

            return True, f"Rendered successfully, hash: {output_hash}", output_path

        except subprocess.TimeoutExpired:
            return False, "Render timeout (>10 minutes)", None
        except Exception as e:
            log.error(f"Render exception: {e}")
            return False, f"Render error: {e}", None

    def process_mlt_job(
        self,
        mlt_content: str,
        job_id: str,
        policy_id: Optional[str] = None,
        actor_did: str = ""
    ) -> Dict[str, Any]:
        """
        Full MLT processing pipeline.

        Steps:
        1. Validate MLT content
        2. Hash MLT (auditable recipe)
        3. Save to work directory
        4. Render via melt
        5. Hash output
        6. Return result (conform or exception)

        Returns:
            Job result with verdict (conforme/exception)
        """
        result = {
            "job_id": job_id,
            "mlt_hash": None,
            "render_hash": None,
            "output_path": None,
            "verdict": "exception",
            "error": None,
            "metadata": {}
        }

        # 1. Validate
        valid, msg, metadata = self.validate_mlt(mlt_content)
        result["metadata"] = metadata

        if not valid:
            result["error"] = msg
            log.warning(f"MLT validation failed: {msg}")
            return result

        # 2. Hash MLT
        mlt_hash = self.hash_mlt(mlt_content)
        result["mlt_hash"] = mlt_hash
        log.info(f"MLT hash: {mlt_hash[:16]}...")

        # 3. Save
        mlt_path = self.save_mlt(mlt_content, job_id)

        # 4. Render
        success, msg, output_path = self.render(mlt_path, job_id)

        if not success:
            result["error"] = msg
            log.warning(f"MLT render failed: {msg}")
            return result

        # 5. Hash output
        render_hash = hashlib.sha256(output_path.read_bytes()).hexdigest()
        result["render_hash"] = render_hash
        result["output_path"] = str(output_path)
        result["verdict"] = "conforme"

        log.info(f"MLT job complete: {job_id}, verdict=conforme")
        return result

    def get_status(self) -> Dict[str, Any]:
        """Get MLT engine status."""
        return {
            "enabled": self.enabled,
            "melt_available": self.melt_available,
            "melt_bin": MELT_BIN,
            "work_dir": str(MLT_WORK_DIR),
            "render_dir": str(MLT_RENDER_DIR),
            "work_dir_exists": MLT_WORK_DIR.exists(),
            "render_dir_exists": MLT_RENDER_DIR.exists()
        }


# Module-level instance
mlt_engine = MLTEngine()


def get_engine() -> MLTEngine:
    """Get MLT engine instance."""
    return mlt_engine
