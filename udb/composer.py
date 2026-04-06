"""
W-COMPOSER-001 — WINDI Sovereign Collage Engine
Multi-momento Composition for Forensic Comparison

Part of W-UDB-001 Dashboard
Port: 8140 (integrated)

"A verdade em estéreo."

Liga IA+H · Kempten, Bavaria · 2026
"""

import os
import subprocess
import hashlib
import sqlite3
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List, Dict, Tuple
import logging

# Configuration
VD_CUT_MEDIA = Path("/opt/windi/media/vd-cut")
VD_CUT_EXPORTS = VD_CUT_MEDIA / "exports"
VD_CUT_SEALED = VD_CUT_MEDIA / "sealed"
COLLAGE_OUTPUT = Path("/opt/windi/media/collages")
COLLAGE_THUMBS = COLLAGE_OUTPUT / "thumbs"
MLT_TEMPLATES = Path("/opt/windi/udb/mlt_templates")

# Ensure directories exist
COLLAGE_OUTPUT.mkdir(parents=True, exist_ok=True)
COLLAGE_THUMBS.mkdir(parents=True, exist_ok=True)
MLT_TEMPLATES.mkdir(parents=True, exist_ok=True)

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("W-COMPOSER-001")


class CollageEngine:
    """
    Sovereign Collage Engine using MLT/melt.
    Creates forensic comparisons from VD-CUT exports.
    """

    def __init__(self, db_path: Path = Path("/opt/windi/udb/dashboard.db")):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initialize collage tracking table."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS collages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                collage_id TEXT UNIQUE NOT NULL,
                layout TEXT NOT NULL,
                source_a TEXT NOT NULL,
                source_b TEXT NOT NULL,
                source_a_timestamp TEXT,
                source_b_timestamp TEXT,
                output_path TEXT,
                output_hash TEXT,
                mlt_recipe TEXT,
                status TEXT DEFAULT 'pending',
                created_at TEXT NOT NULL,
                completed_at TEXT,
                error TEXT
            )
        """)
        conn.commit()
        conn.close()

    def _get_db(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _find_video(self, video_id: str) -> Optional[Path]:
        """Find video file by ID in exports or sealed directories."""
        # Try exports first
        for f in VD_CUT_EXPORTS.glob(f"*{video_id}*.mp4"):
            return f
        # Try sealed
        for f in VD_CUT_SEALED.glob(f"*{video_id}*.mp4"):
            return f
        return None

    def _get_video_info(self, video_path: Path) -> Dict:
        """Get video metadata using ffprobe."""
        try:
            cmd = [
                "ffprobe", "-v", "quiet",
                "-print_format", "json",
                "-show_format", "-show_streams",
                str(video_path)
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                data = json.loads(result.stdout)
                video_stream = next(
                    (s for s in data.get("streams", []) if s.get("codec_type") == "video"),
                    {}
                )
                return {
                    "width": int(video_stream.get("width", 1280)),
                    "height": int(video_stream.get("height", 720)),
                    "duration": float(data.get("format", {}).get("duration", 0)),
                    "fps": eval(video_stream.get("r_frame_rate", "24/1"))
                }
        except Exception as e:
            logger.error(f"ffprobe error: {e}")
        return {"width": 1280, "height": 720, "duration": 0, "fps": 24}

    def _generate_mlt_sidebyside(
        self,
        video_a: Path,
        video_b: Path,
        output_path: Path,
        collage_id: str,
        timestamp_a: str = "",
        timestamp_b: str = ""
    ) -> str:
        """Generate MLT XML for side-by-side comparison."""

        info_a = self._get_video_info(video_a)
        info_b = self._get_video_info(video_b)

        # Use shorter duration
        duration = min(info_a["duration"], info_b["duration"])
        if duration == 0:
            duration = 10  # fallback

        # Output dimensions: 1920x1080, each side 960x1080
        out_width = 1920
        out_height = 1080
        half_width = out_width // 2

        # Timestamps for overlay
        ts_a = timestamp_a or "MOMENTO A"
        ts_b = timestamp_b or "MOMENTO B"

        mlt_xml = f'''<?xml version="1.0" encoding="utf-8"?>
<mlt LC_NUMERIC="C" version="7.12.0" producer="W-COMPOSER-001">
  <profile description="WINDI Collage 1080p" width="{out_width}" height="{out_height}"
           progressive="1" sample_aspect_num="1" sample_aspect_den="1"
           display_aspect_num="16" display_aspect_den="9" frame_rate_num="24" frame_rate_den="1"/>

  <!-- Source A (Left) -->
  <producer id="source_a" in="0" out="{int(duration * 24)}">
    <property name="resource">{video_a}</property>
    <property name="mlt_service">avformat</property>
  </producer>

  <!-- Source B (Right) -->
  <producer id="source_b" in="0" out="{int(duration * 24)}">
    <property name="resource">{video_b}</property>
    <property name="mlt_service">avformat</property>
  </producer>

  <!-- Background -->
  <producer id="background">
    <property name="mlt_service">color</property>
    <property name="resource">#0A0A10</property>
  </producer>

  <!-- Timestamp A Text -->
  <producer id="text_a">
    <property name="mlt_service">qtext</property>
    <property name="text">{ts_a}</property>
    <property name="fgcolour">#C9A84C</property>
    <property name="bgcolour">#00000080</property>
    <property name="olcolour">#000000</property>
    <property name="outline">1</property>
    <property name="pad">10</property>
    <property name="size">32</property>
    <property name="family">JetBrains Mono</property>
  </producer>

  <!-- Timestamp B Text -->
  <producer id="text_b">
    <property name="mlt_service">qtext</property>
    <property name="text">{ts_b}</property>
    <property name="fgcolour">#C9A84C</property>
    <property name="bgcolour">#00000080</property>
    <property name="olcolour">#000000</property>
    <property name="outline">1</property>
    <property name="pad">10</property>
    <property name="size">32</property>
    <property name="family">JetBrains Mono</property>
  </producer>

  <!-- Footer Text -->
  <producer id="footer">
    <property name="mlt_service">qtext</property>
    <property name="text">{collage_id} | WINDI Sovereign Collage</property>
    <property name="fgcolour">#8A8A8A</property>
    <property name="bgcolour">#0A0A10</property>
    <property name="size">24</property>
    <property name="family">JetBrains Mono</property>
  </producer>

  <!-- Main Timeline -->
  <playlist id="main">
    <entry producer="background" in="0" out="{int(duration * 24)}"/>
  </playlist>

  <!-- Track A (Left side) -->
  <playlist id="track_a">
    <entry producer="source_a" in="0" out="{int(duration * 24)}"/>
  </playlist>

  <!-- Track B (Right side) -->
  <playlist id="track_b">
    <entry producer="source_b" in="0" out="{int(duration * 24)}"/>
  </playlist>

  <!-- Overlay Tracks -->
  <playlist id="overlay_a">
    <entry producer="text_a" in="0" out="{int(duration * 24)}"/>
  </playlist>

  <playlist id="overlay_b">
    <entry producer="text_b" in="0" out="{int(duration * 24)}"/>
  </playlist>

  <playlist id="overlay_footer">
    <entry producer="footer" in="0" out="{int(duration * 24)}"/>
  </playlist>

  <!-- Tractor (Composition) -->
  <tractor id="tractor0">
    <multitrack>
      <track producer="main"/>
      <track producer="track_a"/>
      <track producer="track_b"/>
      <track producer="overlay_a"/>
      <track producer="overlay_b"/>
      <track producer="overlay_footer"/>
    </multitrack>

    <!-- Position Source A (left half) -->
    <transition id="trans_a">
      <property name="mlt_service">affine</property>
      <property name="a_track">0</property>
      <property name="b_track">1</property>
      <property name="rect">0 0 {half_width} {out_height}</property>
      <property name="distort">1</property>
    </transition>

    <!-- Position Source B (right half) -->
    <transition id="trans_b">
      <property name="mlt_service">affine</property>
      <property name="a_track">0</property>
      <property name="b_track">2</property>
      <property name="rect">{half_width} 0 {half_width} {out_height}</property>
      <property name="distort">1</property>
    </transition>

    <!-- Position Timestamp A (top-left) -->
    <transition id="trans_text_a">
      <property name="mlt_service">affine</property>
      <property name="a_track">0</property>
      <property name="b_track">3</property>
      <property name="rect">20 20 400 50</property>
    </transition>

    <!-- Position Timestamp B (top-right) -->
    <transition id="trans_text_b">
      <property name="mlt_service">affine</property>
      <property name="a_track">0</property>
      <property name="b_track">4</property>
      <property name="rect">{half_width + 20} 20 400 50</property>
    </transition>

    <!-- Position Footer (bottom center) -->
    <transition id="trans_footer">
      <property name="mlt_service">affine</property>
      <property name="a_track">0</property>
      <property name="b_track">5</property>
      <property name="rect">0 {out_height - 50} {out_width} 50</property>
      <property name="halign">center</property>
    </transition>
  </tractor>
</mlt>'''

        return mlt_xml

    def create_collage(
        self,
        source_a_id: str,
        source_b_id: str,
        timestamp_a: str = "",
        timestamp_b: str = "",
        actor_did: str = ""
    ) -> Dict:
        """
        Create a side-by-side forensic collage.

        Args:
            source_a_id: VD-CUT export ID for left side
            source_b_id: VD-CUT export ID for right side
            timestamp_a: Optional timestamp label for A
            timestamp_b: Optional timestamp label for B
            actor_did: Human actor DID (I9 requirement)

        Returns:
            Dict with collage info or error
        """

        # I9 Gate
        if not actor_did:
            return {"error": "I9 VIOLATION: actor_did required"}

        # Find source videos
        video_a = self._find_video(source_a_id)
        video_b = self._find_video(source_b_id)

        if not video_a:
            return {"error": f"Source A not found: {source_a_id}"}
        if not video_b:
            return {"error": f"Source B not found: {source_b_id}"}

        # Generate collage ID
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        hash_input = f"{source_a_id}{source_b_id}{timestamp}"
        short_hash = hashlib.sha256(hash_input.encode()).hexdigest()[:8].upper()
        collage_id = f"WINDI-COLLAGE-{timestamp}-{short_hash}"

        # Output paths
        output_file = COLLAGE_OUTPUT / f"{collage_id}.mp4"
        mlt_file = MLT_TEMPLATES / f"{collage_id}.mlt"
        thumb_file = COLLAGE_THUMBS / f"{collage_id}_thumb.jpg"

        # Generate MLT recipe
        mlt_xml = self._generate_mlt_sidebyside(
            video_a, video_b, output_file, collage_id,
            timestamp_a, timestamp_b
        )

        # Save MLT file
        mlt_file.write_text(mlt_xml)

        # Register in database
        db = self._get_db()
        c = db.cursor()
        c.execute("""
            INSERT INTO collages
            (collage_id, layout, source_a, source_b, source_a_timestamp, source_b_timestamp,
             output_path, mlt_recipe, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            collage_id, "side-by-side",
            str(video_a), str(video_b),
            timestamp_a, timestamp_b,
            str(output_file), str(mlt_file),
            "pending",
            datetime.now(timezone.utc).isoformat()
        ))
        db.commit()
        db_id = c.lastrowid
        db.close()

        return {
            "status": "PENDING",
            "collage_id": collage_id,
            "db_id": db_id,
            "mlt_recipe": str(mlt_file),
            "output_path": str(output_file),
            "sources": {
                "a": str(video_a),
                "b": str(video_b)
            },
            "message": "Collage queued for rendering. Use /compose/render to start."
        }

    def render_collage(self, collage_id: str) -> Dict:
        """
        Render a pending collage using melt.

        Args:
            collage_id: The collage ID to render

        Returns:
            Dict with render result
        """

        db = self._get_db()
        c = db.cursor()
        c.execute("SELECT * FROM collages WHERE collage_id = ?", (collage_id,))
        row = c.fetchone()

        if not row:
            db.close()
            return {"error": f"Collage not found: {collage_id}"}

        if row["status"] == "completed":
            db.close()
            return {
                "status": "ALREADY_COMPLETED",
                "collage_id": collage_id,
                "output_path": row["output_path"],
                "output_hash": row["output_hash"]
            }

        mlt_file = row["mlt_recipe"]
        output_file = row["output_path"]

        # Update status to rendering
        c.execute(
            "UPDATE collages SET status = ? WHERE collage_id = ?",
            ("rendering", collage_id)
        )
        db.commit()

        try:
            # Run melt
            cmd = [
                "melt", mlt_file,
                "-consumer", f"avformat:{output_file}",
                "vcodec=libx264",
                "acodec=aac",
                "preset=fast",
                "crf=23",
                "threads=2"
            ]

            logger.info(f"Rendering collage: {collage_id}")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 min timeout
            )

            if result.returncode != 0:
                raise Exception(f"melt error: {result.stderr}")

            # Calculate output hash
            output_path = Path(output_file)
            if output_path.exists():
                with open(output_path, "rb") as f:
                    output_hash = hashlib.sha256(f.read()).hexdigest()

                # Generate thumbnail
                thumb_cmd = [
                    "ffmpeg", "-y", "-i", str(output_path),
                    "-ss", "00:00:01", "-vframes", "1",
                    "-vf", "scale=480:-1",
                    str(COLLAGE_THUMBS / f"{collage_id}_thumb.jpg")
                ]
                subprocess.run(thumb_cmd, capture_output=True, timeout=30)

                # Update database
                c.execute("""
                    UPDATE collages
                    SET status = ?, output_hash = ?, completed_at = ?
                    WHERE collage_id = ?
                """, (
                    "completed",
                    output_hash,
                    datetime.now(timezone.utc).isoformat(),
                    collage_id
                ))
                db.commit()
                db.close()

                return {
                    "status": "COMPLETED",
                    "collage_id": collage_id,
                    "output_path": str(output_path),
                    "output_hash": f"sha256:{output_hash}",
                    "file_size": output_path.stat().st_size,
                    "message": "Collage rendered successfully"
                }
            else:
                raise Exception("Output file not created")

        except Exception as e:
            logger.error(f"Render error: {e}")
            c.execute(
                "UPDATE collages SET status = ?, error = ? WHERE collage_id = ?",
                ("error", str(e), collage_id)
            )
            db.commit()
            db.close()
            return {"error": str(e), "collage_id": collage_id}

    def list_collages(self, status: Optional[str] = None) -> List[Dict]:
        """List all collages, optionally filtered by status."""
        db = self._get_db()
        c = db.cursor()

        if status:
            c.execute("SELECT * FROM collages WHERE status = ? ORDER BY created_at DESC", (status,))
        else:
            c.execute("SELECT * FROM collages ORDER BY created_at DESC LIMIT 50")

        rows = c.fetchall()
        db.close()

        return [dict(row) for row in rows]

    def get_collage(self, collage_id: str) -> Optional[Dict]:
        """Get collage by ID."""
        db = self._get_db()
        c = db.cursor()
        c.execute("SELECT * FROM collages WHERE collage_id = ?", (collage_id,))
        row = c.fetchone()
        db.close()
        return dict(row) if row else None


# Singleton instance
composer = CollageEngine()
