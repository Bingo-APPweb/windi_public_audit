"""
W-VERIFY-001 — Agente Interpretador Constitucional
════════════════════════════════════════════════════════════════════
Extensão do Sandbox Core (:8091) — padrão constellation WINDI
Versão:          1.0.0
Porto:           :8091 (via blueprint, NÃO standalone)
Prefixo:         /verify-agent/
Invariante:      I9 — sem autonomia. Interpreta. Nunca decide.
Regra central:   WINDI GARANTE apenas Modo 1.
                 Modos 2+3 → análise. Nunca garantia.
════════════════════════════════════════════════════════════════════

DEPLOY:
  cp w-verify-001-blueprint.py /opt/windi/agents/constitutional-agent/blueprints/
  # Reiniciar constitutional-agent (nohup):
  kill $(pgrep -f "constitutional-agent") && sleep 2
  cd /opt/windi/agents/constitutional-agent
  nohup python3 agent.py >> /opt/windi/logs/constitutional-agent.log 2>&1 &
  curl -s http://localhost:8091/verify-agent/health

SMOKE TEST:
  curl -s -X POST http://localhost:8091/verify-agent/interpret \
    -H "Content-Type: application/json" \
    -d '{"mode":2,"result":{"integrity":"MATCH","sha256":"abc123...","filename":"doc.pdf"}}'
"""

from flask import Blueprint, request, jsonify
from typing import Optional, Literal
from datetime import datetime, timezone
import re

router = Blueprint("w_verify_001", __name__, url_prefix="/verify-agent")

# ─────────────────────────────────────────────
# TABELA DE PADRÕES — QR externos (Modo 3)
# Expandir conforme mercado cresce
# ─────────────────────────────────────────────

QR_PATTERNS = [
    {
        "id": "nfe_br",
        "name": "Nota Fiscal Eletrônica (BR)",
        "regex": r"^https?://(www\.)?nfe\.fazenda\.gov\.br",
        "alt_regex": r"\b[0-9]{44}\b",
        "official_url_template": "https://www.nfe.fazenda.gov.br/portal/consultaRecaptcha.aspx",
        "fields": ["chave_acesso", "cnpj_emitente", "valor_total"],
    },
    {
        "id": "nfce_br",
        "name": "Nota Fiscal do Consumidor Eletrônica (BR)",
        "regex": r"nfce\.(fazenda|sefaz)\.",
        "official_url_template": None,
        "fields": ["chave_acesso"],
    },
    {
        "id": "gov_de_elster",
        "name": "Dokument Finanzverwaltung (DE)",
        "regex": r"ELSTER|elster|Steuernummer|StNr",
        "official_url_template": "https://www.elster.de",
        "fields": ["steuernummer", "datum"],
    },
    {
        "id": "cert_eu_covid",
        "name": "EU Digital COVID Certificate",
        "regex": r"^HC1:",
        "official_url_template": "https://ec.europa.eu/info/live-work-travel-eu/coronavirus-response/safe-covid-19-vaccines-europeans/eu-digital-covid-certificate_en",
        "fields": ["name", "dob", "vaccine"],
    },
    {
        "id": "pix_br",
        "name": "PIX (Pagamento BR)",
        "regex": r"^000201",
        "official_url_template": None,
        "fields": ["chave_pix", "nome_beneficiario", "valor"],
    },
    {
        "id": "url_generic",
        "name": "URL genérica",
        "regex": r"^https?://",
        "official_url_template": None,
        "fields": ["url"],
    },
    {
        "id": "windi_doc",
        "name": "Documento WINDI",
        "regex": r"^WINDI:",
        "official_url_template": "https://windi-domain.com/verify-public/",
        "fields": ["receipt_id", "hash_prefix"],
    },
]

# ─────────────────────────────────────────────
# MENSAGENS I18N
# ─────────────────────────────────────────────

MESSAGES = {
    "pt": {
        "m1_ok_high":     "Documento WINDI autêntico. Nível de governança HIGH — selado com máxima garantia constitucional.",
        "m1_ok_medium":   "Documento WINDI autêntico. Nível MEDIUM — integridade verificada.",
        "m1_ok_low":      "Documento WINDI autêntico. Nível LOW — registo confirmado.",
        "m1_fail":        "Documento não encontrado no Ledger WINDI. Pode ter sido adulterado, o ID pode estar errado, ou o documento não é WINDI.",
        "m1_sig_note":    "Assinatura Ed25519 presente e válida.",
        "m2_match":       "Ficheiro íntegro. O hash SHA corresponde exactamente. Nenhum byte foi alterado desde a publicação deste hash.",
        "m2_mismatch":    "ATENÇÃO: ficheiro MODIFICADO. O hash calculado diverge do esperado. A diferença pode ser mínima ou total — matematicamente é adulteração.",
        "m2_ocr_low":     "Hash extraído por OCR com confiança baixa ({conf}%). Recomenda-se confirmar colando o hash manualmente.",
        "m2_no_windi":    "Este hash não é WINDI. Prova integridade mas não garante origem nem autoria.",
        "m3_recognized":  "QR identificado: {name}. Decodificação estrutural completa. Para validação oficial, usa o sistema indicado.",
        "m3_unknown":     "QR decodificado mas tipo não reconhecido. O WINDI leu o conteúdo — não é possível indicar sistema oficial de verificação.",
        "m3_windi_qr":    "Este QR é de um documento WINDI! Redireccionando para verificação com garantia total.",
        "cta_verify_official": "Verificar no sistema oficial",
        "cta_create_windi":    "Criar documento WINDI",
        "cta_paste_hash":      "Colar hash manualmente",
        "cta_open_verify":     "Abrir WINDI Verify",
        "const_m1": "I11 activo — evidência criptográfica permanente e irremediável.",
        "const_m2": "Cálculo local via Web Crypto API. Zero dados enviados ao servidor.",
        "const_m3": "WINDI interpreta. O sistema oficial garante. Fronteira constitucional respeitada.",
    },
    "de": {
        "m1_ok_high":     "WINDI-Dokument authentisch. Governance-Level HIGH — höchste konstitutionelle Garantie.",
        "m1_ok_medium":   "WINDI-Dokument authentisch. Level MEDIUM — Integrität bestätigt.",
        "m1_ok_low":      "WINDI-Dokument authentisch. Level LOW — Eintrag bestätigt.",
        "m1_fail":        "Dokument nicht im WINDI-Ledger gefunden. Möglicherweise manipuliert oder kein WINDI-Dokument.",
        "m1_sig_note":    "Ed25519-Signatur vorhanden und gültig.",
        "m2_match":       "Datei integer. SHA-Hash stimmt exakt überein. Kein Byte wurde seit Veröffentlichung geändert.",
        "m2_mismatch":    "ACHTUNG: Datei VERÄNDERT. Berechneter Hash weicht ab. Mathematisch ist das Manipulation.",
        "m2_ocr_low":     "Hash per OCR mit geringer Konfidenz ({conf}%) extrahiert. Manuelles Einfügen empfohlen.",
        "m2_no_windi":    "Kein WINDI-Hash. Beweist Integrität, aber keine Herkunft.",
        "m3_recognized":  "QR identifiziert: {name}. Für offizielle Validierung das angegebene System nutzen.",
        "m3_unknown":     "QR dekodiert, Typ unbekannt. WINDI hat gelesen — offizielles Verifizierungssystem unbekannt.",
        "m3_windi_qr":    "Dies ist ein WINDI QR-Code! Weiterleitung zur vollständigen Verifikation.",
        "cta_verify_official": "Im offiziellen System prüfen",
        "cta_create_windi":    "WINDI-Dokument erstellen",
        "cta_paste_hash":      "Hash manuell einfügen",
        "cta_open_verify":     "WINDI Verify öffnen",
        "const_m1": "I11 aktiv — permanenter kryptografischer Nachweis.",
        "const_m2": "Lokale Berechnung via Web Crypto API. Keine Daten an Server gesendet.",
        "const_m3": "WINDI interpretiert. Das offizielle System garantiert. Konstitutionelle Grenze respektiert.",
    },
    "en": {
        "m1_ok_high":     "Authentic WINDI document. Governance level HIGH — maximum constitutional guarantee.",
        "m1_ok_medium":   "Authentic WINDI document. Level MEDIUM — integrity verified.",
        "m1_ok_low":      "Authentic WINDI document. Level LOW — record confirmed.",
        "m1_fail":        "Document not found in WINDI Ledger. May have been tampered with, wrong ID, or not a WINDI document.",
        "m1_sig_note":    "Ed25519 signature present and valid.",
        "m2_match":       "File intact. SHA hash matches exactly. No byte has been changed since this hash was published.",
        "m2_mismatch":    "WARNING: file MODIFIED. Calculated hash diverges from expected. Mathematically, this is tampering.",
        "m2_ocr_low":     "Hash extracted via OCR with low confidence ({conf}%). Recommend pasting hash manually.",
        "m2_no_windi":    "Not a WINDI hash. Proves integrity but not origin or authorship.",
        "m3_recognized":  "QR identified: {name}. Full structural decode complete. Use the indicated system for official validation.",
        "m3_unknown":     "QR decoded but type not recognised. WINDI read the content — no official verification system can be suggested.",
        "m3_windi_qr":    "This is a WINDI QR code! Redirecting to full-guarantee verification.",
        "cta_verify_official": "Verify in official system",
        "cta_create_windi":    "Create WINDI document",
        "cta_paste_hash":      "Paste hash manually",
        "cta_open_verify":     "Open WINDI Verify",
        "const_m1": "I11 active — permanent, irremediable cryptographic evidence.",
        "const_m2": "Local calculation via Web Crypto API. Zero data sent to server.",
        "const_m3": "WINDI interprets. The official system guarantees. Constitutional boundary respected.",
    },
}

# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────

def _detect_qr_type(raw: str) -> dict:
    """Determina tipo de QR por padrão. Determinístico — zero IA."""
    for pattern in QR_PATTERNS:
        if re.search(pattern["regex"], raw, re.IGNORECASE):
            fields = {}
            for field in pattern.get("fields", []):
                if field == "chave_acesso":
                    m = re.search(r'\b([0-9]{44})\b', raw)
                    if m:
                        fields["chave_acesso"] = m.group(1)
            return {
                "id": pattern["id"],
                "name": pattern["name"],
                "official_url": pattern.get("official_url_template"),
                "fields": fields,
                "schema_recognized": True,
            }
    return {
        "id": "unknown",
        "name": "Tipo desconhecido",
        "official_url": None,
        "fields": {},
        "schema_recognized": False,
    }

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

# ─────────────────────────────────────────────
# ENDPOINTS
# ─────────────────────────────────────────────

@router.route("/health", methods=["GET"])
def health():
    return jsonify({
        "agent": "W-VERIFY-001",
        "version": "1.0.0",
        "status": "OPERATIONAL",
        "invariant": "I9",
        "modes_supported": [1, 2, 3],
        "locales": ["pt", "de", "en"],
        "ts": _now_iso(),
    })

@router.route("/interpret", methods=["POST"])
def interpret():
    """
    Recebe resultado de qualquer dos 3 modos e devolve
    interpretação constitucional em linguagem humana.

    I9 ENFORCEMENT:
    - Modo 1: apenas lê resultado do Ledger. Nunca escreve.
    - Modo 2: interpreta resultado de cálculo local. Nunca calcula.
    - Modo 3: interpreta payload decodificado. Nunca valida.
    """
    data = request.get_json(force=True)
    mode = data.get("mode")
    locale = data.get("locale", "pt")
    msg = MESSAGES.get(locale, MESSAGES["pt"])
    ts = _now_iso()

    # ── MODO 1 — WINDI GARANTE ──────────────────────────────────
    if mode == 1:
        r = data.get("result_mode1", {})
        if not r.get("verified"):
            return jsonify({
                "mode": 1,
                "confidence_level": "LOW",
                "verdict": "NÃO ENCONTRADO",
                "title": "Documento não verificado",
                "message": msg["m1_fail"],
                "action_label": msg["cta_create_windi"],
                "action_url": "https://windi-domain.com/app/",
                "windi_badge": False,
                "constitutional_note": msg["const_m1"],
                "interpreted_at": ts,
            })

        gov = r.get("governance_level", "LOW")
        body = msg.get(f"m1_ok_{gov.lower()}", msg["m1_ok_low"])
        if r.get("ed25519_sig"):
            body += f" {msg['m1_sig_note']}"
        if r.get("created_at"):
            body += f" Data de selagem: {r['created_at'][:10]}."

        return jsonify({
            "mode": 1,
            "confidence_level": "HIGH",
            "verdict": "GARANTIDO",
            "title": f"WINDI GARANTE — {gov}",
            "message": body,
            "action_label": None,
            "action_url": None,
            "windi_badge": True,
            "constitutional_note": msg["const_m1"],
            "interpreted_at": ts,
        })

    # ── MODO 2 — HASH INSPECTOR ──────────────────────────────────
    elif mode == 2:
        r = data.get("result_mode2", {})
        integrity = r.get("integrity", "UNKNOWN")

        if integrity == "MATCH":
            body = msg["m2_match"]
            if r.get("source") == "ocr_photo" and r.get("ocr_confidence") and r["ocr_confidence"] < 0.85:
                conf_pct = int(r["ocr_confidence"] * 100)
                body += f" {msg['m2_ocr_low'].format(conf=conf_pct)}"
            body += f" {msg['m2_no_windi']}"
            return jsonify({
                "mode": 2,
                "confidence_level": "MEDIUM",
                "verdict": "ÍNTEGRO",
                "title": "Hash íntegro — sem adulteração detectada",
                "message": body,
                "agent_message": "Hash correcto. Ficheiro íntegro. Mas lembra: qualquer pessoa pode gerar este hash. Para garantia de origem e autoria → cria documento WINDI.",
                "action_label": msg["cta_create_windi"],
                "action_url": "https://windi-domain.com/app/",
                "windi_badge": False,
                "constitutional_note": msg["const_m2"],
                "interpreted_at": ts,
            })

        elif integrity == "MISMATCH":
            return jsonify({
                "mode": 2,
                "confidence_level": "LOW",
                "verdict": "ADULTERADO",
                "title": "Ficheiro modificado — hash divergente",
                "message": msg["m2_mismatch"],
                "agent_message": "Atenção. Este ficheiro não é o original. A divergência de hash é prova matemática de adulteração — independentemente de qual foi a alteração.",
                "action_label": None,
                "action_url": None,
                "windi_badge": False,
                "constitutional_note": msg["const_m2"],
                "interpreted_at": ts,
            })

        else:
            return jsonify({
                "mode": 2,
                "confidence_level": "LOW",
                "verdict": "INCONCLUSIVO",
                "title": "Não foi possível comparar o hash",
                "message": msg["m2_ocr_low"].format(conf=0) if r.get("source") == "ocr_photo" else "Hash não reconhecido.",
                "agent_message": "Erro durante o cálculo. Tenta novamente ou cola o hash manualmente.",
                "action_label": msg["cta_paste_hash"],
                "action_url": None,
                "windi_badge": False,
                "constitutional_note": msg["const_m2"],
                "interpreted_at": ts,
            })

    # ── MODO 3 — QR DECODER ──────────────────────────────────────
    elif mode == 3:
        r = data.get("result_mode3", {})
        detected_type = r.get("detected_type")
        raw_payload = r.get("raw_payload", "")

        if detected_type == "windi_doc":
            return jsonify({
                "mode": 3,
                "confidence_level": "HIGH",
                "verdict": "WINDI QR",
                "title": "QR WINDI detectado!",
                "message": msg["m3_windi_qr"],
                "action_label": msg["cta_open_verify"],
                "action_url": f"https://windi-domain.com/verify-public/?payload={raw_payload}",
                "windi_badge": False,
                "constitutional_note": msg["const_m3"],
                "interpreted_at": ts,
            })

        if r.get("schema_recognized") and detected_type:
            pattern_name = detected_type.replace("_", " ").upper()
            body = msg["m3_recognized"].format(name=detected_type)
            return jsonify({
                "mode": 3,
                "confidence_level": "MEDIUM",
                "verdict": "DECODIFICADO",
                "title": f"QR identificado: {pattern_name}",
                "message": body,
                "action_label": msg["cta_verify_official"] if r.get("official_verify_url") else None,
                "action_url": r.get("official_verify_url"),
                "windi_badge": False,
                "constitutional_note": msg["const_m3"],
                "interpreted_at": ts,
            })

        return jsonify({
            "mode": 3,
            "confidence_level": "LOW",
            "verdict": "DECODIFICADO",
            "title": "QR decodificado — tipo não reconhecido",
            "message": msg["m3_unknown"],
            "action_label": msg["cta_create_windi"],
            "action_url": "https://windi-domain.com/app/",
            "windi_badge": False,
            "constitutional_note": msg["const_m3"],
            "interpreted_at": ts,
        })

    return jsonify({"error": "mode deve ser 1, 2 ou 3"}), 400


@router.route("/detect-qr-type", methods=["POST"])
def detect_qr_type():
    """
    Detecta tipo de QR por padrão determinístico.
    Usado pelo frontend antes de chamar /interpret.
    Sem IA. Sem rede. Pura regex.
    """
    data = request.get_json(force=True)
    raw = data.get("raw", "")
    if not raw:
        return jsonify({"error": "Campo 'raw' obrigatório"}), 400
    return jsonify(_detect_qr_type(raw))


@router.route("/patterns", methods=["GET"])
def list_patterns():
    """Lista todos os padrões QR conhecidos (sem regex interna)."""
    return jsonify({
        "patterns": [
            {"id": p["id"], "name": p["name"], "has_official_verify": bool(p.get("official_url_template"))}
            for p in QR_PATTERNS
        ],
        "total": len(QR_PATTERNS),
    })
