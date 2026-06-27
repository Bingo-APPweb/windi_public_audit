"""
WINDI Playground Blueprint — Project Compiler Proxy
====================================================
Proxy para VPSE :8120. Não decide, não sela — apenas encaminha.

Endpoint: /api/decompose
Proxy to: VPSE :8120/prescreen

Invariants: I9 (proxy não escala autonomia), I14 (erro explícito se VPSE down)

§SESSION-20260628: I14 fix — domínio desconhecido → 'unclassified' + log server-side
"""

import logging
import requests
from flask import Blueprint, request, jsonify

playground_bp = Blueprint('playground', __name__)

# Detector de lacunas — print directo para stdout (systemd captura)
# Logger hierárquico não propaga correctamente quando blueprint é importado tarde
import sys

# ---------------------------------------------------------------------------
# Mapa de domínios VPSE → dimensões UI
# Quando um domínio não está aqui, é marcado 'unclassified' e logado.
# Este log é o detector de lacunas — revela onde o mapa precisa crescer.
# ---------------------------------------------------------------------------
DOMAIN_TO_DIMENSION = {
    'live_streaming': 'technology',
    'promotional_mechanics': 'regulatory',
    'document_governance': 'regulatory',
    'finance': 'costs',
    'health': 'regulatory',
    'education': 'users',
}


def _enrich_domains_with_dimension(vpse_result: dict) -> dict:
    """
    Enriquece detected_domains com dimension_id.
    Se domínio não está no mapa → dimension_id='unclassified' + log.

    I14: Não mascara. Não finge saber. Admite e regista.
    """
    domains = vpse_result.get('detected_domains', [])

    for domain in domains:
        content = domain.get('content', '')

        if content in DOMAIN_TO_DIMENSION:
            domain['dimension_id'] = DOMAIN_TO_DIMENSION[content]
        else:
            domain['dimension_id'] = 'unclassified'
            domain['raw'] = True
            # Pegada server-side: detector de lacunas (print directo para systemd)
            print(f"[UNCLASSIFIED_DOMAIN] '{content}' — candidato a entrada no mapa", file=sys.stderr, flush=True)

    return vpse_result

VPSE_URL = "http://127.0.0.1:8120"


@playground_bp.route('/api/decompose', methods=['POST'])
def decompose():
    """
    Decomposes user intent via VPSE engine.

    Input:  { "idea": "...", "context": "...", ... }
    Output: VPSE report with provenance markers

    I9: This endpoint is a PROXY. It does not make decisions.
    I14: If VPSE is down, returns explicit error (no placeholder).
    """
    try:
        data = request.get_json() or {}

        # Validate required field
        if not data.get('idea'):
            return jsonify({
                "error": "MISSING_IDEA",
                "message": "Field 'idea' is required",
                "i14": "Explicit failure — no placeholder"
            }), 400

        # Proxy to VPSE
        vpse_payload = {
            "idea": data.get('idea', ''),
            "context": data.get('context', ''),
            "target_domain": data.get('target_domain', ''),
            "jurisdiction": data.get('jurisdiction', ''),
            "desired_output": data.get('desired_output', 'unknown'),
            "emit_receipt_candidate": data.get('emit_receipt_candidate', False),
        }

        response = requests.post(
            f"{VPSE_URL}/prescreen",
            json=vpse_payload,
            timeout=30
        )

        if response.status_code == 200:
            vpse_result = response.json()

            # I14 fix: enriquecer domínios com dimension_id (ou unclassified + log)
            vpse_result = _enrich_domains_with_dimension(vpse_result)

            # Add proxy metadata
            vpse_result['_proxy'] = {
                "via": "sandbox-core:8091/api/decompose",
                "upstream": "vpse:8120/prescreen",
                "i9": "proxy_only_no_autonomy",
                "i14": "domains_enriched_with_dimension_id"
            }
            return jsonify(vpse_result), 200
        else:
            return jsonify({
                "error": "VPSE_ERROR",
                "status_code": response.status_code,
                "message": response.text[:500],
                "i14": "Upstream error — no masking"
            }), 502

    except requests.exceptions.ConnectionError:
        return jsonify({
            "error": "VPSE_DOWN",
            "message": "VPSE engine at :8120 is not responding",
            "i14": "Explicit failure — VPSE unreachable",
            "action": "Check if VPSE is running: curl localhost:8120/health"
        }), 503

    except requests.exceptions.Timeout:
        return jsonify({
            "error": "VPSE_TIMEOUT",
            "message": "VPSE engine timed out (30s)",
            "i14": "Explicit timeout — not masked"
        }), 504

    except Exception as e:
        return jsonify({
            "error": "INTERNAL_ERROR",
            "message": str(e),
            "i14": "Unhandled exception — exposed for diagnosis"
        }), 500


@playground_bp.route('/api/decompose/health', methods=['GET'])
def decompose_health():
    """Health check for decompose endpoint and upstream VPSE."""
    try:
        vpse_health = requests.get(f"{VPSE_URL}/health", timeout=5)
        if vpse_health.status_code == 200:
            return jsonify({
                "status": "ok",
                "endpoint": "/api/decompose",
                "upstream": "vpse:8120",
                "upstream_status": "ok",
                "vpse": vpse_health.json()
            }), 200
        else:
            return jsonify({
                "status": "degraded",
                "endpoint": "/api/decompose",
                "upstream": "vpse:8120",
                "upstream_status": "error",
                "upstream_code": vpse_health.status_code
            }), 503
    except requests.exceptions.ConnectionError:
        return jsonify({
            "status": "down",
            "endpoint": "/api/decompose",
            "upstream": "vpse:8120",
            "upstream_status": "unreachable"
        }), 503
