"""
W-WORKBENCH-001 — Playground Server (Peça 3)
WINDI Publishing House · 2026

O "vidro" que liga o frontend ao motor de decomposição.
Serve o playground-v2.html e expõe /api/decompose para o Dragon Hub.

Port: :8203
Invariants: I9, I10, I14
"""

import os
import json
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from datetime import datetime

from decomposition_fill import decomposition_fill, DEFAULT_ENGINE, ENGINES
from decomposition_grammar import ProjectGraph, get_grammar_contract

app = Flask(__name__)
CORS(app)

# Static files directory
STATIC_DIR = os.path.dirname(os.path.abspath(__file__))


# ============================================================================
# STATIC FILES
# ============================================================================

@app.route('/')
def serve_playground():
    """Serve playground-v2.html"""
    return send_from_directory(STATIC_DIR, 'playground-v2.html')


@app.route('/<path:filename>')
def serve_static(filename):
    """Serve other static files"""
    return send_from_directory(STATIC_DIR, filename)


# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.route('/api/decompose', methods=['POST'])
def decompose():
    """
    Decompõe uma intenção em ProjectGraph via Dragon Hub.

    Request:
    {
        "intent": "Quero criar um app para clínica",
        "engine": "DRAGON_HUB",  // optional
        "lang": "pt"  // optional
    }

    Response:
    {
        "success": true,
        "graph": {...},
        "metadata": {...},
        "status": "estimated",
        "requires_confirmation": true
    }

    Invariants:
    - I9: Resultado sempre "estimated" até confirmação humana
    - I10: Se motor indisponível, retorna erro explícito (não fallback silencioso)
    - I14: Sem placeholders — se falhar, falha explicitamente
    """
    try:
        data = request.get_json() or {}
        intent = data.get('intent', '').strip()

        if not intent:
            return jsonify({
                'success': False,
                'error': 'Intent is required',
                'error_code': 'MISSING_INTENT'
            }), 400

        engine = data.get('engine', DEFAULT_ENGINE)
        lang = data.get('lang', 'pt')

        # Validate engine
        if engine not in ENGINES:
            return jsonify({
                'success': False,
                'error': f'Unknown engine: {engine}. Available: {list(ENGINES.keys())}',
                'error_code': 'INVALID_ENGINE'
            }), 400

        # Call decomposition
        graph, metadata = decomposition_fill(
            intent=intent,
            engine=engine,
            lang=lang,
            minimize=True
        )

        if not metadata.get('success'):
            # I14: Explicit failure, no placeholder
            return jsonify({
                'success': False,
                'error': metadata.get('error', 'Unknown error during decomposition'),
                'error_code': 'DECOMPOSITION_FAILED',
                'engine': engine,
                'timestamp': metadata.get('timestamp')
            }), 500

        return jsonify({
            'success': True,
            'graph': graph.to_dict(lang),
            'metadata': {
                'engine': metadata.get('engine'),
                'minimized': metadata.get('minimized'),
                'removed_count': len(metadata.get('removed_items', [])),
                'timestamp': metadata.get('timestamp')
            },
            'status': 'estimated',  # I9: SEMPRE estimado até confirmação humana
            'requires_confirmation': True
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'error_code': 'SERVER_ERROR'
        }), 500


@app.route('/api/grammar', methods=['GET'])
def grammar():
    """
    Retorna o contrato da gramática para referência.
    """
    lang = request.args.get('lang', 'en')
    return jsonify({
        'success': True,
        'grammar': get_grammar_contract(lang),
        'schema_version': '1.0.0'
    })


@app.route('/api/engines', methods=['GET'])
def engines():
    """
    Lista motores disponíveis.
    """
    return jsonify({
        'success': True,
        'engines': [
            {
                'id': engine_id,
                'name': config.name,
                'tier': config.tier,
                'available': True  # TODO: health check
            }
            for engine_id, config in ENGINES.items()
        ],
        'default': DEFAULT_ENGINE
    })


@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({
        'status': 'ok',
        'service': 'W-WORKBENCH-001',
        'component': 'Playground Server',
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    })


# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    print("=" * 60)
    print("W-WORKBENCH-001 — Playground Server")
    print("=" * 60)
    print(f"Port: 8203")
    print(f"Default Engine: {DEFAULT_ENGINE}")
    print(f"Available Engines: {list(ENGINES.keys())}")
    print("=" * 60)
    print("Endpoints:")
    print("  GET  /                 → playground-v2.html")
    print("  POST /api/decompose    → Decompose intent into ProjectGraph")
    print("  GET  /api/grammar      → Get grammar contract")
    print("  GET  /api/engines      → List available engines")
    print("  GET  /api/health       → Health check")
    print("=" * 60)

    app.run(host='0.0.0.0', port=8203, debug=False)
