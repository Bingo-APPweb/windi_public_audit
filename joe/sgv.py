"""
W-SGV-001 — Truth Illumination Engine
WINDI Publishing House · Kempten, Bavaria
v1.0.0 · 2026-04-03

"SGV nao julga. SGV ilumina."

Principio constitucional:
  NEVER → "isto e falso"
  ALWAYS → "este e o nivel de certeza antes de publicares"

Invariantes:
  I9  — humano e sempre o decisor final
  I13 — SGV nao bloqueia, apenas ilumina
  SGV nao substitui responsabilidade editorial

Pipeline de analise:
  1. Integridade tecnica  (metadata, encoding, sinais de edicao)
  2. Sinais de manipulacao (deepfake patterns, splice, cortes)
  3. Contexto externo      (localizacao, timing, evento)
  → output: VERIFIED | UNVERIFIED | SUSPICIOUS + explainability
"""

import os
import json
import hashlib
import sqlite3
import logging
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List, Tuple
from dataclasses import dataclass, field, asdict

log = logging.getLogger("sgv")

# ── Config ────────────────────────────────────────────────────────────────────
DB_PATH     = os.getenv("SGV_DB", "/opt/windi/joe/sgv.db")
EXPORTS_DIR = Path(os.getenv("VDCUT_EXPORTS", "/opt/windi/media/vd-cut/exports"))
VERSION     = "1.0.0"


# ── Status constants ───────────────────────────────────────────────────────────
class SGVStatus:
    VERIFIED   = "VERIFIED"
    UNVERIFIED = "UNVERIFIED"
    SUSPICIOUS = "SUSPICIOUS"


class Confidence:
    LOW    = "low"
    MEDIUM = "medium"
    HIGH   = "high"


# ── Result dataclass ───────────────────────────────────────────────────────────
@dataclass
class SGVSignal:
    layer:       str
    code:        str
    label:       str
    weight:      float
    is_warning:  bool


@dataclass
class SGVResult:
    fragment_id:    str
    export_id:      str
    sgv_status:     str
    confidence:     str
    risk_score:     float
    signals:        List[SGVSignal]
    explainability: List[str]
    declaration_required: bool
    analysed_at:    str

    def to_dict(self) -> dict:
        return {
            "fragment_id":    self.fragment_id,
            "export_id":      self.export_id,
            "sgv_status":     self.sgv_status,
            "confidence":     self.confidence,
            "risk_score":     round(self.risk_score, 3),
            "explainability": self.explainability,
            "declaration_required": self.declaration_required,
            "analysed_at":    self.analysed_at,
            "signals":        [asdict(s) for s in self.signals],
        }

    def telegram_summary(self) -> str:
        icons = {
            SGVStatus.VERIFIED:   "✅",
            SGVStatus.UNVERIFIED: "⚪",
            SGVStatus.SUSPICIOUS: "⚠️",
        }
        icon = icons.get(self.sgv_status, "?")
        lines = [
            f"{icon} *SGV: {self.sgv_status}* (confianca: {self.confidence})",
            f"Risco: {self.risk_score:.0%}",
            "",
        ]
        for e in self.explainability[:5]:
            lines.append(f"  {e}")
        if self.declaration_required:
            lines.append("")
            lines.append("Declaracao de contexto recomendada.")
        return "\n".join(lines)


# ── DB ─────────────────────────────────────────────────────────────────────────
SGV_SCHEMA = """
CREATE TABLE IF NOT EXISTS sgv_analyses (
    id              TEXT PRIMARY KEY,
    fragment_id     TEXT,
    export_id       TEXT,
    sgv_status      TEXT,
    confidence      TEXT,
    risk_score      REAL,
    signals_json    TEXT,
    explainability  TEXT,
    declaration_req INTEGER DEFAULT 0,
    analysed_at     TEXT
);
"""

def init_sgv_db():
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(DB_PATH)
    db.execute("PRAGMA journal_mode=WAL")
    db.executescript(SGV_SCHEMA)
    db.close()
    log.info("SGV DB initialized at %s", DB_PATH)

def save_result(result: SGVResult):
    db = sqlite3.connect(DB_PATH)
    db.execute("PRAGMA journal_mode=WAL")
    db.execute(
        """INSERT OR REPLACE INTO sgv_analyses
           (id,fragment_id,export_id,sgv_status,confidence,risk_score,
            signals_json,explainability,declaration_req,analysed_at)
           VALUES(?,?,?,?,?,?,?,?,?,?)""",
        (
            f"SGV-{result.fragment_id}",
            result.fragment_id, result.export_id,
            result.sgv_status, result.confidence, result.risk_score,
            json.dumps([asdict(s) for s in result.signals]),
            json.dumps(result.explainability),
            int(result.declaration_required),
            result.analysed_at
        )
    )
    db.commit()
    db.close()


# ── Layer 1: Integridade Tecnica ──────────────────────────────────────────────

def analyse_technical(video_path: Path, expected_hash: str = None) -> List[SGVSignal]:
    signals = []

    if not video_path.exists():
        signals.append(SGVSignal(
            layer="technical", code="FILE_MISSING",
            label="Ficheiro de video nao encontrado para analise",
            weight=0.6, is_warning=True
        ))
        return signals

    # Verificar hash do ficheiro
    if expected_hash:
        actual = _file_hash(video_path)
        expected_clean = expected_hash.replace("sha256:", "")
        if actual == expected_clean:
            signals.append(SGVSignal(
                layer="technical", code="HASH_OK",
                label="Hash do ficheiro corresponde ao registado no VD-CUT",
                weight=0.0, is_warning=False
            ))
        else:
            signals.append(SGVSignal(
                layer="technical", code="HASH_MISMATCH",
                label="Hash do ficheiro nao corresponde — possivel adulteracao",
                weight=0.9, is_warning=True
            ))

    # ffprobe para metadata
    try:
        probe = _ffprobe(video_path)
        streams = probe.get("streams", [])
        fmt     = probe.get("format", {})

        video_streams = [s for s in streams if s.get("codec_type") == "video"]

        for vs in video_streams:
            codec = vs.get("codec_name", "unknown")
            if codec == "h264":
                signals.append(SGVSignal(
                    layer="technical", code="CODEC_H264",
                    label="Codec H.264 consistente com captura directa",
                    weight=0.0, is_warning=False
                ))
            else:
                signals.append(SGVSignal(
                    layer="technical", code="CODEC_UNUSUAL",
                    label=f"Codec '{codec}' incomum para captura mobile",
                    weight=0.3, is_warning=True
                ))

            # Frame rate
            fr_str = vs.get("r_frame_rate", "0/1")
            fr     = _parse_fraction(fr_str)
            if 20 <= fr <= 60:
                signals.append(SGVSignal(
                    layer="technical", code="FPS_NORMAL",
                    label=f"Frame rate {fr:.1f}fps dentro do intervalo normal",
                    weight=0.0, is_warning=False
                ))
            elif fr < 10 or fr > 120:
                signals.append(SGVSignal(
                    layer="technical", code="FPS_ANOMALY",
                    label=f"Frame rate {fr:.1f}fps anomalo — possivel re-encoding",
                    weight=0.4, is_warning=True
                ))

        # Duracao vs tamanho do ficheiro
        duration = float(fmt.get("duration", 0))
        size_kb   = int(fmt.get("size", 0)) / 1024
        if duration > 0:
            kbps = (size_kb * 8) / duration
            if 200 <= kbps <= 8000:
                signals.append(SGVSignal(
                    layer="technical", code="BITRATE_OK",
                    label=f"Bitrate {kbps:.0f}kbps consistente com captura directa",
                    weight=0.0, is_warning=False
                ))
            elif kbps < 50:
                signals.append(SGVSignal(
                    layer="technical", code="BITRATE_TOO_LOW",
                    label=f"Bitrate muito baixo ({kbps:.0f}kbps)",
                    weight=0.35, is_warning=True
                ))

        # Metadata GPS/timestamp
        tags = fmt.get("tags", {})
        if any(k.lower() in ("location", "gps", "creation_time") for k in tags):
            signals.append(SGVSignal(
                layer="technical", code="METADATA_RICH",
                label="Metadata de localizacao/timestamp presente",
                weight=0.0, is_warning=False
            ))
        else:
            signals.append(SGVSignal(
                layer="technical", code="METADATA_SPARSE",
                label="Metadata de localizacao/timestamp ausente",
                weight=0.1, is_warning=True
            ))

    except Exception as e:
        log.warning("ffprobe failed: %s", e)
        signals.append(SGVSignal(
            layer="technical", code="PROBE_FAILED",
            label="Analise tecnica parcial — ffprobe indisponivel",
            weight=0.15, is_warning=True
        ))

    return signals


# ── Layer 2: Sinais de Manipulacao ────────────────────────────────────────────

def analyse_manipulation(video_path: Path) -> List[SGVSignal]:
    signals = []

    if not video_path.exists():
        return signals

    try:
        # Detectar scene cuts
        cuts = _detect_scene_cuts(video_path)
        duration = _get_duration(video_path)

        if duration > 0 and cuts is not None:
            cuts_per_min = (cuts / duration) * 60
            if cuts_per_min <= 4:
                signals.append(SGVSignal(
                    layer="manipulation", code="CUTS_NORMAL",
                    label=f"Ritmo de corte natural ({cuts_per_min:.1f}/min)",
                    weight=0.0, is_warning=False
                ))
            elif cuts_per_min <= 12:
                signals.append(SGVSignal(
                    layer="manipulation", code="CUTS_ELEVATED",
                    label=f"Cortes elevados ({cuts_per_min:.1f}/min) — pode ser edicao legitima",
                    weight=0.25, is_warning=True
                ))
            else:
                signals.append(SGVSignal(
                    layer="manipulation", code="CUTS_SUSPICIOUS",
                    label=f"Cortes muito frequentes ({cuts_per_min:.1f}/min) — possivel splice",
                    weight=0.55, is_warning=True
                ))

        # Detectar freezes
        freezes = _detect_freezes(video_path)
        if freezes == 0:
            signals.append(SGVSignal(
                layer="manipulation", code="NO_FREEZE",
                label="Sem frames congelados detectados",
                weight=0.0, is_warning=False
            ))
        elif freezes <= 2:
            signals.append(SGVSignal(
                layer="manipulation", code="MINOR_FREEZE",
                label=f"{freezes} momento(s) de freeze detectado(s)",
                weight=0.2, is_warning=True
            ))
        else:
            signals.append(SGVSignal(
                layer="manipulation", code="FREEZE_PATTERN",
                label=f"{freezes} freezes detectados — padrao associado a stitching",
                weight=0.5, is_warning=True
            ))

        # Audio/video sync
        av_drift = _check_av_sync(video_path)
        if av_drift is not None:
            if av_drift < 0.2:
                signals.append(SGVSignal(
                    layer="manipulation", code="AV_SYNC_OK",
                    label=f"Sincronismo audio/video correcto ({av_drift*1000:.0f}ms)",
                    weight=0.0, is_warning=False
                ))
            else:
                signals.append(SGVSignal(
                    layer="manipulation", code="AV_DRIFT",
                    label=f"Deriva audio/video de {av_drift*1000:.0f}ms — possivel re-montagem",
                    weight=0.4, is_warning=True
                ))

    except Exception as e:
        log.warning("Manipulation analysis error: %s", e)
        signals.append(SGVSignal(
            layer="manipulation", code="ANALYSIS_PARTIAL",
            label="Analise de manipulacao parcial",
            weight=0.1, is_warning=True
        ))

    return signals


# ── Layer 3: Contexto Externo ─────────────────────────────────────────────────

def analyse_context(
    location:  str = None,
    timestamp: str = None,
    claim:     str = None,
) -> List[SGVSignal]:
    signals = []
    now = datetime.now(timezone.utc)

    # Localizacao declarada
    if location:
        signals.append(SGVSignal(
            layer="context", code="LOCATION_DECLARED",
            label=f"Localizacao declarada: '{location}'",
            weight=0.0, is_warning=False
        ))
    else:
        signals.append(SGVSignal(
            layer="context", code="LOCATION_MISSING",
            label="Localizacao nao declarada",
            weight=0.2, is_warning=True
        ))

    # Timestamp plausivel
    if timestamp:
        try:
            ts = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            delta_hours = abs((now - ts).total_seconds()) / 3600
            if delta_hours <= 1:
                signals.append(SGVSignal(
                    layer="context", code="TIMESTAMP_FRESH",
                    label=f"Captura recente ({delta_hours*60:.0f} min atras)",
                    weight=0.0, is_warning=False
                ))
            elif delta_hours <= 24:
                signals.append(SGVSignal(
                    layer="context", code="TIMESTAMP_RECENT",
                    label=f"Captura de {delta_hours:.1f}h atras — plausivel",
                    weight=0.05, is_warning=False
                ))
            elif delta_hours <= 72:
                signals.append(SGVSignal(
                    layer="context", code="TIMESTAMP_OLD",
                    label=f"Captura de {delta_hours:.0f}h atras — contexto pode ter mudado",
                    weight=0.2, is_warning=True
                ))
            else:
                signals.append(SGVSignal(
                    layer="context", code="TIMESTAMP_STALE",
                    label="Captura de mais de 3 dias",
                    weight=0.4, is_warning=True
                ))
        except Exception:
            signals.append(SGVSignal(
                layer="context", code="TIMESTAMP_INVALID",
                label="Timestamp invalido ou ilegivel",
                weight=0.25, is_warning=True
            ))
    else:
        signals.append(SGVSignal(
            layer="context", code="TIMESTAMP_MISSING",
            label="Sem timestamp de captura declarado",
            weight=0.15, is_warning=True
        ))

    # Declaracao de contexto (claim)
    if claim and len(claim.strip()) >= 10:
        signals.append(SGVSignal(
            layer="context", code="CLAIM_PROVIDED",
            label=f"Contexto editorial declarado ({len(claim)} caracteres)",
            weight=0.0, is_warning=False
        ))
    else:
        signals.append(SGVSignal(
            layer="context", code="CLAIM_MISSING",
            label="Sem declaracao de contexto do autor",
            weight=0.25, is_warning=True
        ))

    return signals


# ── Scoring Engine ────────────────────────────────────────────────────────────

def compute_result(
    fragment_id: str,
    export_id:   str,
    all_signals: List[SGVSignal],
    location:    str = None,
    timestamp:   str = None,
    claim:       str = None,
) -> SGVResult:
    warnings = [s for s in all_signals if s.is_warning]
    positives = [s for s in all_signals if not s.is_warning]

    # Risco ponderado
    if warnings:
        risk = sum(s.weight for s in warnings) / len(all_signals)
        risk = min(risk, 1.0)
    else:
        risk = 0.0

    # Status
    if risk < 0.15:
        status = SGVStatus.VERIFIED
    elif risk < 0.40:
        status = SGVStatus.UNVERIFIED
    else:
        status = SGVStatus.SUSPICIOUS

    # Confianca
    pos_ratio = len(positives) / max(len(all_signals), 1)
    if pos_ratio >= 0.6:
        confidence = Confidence.HIGH
    elif pos_ratio >= 0.35:
        confidence = Confidence.MEDIUM
    else:
        confidence = Confidence.LOW

    # Explainability
    explainability = []
    for s in positives:
        explainability.append(f"OK {s.label}")
    for s in warnings:
        if s.weight >= 0.4:
            explainability.append(f"!! {s.label}")
        elif s.weight >= 0.15:
            explainability.append(f"-- {s.label}")

    declaration_required = (status == SGVStatus.SUSPICIOUS) or (not claim)

    return SGVResult(
        fragment_id=fragment_id,
        export_id=export_id,
        sgv_status=status,
        confidence=confidence,
        risk_score=risk,
        signals=all_signals,
        explainability=explainability,
        declaration_required=declaration_required,
        analysed_at=datetime.now(timezone.utc).isoformat()
    )


# ── Public API ─────────────────────────────────────────────────────────────────

def analyse(
    fragment_id:   str,
    export_id:     str,
    video_path:    Path = None,
    expected_hash: str  = None,
    location:      str  = None,
    timestamp:     str  = None,
    claim:         str  = None,
) -> SGVResult:
    """
    Ponto de entrada principal.
    Corre as 3 camadas e retorna SGVResult.
    """
    log.info("SGV analyse: fragment=%s export=%s", fragment_id, export_id)

    signals = []
    vp = video_path or Path("/dev/null")
    signals += analyse_technical(vp, expected_hash)
    signals += analyse_manipulation(vp)
    signals += analyse_context(location, timestamp, claim)

    result = compute_result(fragment_id, export_id, signals, location, timestamp, claim)
    save_result(result)

    log.info("SGV result: %s (risk=%.2f confidence=%s)",
             result.sgv_status, result.risk_score, result.confidence)
    return result


# ── FFmpeg helpers ─────────────────────────────────────────────────────────────

def _ffprobe(video_path: Path) -> dict:
    cmd = [
        "ffprobe", "-v", "quiet", "-print_format", "json",
        "-show_streams", "-show_format", str(video_path)
    ]
    out = subprocess.check_output(cmd, timeout=15)
    return json.loads(out)

def _detect_scene_cuts(video_path: Path, threshold: float = 0.35) -> int:
    cmd = [
        "ffmpeg", "-i", str(video_path),
        "-vf", f"select='gt(scene,{threshold})',showinfo",
        "-vsync", "vfr", "-f", "null", "-"
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return result.stderr.count("pts_time")
    except Exception:
        return 0

def _detect_freezes(video_path: Path) -> int:
    cmd = [
        "ffmpeg", "-i", str(video_path),
        "-vf", "freezedetect=n=-60dB:d=0.5",
        "-f", "null", "-"
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return result.stderr.count("freeze_start")
    except Exception:
        return 0

def _check_av_sync(video_path: Path) -> Optional[float]:
    try:
        probe = _ffprobe(video_path)
        streams = probe.get("streams", [])
        vs = next((s for s in streams if s.get("codec_type") == "video"), None)
        as_ = next((s for s in streams if s.get("codec_type") == "audio"), None)
        if vs and as_:
            v_start = float(vs.get("start_time", 0))
            a_start = float(as_.get("start_time", 0))
            return abs(v_start - a_start)
    except Exception:
        pass
    return None

def _get_duration(video_path: Path) -> float:
    try:
        probe = _ffprobe(video_path)
        return float(probe.get("format", {}).get("duration", 0))
    except Exception:
        return 0.0

def _parse_fraction(frac: str) -> float:
    try:
        parts = frac.split("/")
        return float(parts[0]) / float(parts[1]) if len(parts) == 2 else float(frac)
    except Exception:
        return 0.0

def _file_hash(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()
