#!/usr/bin/env python3
# /opt/windi/engine/wisdom/wisdom_block_manager.py
# ═══════════════════════════════════════════════════════════════════
# WINDI Wisdom Protocol v0.1 — Block Manager (MVP)
#
# Três capacidades:
# 1. create  — criar candidato (proposta manual durante sessão)
# 2. tick    — avaliar TTL/peso (sem daemon, manual)
# 3. decide  — I1: approve/defer/reject (soberania humana)
#
# + list (dashboard de selagem)
# + genesis (selar o Bloco Zero)
#
# Integração: Forensic Ledger :8101 (POST /api/receipts)
# Fallback:   Vault :8106 (POST /api/receipts) se Ledger falhar
#
# "AI processes. Human decides. WINDI guarantees."
# ═══════════════════════════════════════════════════════════════════
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from dataclasses import asdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

# Garante que o módulo schema está acessível
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from schema import (
    WisdomBlockCandidate,
    EmergenceContext,
    OsmoticWeight,
    ShelfCoordinates,
    I1Decision,
    TTL_DEFAULT_MINUTES_BY_CHAMBER,
    ESSENCE_MAX_DEFAULT,
    SHELF_N1_DOMAINS,
    iso_now,
)

# === CAMINHOS ===
BASE_DIR = os.environ.get("WISDOM_BASE_DIR", "/opt/windi/engine/wisdom")
CAND_DIR = os.path.join(BASE_DIR, "candidates")
BLOCKS_DIR = os.path.join(BASE_DIR, "blocks")
MANIFEST_PATH = os.path.join(BASE_DIR, "manifest.json")
LOG_DIR = os.path.join(BASE_DIR, "logs")

# === LEDGER (interno, localhost) ===
LEDGER_URL = os.environ.get("WISDOM_LEDGER_URL", "http://127.0.0.1:8101")
VAULT_URL = os.environ.get("WISDOM_VAULT_URL", "http://127.0.0.1:8106")

# === VERSÃO ===
VERSION = "0.1.0"
PROTOCOL = "WINDI Wisdom Protocol"


# ─────────────────────────────────────────────
# Utilitários
# ─────────────────────────────────────────────

def sha256_hex(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def short_hash(s: str, n: int = 8) -> str:
    return sha256_hex(s)[:n]


def make_candidate_id() -> str:
    ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    rand = short_hash(f"{ts}-{os.getpid()}-{time.monotonic_ns()}", 4)
    return f"WBC-{ts}-{rand}"


def candidate_path(chamber: str, candidate_id: str) -> str:
    return os.path.join(CAND_DIR, chamber, f"{candidate_id}.json")


def write_json(path: str, data: Dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


def read_json(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def log_event(event: str, data: Dict[str, Any]) -> None:
    """Append-only log para rastreabilidade."""
    os.makedirs(LOG_DIR, exist_ok=True)
    log_path = os.path.join(LOG_DIR, "wisdom_events.jsonl")
    entry = {"timestamp": iso_now(), "event": event, **data}
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def http_post_json(url: str, payload: Dict[str, Any],
                   timeout: int = 5) -> Dict[str, Any]:
    """POST JSON com tratamento robusto de erros."""
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = Request(url, data=body,
                  headers={"Content-Type": "application/json"},
                  method="POST")
    try:
        with urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
            return {"ok": True, "status": resp.status,
                    "data": json.loads(raw) if raw.strip() else {}}
    except HTTPError as e:
        body_err = e.read().decode("utf-8", "ignore")[:200]
        return {"ok": False, "error": f"HTTP {e.code}", "detail": body_err}
    except URLError as e:
        return {"ok": False, "error": f"unreachable: {e.reason}"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


# ─────────────────────────────────────────────
# Manifest (registro local de blocos selados)
# ─────────────────────────────────────────────

def ensure_manifest() -> None:
    if not os.path.exists(MANIFEST_PATH):
        write_json(MANIFEST_PATH, {
            "protocol": PROTOCOL,
            "version": VERSION,
            "genesis": "WB-INSP-00000000",
            "created_at": iso_now(),
            "blocks": [],
        })


def load_manifest() -> Dict[str, Any]:
    ensure_manifest()
    return read_json(MANIFEST_PATH)


def save_manifest(m: Dict[str, Any]) -> None:
    write_json(MANIFEST_PATH, m)


# ─────────────────────────────────────────────
# Ledger Integration
# ─────────────────────────────────────────────

def post_to_ledger(wb_id: str, sha: str, essence: str,
                   shelf: Dict[str, str],
                   emergence: Dict[str, Any],
                   session: str, chamber: str) -> Dict[str, Any]:
    """Registra bloco selado no Forensic Ledger.
    
    Formato compatível com o contract existente:
    - id: "VR-WB-{hash12}" (prefixo VR para Virtue Receipt)
    - doc_type: "wisdom_block"
    - content_hash: SHA-256 da essence
    - metadata_json: contexto forense completo
    """
    receipt_hash = short_hash(f"{wb_id}-{sha}-{iso_now()}", 12)
    
    payload = {
        "id": f"VR-WB-{receipt_hash}",
        "doc_type": "wisdom_block",
        "doc_name": wb_id,
        "content_hash": sha,
        "bundle_hash": sha256_hex(json.dumps(shelf, sort_keys=True)),
        "status": "sealed",
        "metadata_json": json.dumps({
            "protocol": PROTOCOL,
            "version": VERSION,
            "wb_id": wb_id,
            "essence_length": len(essence),
            "shelf": shelf,
            "emergence": emergence,
            "origin_session": session,
            "origin_chamber": chamber,
            "hash_algorithm": "SHA-256",
            "sealed_at": iso_now(),
            "decided_by": "human_dragon",
        }, ensure_ascii=False),
    }

    # Tenta Ledger :8101 primeiro
    result = http_post_json(f"{LEDGER_URL}/api/receipts", payload)
    if result.get("ok"):
        result["target"] = "ledger:8101"
        return result

    # Fallback: Vault :8106
    result2 = http_post_json(f"{VAULT_URL}/api/receipts", payload)
    if result2.get("ok"):
        result2["target"] = "vault:8106"
        return result2

    # Ambos falharam — log local e continua (não bloqueia selagem)
    return {
        "ok": False,
        "target": "none",
        "ledger_error": result.get("error", "unknown"),
        "vault_error": result2.get("error", "unknown"),
        "note": "Selagem local OK. Ledger sync pendente.",
    }


# ─────────────────────────────────────────────
# Comandos CLI
# ─────────────────────────────────────────────

def cmd_create(args: argparse.Namespace) -> None:
    """Criar WisdomBlockCandidate (proposta manual durante sessão)."""
    cid = make_candidate_id()
    chamber = args.chamber
    ttl = args.ttl if args.ttl is not None else TTL_DEFAULT_MINUTES_BY_CHAMBER[chamber]

    weight = OsmoticWeight(base=float(args.base_weight))
    weight.recompute()

    tags = [t.strip() for t in args.tags.split(",") if t.strip()] if args.tags else []
    actors = [a.strip() for a in args.actors.split(",") if a.strip()] if args.actors else []

    c = WisdomBlockCandidate(
        candidate_id=cid,
        origin_session=args.session,
        origin_chamber=chamber,
        essence=args.essence.strip(),
        context_tags=tags,
        source_fragments=int(args.source_fragments),
        emergence_context=EmergenceContext(
            situation=args.situation,
            actors_involved=actors,
            intensity=float(args.intensity),
        ),
        weight=weight,
        ttl_remaining=int(ttl),
    )
    c.validate_essence()

    # Aviso se > 280 chars
    if len(c.essence) > ESSENCE_MAX_DEFAULT:
        print(f"⚠️  Essence excepcional: {len(c.essence)} chars (padrão: {ESSENCE_MAX_DEFAULT})",
              file=sys.stderr)

    path = candidate_path(chamber, cid)
    write_json(path, c.to_dict())

    log_event("candidate_created", {
        "candidate_id": cid, "chamber": chamber,
        "essence_len": len(c.essence), "weight": weight.effective,
    })

    result = {
        "created": True,
        "candidate_id": cid,
        "chamber": chamber,
        "essence": c.essence[:90] + ("…" if len(c.essence) > 90 else ""),
        "weight": round(weight.effective, 3),
        "ttl_minutes": c.ttl_remaining,
        "file": path,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


def iter_candidate_files() -> List[str]:
    """Lista todos os ficheiros de candidatos nas três câmaras."""
    out = []
    for chamber in ["echo", "pattern", "archetype"]:
        d = os.path.join(CAND_DIR, chamber)
        if not os.path.isdir(d):
            continue
        for fn in sorted(os.listdir(d)):
            if fn.endswith(".json"):
                out.append(os.path.join(d, fn))
    return out


def cmd_list(args: argparse.Namespace) -> None:
    """Dashboard de selagem: listar candidatos com estado e peso."""
    files = iter_candidate_files()
    rows = []
    for p in files:
        d = read_json(p)
        if args.status and d.get("status") != args.status:
            continue
        rows.append({
            "id": d["candidate_id"],
            "chamber": d["origin_chamber"],
            "status": d["status"],
            "ttl": d.get("ttl_remaining", 0),
            "w_eff": round(d.get("weight", {}).get("effective", 0), 3),
            "cycles": d.get("cycle_count", 0),
            "situation": d.get("emergence_context", {}).get("situation", "?"),
            "tags": d.get("context_tags", []),
            "essence": d["essence"][:90] + ("…" if len(d["essence"]) > 90 else ""),
            "file": p,
        })

    if not rows:
        print("Nenhum candidato encontrado.", file=sys.stderr)
        print("[]")
        return

    # Dashboard visual para o Human Dragon
    if not args.json:
        print(f"\n🛡️  WINDI Wisdom Protocol — Dashboard de Selagem")
        print(f"   {len(rows)} candidato(s) | Filtro: {args.status or 'todos'}\n")
        for i, r in enumerate(rows, 1):
            status_icon = {"candidate": "🟡", "deferred": "🟠",
                          "rejected": "🔴", "sealed": "🟢"}.get(r["status"], "⚪")
            print(f"  {i}. {status_icon} [{r['chamber'][:3].upper()}] {r['id']}")
            print(f"     Essência: {r['essence']}")
            print(f"     Peso: {r['w_eff']}  TTL: {r['ttl']}min  "
                  f"Ciclos: {r['cycles']}  Situação: {r['situation']}")
            print(f"     Tags: {', '.join(r['tags']) if r['tags'] else '—'}")
            print(f"     Ficheiro: {r['file']}")
            print()
    else:
        print(json.dumps(rows, ensure_ascii=False, indent=2))


def cmd_tick(args: argparse.Namespace) -> None:
    """Simular passagem de tempo (avaliar TTL e peso osmótico)."""
    minutes = int(args.minutes)
    files = iter_candidate_files()
    changed = 0
    expired = 0

    for p in files:
        d = read_json(p)
        if d.get("status") in ["rejected", "sealed"]:
            continue

        old_ttl = int(d.get("ttl_remaining", 0))
        d["ttl_remaining"] = max(0, old_ttl - minutes)
        d["last_evaluated"] = iso_now()

        # Se TTL expirou → decaimento osmótico + renovação
        if d["ttl_remaining"] == 0 and d["status"] in ["candidate", "deferred"]:
            d["cycle_count"] = int(d.get("cycle_count", 0)) + 1

            w = d.get("weight", {})
            w["staleness_decay"] = min(0.4,
                float(w.get("staleness_decay", 0.0)) + 0.05)
            w["effective"] = max(0.0, min(1.0,
                float(w.get("base", 0.6))
                + float(w.get("recurrence_bonus", 0.0))
                - float(w["staleness_decay"])))
            d["weight"] = w

            # Renova TTL para permitir reemergência por mérito
            chamber = d.get("origin_chamber", "pattern")
            d["ttl_remaining"] = TTL_DEFAULT_MINUTES_BY_CHAMBER.get(chamber, 360)
            expired += 1

        write_json(p, d)
        changed += 1

    log_event("tick", {"minutes": minutes, "updated": changed, "expired": expired})

    result = {"tick_minutes": minutes, "updated": changed,
              "expired_renewed": expired}
    print(json.dumps(result, ensure_ascii=False, indent=2))


def cmd_decide(args: argparse.Namespace) -> None:
    """Decisão I1 do Human Dragon: approve/defer/reject."""
    target = args.candidate_file
    if not os.path.exists(target):
        print(f"❌ Ficheiro não encontrado: {target}", file=sys.stderr)
        sys.exit(1)

    d = read_json(target)
    action = args.action

    if d.get("status") == "sealed":
        print(f"⚠️  Candidato já selado como: {d.get('sealed_as')}", file=sys.stderr)
        sys.exit(1)

    d["i1_decision"]["action"] = action
    d["i1_decision"]["decided_at"] = iso_now()
    d["i1_decision"]["decided_by"] = "human_dragon"

    # ── REJECT ──
    if action == "reject":
        rej_class = args.rejection_class or "noise"
        d["i1_decision"]["rejection_class"] = rej_class
        d["status"] = "rejected"
        write_json(target, d)
        log_event("i1_reject", {
            "candidate_id": d["candidate_id"],
            "rejection_class": rej_class,
        })
        print(json.dumps({
            "decision": "rejected",
            "class": rej_class,
            "candidate_id": d["candidate_id"],
            "file": target,
        }, ensure_ascii=False, indent=2))
        return

    # ── DEFER ──
    if action == "defer":
        d["status"] = "deferred"
        w = d.get("weight", {})
        w["staleness_decay"] = min(0.4,
            float(w.get("staleness_decay", 0.0)) + 0.02)
        w["effective"] = max(0.0, min(1.0,
            float(w.get("base", 0.6))
            + float(w.get("recurrence_bonus", 0.0))
            - float(w["staleness_decay"])))
        d["weight"] = w
        write_json(target, d)
        log_event("i1_defer", {"candidate_id": d["candidate_id"]})
        print(json.dumps({
            "decision": "deferred",
            "candidate_id": d["candidate_id"],
            "new_weight": round(w["effective"], 3),
            "file": target,
        }, ensure_ascii=False, indent=2))
        return

    # ── APPROVE (SELAGEM) ──
    if action == "approve":
        essence = d.get("essence", "")
        sha = sha256_hex(essence)
        cat = (args.category or "INSP").upper()
        wb_id = f"WB-{cat}-{sha[:8]}"

        # Shelf coordinates (sistema sugere, humano valida via CLI)
        shelf = ShelfCoordinates(
            n1_domain=args.n1 or "philosophy-ethics",
            n2_subdomain=args.n2 or "guiding-principles",
            n3_context=d.get("emergence_context", {}).get("situation", "milestone"),
            n4_maturity=args.n4 or "seed",
            n5_visibility=args.n5 or "internal",
        )

        d["status"] = "sealed"
        d["sha256"] = sha
        d["sealed_as"] = wb_id
        d["shelf"] = shelf.to_dict()

        # Persistir bloco selado no diretório N1
        block_dir = os.path.join(BLOCKS_DIR, shelf.n1_domain)
        os.makedirs(block_dir, exist_ok=True)
        block_path = os.path.join(block_dir, f"{wb_id}.json")
        write_json(block_path, d)

        # Atualizar manifest local
        m = load_manifest()
        m["blocks"].append({
            "id": wb_id,
            "sha256": sha,
            "path": block_path,
            "sealed_at": iso_now(),
            "shelf": shelf.to_dict(),
            "essence_preview": essence[:90],
        })
        save_manifest(m)

        # Registrar no Forensic Ledger
        ledger_result = post_to_ledger(
            wb_id=wb_id,
            sha=sha,
            essence=essence,
            shelf=shelf.to_dict(),
            emergence=d.get("emergence_context", {}),
            session=d.get("origin_session", "unknown"),
            chamber=d.get("origin_chamber", "pattern"),
        )

        # Atualizar ficheiro original do candidato
        write_json(target, d)

        log_event("i1_approve", {
            "candidate_id": d["candidate_id"],
            "wb_id": wb_id,
            "sha256": sha,
            "shelf": shelf.to_dict(),
            "ledger": ledger_result.get("target", "none"),
        })

        print(json.dumps({
            "decision": "sealed",
            "wb_id": wb_id,
            "sha256": sha,
            "shelf": shelf.to_dict(),
            "block_path": block_path,
            "candidate_file": target,
            "ledger_result": ledger_result,
        }, ensure_ascii=False, indent=2))
        return

    print(f"❌ Acção desconhecida: {action}", file=sys.stderr)
    sys.exit(1)


def cmd_genesis(args: argparse.Namespace) -> None:
    """Selar o Bloco Genesis — WB-INSP-00000000.
    
    O primeiro bloco de sabedoria do WINDI.
    """
    genesis_essence = (
        "AI processes. Human decides. WINDI guarantees. "
        "O átomo precisa estar estável antes do organismo crescer."
    )
    sha = sha256_hex(genesis_essence)
    wb_id = "WB-INSP-00000000"

    shelf = ShelfCoordinates(
        n1_domain="philosophy-ethics",
        n2_subdomain="guiding-principles",
        n3_context="milestone",
        n4_maturity="canonical",
        n5_visibility="public",
    )

    genesis_block = {
        "candidate_id": "WBC-GENESIS-0000",
        "origin_session": "three-dragons-convergence-20260221",
        "origin_chamber": "archetype",
        "essence": genesis_essence,
        "context_tags": ["genesis", "convergence", "three-dragons",
                        "governance", "wisdom-protocol"],
        "source_fragments": 0,
        "emergence_context": {
            "situation": "milestone",
            "actors_involved": ["human_dragon", "guardian", "architect", "witness"],
            "intensity": 1.0,
        },
        "weight": {
            "base": 1.0,
            "recurrence_count": 0,
            "recurrence_bonus": 0.0,
            "staleness_decay": 0.0,
            "effective": 1.0,
        },
        "status": "sealed",
        "ttl_remaining": 0,
        "created_at": iso_now(),
        "last_evaluated": iso_now(),
        "cycle_count": 0,
        "i1_decision": {
            "action": "approve",
            "rejection_class": None,
            "decided_at": iso_now(),
            "decided_by": "human_dragon",
        },
        "sealed_as": wb_id,
        "sha256": sha,
        "shelf": shelf.to_dict(),
    }

    block_dir = os.path.join(BLOCKS_DIR, "philosophy-ethics")
    os.makedirs(block_dir, exist_ok=True)
    block_path = os.path.join(block_dir, f"{wb_id}.json")
    write_json(block_path, genesis_block)

    m = load_manifest()
    # Evitar duplicatas
    if not any(b["id"] == wb_id for b in m["blocks"]):
        m["blocks"].insert(0, {
            "id": wb_id,
            "sha256": sha,
            "path": block_path,
            "sealed_at": iso_now(),
            "shelf": shelf.to_dict(),
            "essence_preview": genesis_essence[:90],
        })
        save_manifest(m)

    # Registrar no Ledger
    ledger_result = post_to_ledger(
        wb_id=wb_id, sha=sha, essence=genesis_essence,
        shelf=shelf.to_dict(),
        emergence=genesis_block["emergence_context"],
        session="three-dragons-convergence-20260221",
        chamber="archetype",
    )

    log_event("genesis_sealed", {"wb_id": wb_id, "sha256": sha})

    print(json.dumps({
        "genesis": True,
        "wb_id": wb_id,
        "sha256": sha,
        "essence": genesis_essence,
        "shelf": shelf.to_dict(),
        "block_path": block_path,
        "ledger_result": ledger_result,
    }, ensure_ascii=False, indent=2))


def cmd_info(args: argparse.Namespace) -> None:
    """Informações do protocolo e estatísticas."""
    m = load_manifest()
    candidates = iter_candidate_files()

    stats = {"candidate": 0, "deferred": 0, "rejected": 0, "sealed": 0}
    for p in candidates:
        d = read_json(p)
        s = d.get("status", "candidate")
        stats[s] = stats.get(s, 0) + 1

    print(json.dumps({
        "protocol": PROTOCOL,
        "version": VERSION,
        "genesis": m.get("genesis", "WB-INSP-00000000"),
        "blocks_sealed": len(m.get("blocks", [])),
        "candidates": stats,
        "base_dir": BASE_DIR,
        "ledger_url": LEDGER_URL,
    }, ensure_ascii=False, indent=2))


# ─────────────────────────────────────────────
# CLI Parser
# ─────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="wisdom_block_manager",
        description=f"🛡️ {PROTOCOL} v{VERSION} — Block Manager",
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    # ── create ──
    c = sub.add_parser("create", help="Criar WisdomBlockCandidate")
    c.add_argument("--session", required=True, help="ID da sessão")
    c.add_argument("--chamber", required=True,
                   choices=["echo", "pattern", "archetype"])
    c.add_argument("--essence", required=True,
                   help="Destilação (280 chars padrão)")
    c.add_argument("--tags", default="", help="Tags separadas por vírgula")
    c.add_argument("--source-fragments", default=0, type=int)
    c.add_argument("--base-weight", default=0.6, type=float,
                   help="Peso base (0.0-1.0)")
    c.add_argument("--ttl", default=None, type=int,
                   help="TTL override em minutos")
    c.add_argument("--situation", default="design",
                   help="Contexto: crisis|audit|design|conflict|milestone|...")
    c.add_argument("--actors", default="",
                   help="Actores envolvidos, separados por vírgula")
    c.add_argument("--intensity", default=0.5, type=float,
                   help="Intensidade do momento (0.0-1.0)")
    c.set_defaults(func=cmd_create)

    # ── list ──
    ls = sub.add_parser("list", help="Dashboard de Selagem")
    ls.add_argument("--status", default=None,
                    choices=["candidate", "deferred", "rejected", "sealed"])
    ls.add_argument("--json", action="store_true",
                    help="Output em JSON puro")
    ls.set_defaults(func=cmd_list)

    # ── tick ──
    t = sub.add_parser("tick", help="Avaliar TTL/peso (manual)")
    t.add_argument("--minutes", required=True, type=int,
                   help="Minutos decorridos")
    t.set_defaults(func=cmd_tick)

    # ── decide ──
    d = sub.add_parser("decide", help="Decisão I1: approve/defer/reject")
    d.add_argument("candidate_file",
                   help="Caminho para o ficheiro JSON do candidato")
    d.add_argument("--action", required=True,
                   choices=["approve", "defer", "reject"])
    d.add_argument("--rejection-class", default=None,
                   choices=["noise", "premature", "duplicate-pattern"])
    d.add_argument("--category", default="INSP",
                   help="Código curto WB (INSP, KNOW, PROF, ARCH, ...)")
    d.add_argument("--n1", default=None,
                   help=f"Domain: {', '.join(SHELF_N1_DOMAINS)}")
    d.add_argument("--n2", default=None, help="SubDomain")
    d.add_argument("--n4", default="seed",
                   choices=["seed", "validated", "canonical", "legacy"])
    d.add_argument("--n5", default="internal",
                   choices=["public", "internal", "restricted", "guardian-only"])
    d.set_defaults(func=cmd_decide)

    # ── genesis ──
    g = sub.add_parser("genesis", help="Selar o Bloco Genesis")
    g.set_defaults(func=cmd_genesis)

    # ── info ──
    i = sub.add_parser("info", help="Status do protocolo")
    i.set_defaults(func=cmd_info)

    return p


def main() -> None:
    ensure_manifest()
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
