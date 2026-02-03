#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WINDI A4 Desk + Template Registry - WSGI Entry Point v1.2.0
============================================================
Para uso com Gunicorn em produção.

Uso:
    gunicorn --workers 2 --bind 127.0.0.1:8085 wsgi:app

Variáveis de ambiente (via /etc/windi/secrets.env):
    WINDI_ADMIN_API_KEY    - Chave para operações administrativas (OBRIGATÓRIO)
    WINDI_GENERATE_API_KEY - Chave para geração (opcional)
    WINDI_DB_PATH          - Path do banco SQLite
    WINDI_SCHEMA_PATH      - Path do schema SQL
"""

import sys
import os

# ============================================================================
# CONFIGURAÇÃO DE PATHS
# ============================================================================

# Adicionar paths necessários
sys.path.insert(0, '/opt/windi/template_registry')
sys.path.insert(0, '/opt/windi/a4desk-editor')

# ============================================================================
# CRIAR OU IMPORTAR APP
# ============================================================================

# Tentar importar app do A4 Desk
try:
    from a4desk_tiptap_babel import app
    print("✅ A4 Desk app loaded")
except ImportError:
    # Fallback: criar app básico se A4 Desk não existir
    from flask import Flask, jsonify
    app = Flask(__name__)
    print("⚠️ A4 Desk not found, using basic app")

# ============================================================================
# REGISTRAR TEMPLATE REGISTRY (COM PROTEÇÃO CONTRA DOUBLE-REGISTER)
# ============================================================================

try:
    from api_endpoints import register_registry_endpoints
    register_registry_endpoints(app)
    # A mensagem de sucesso é impressa pela própria função
except ImportError as e:
    print(f"⚠️ Template Registry not available: {e}")
except Exception as e:
    print(f"❌ Error registering Template Registry: {e}")

# ============================================================================
# ENDPOINTS ADICIONAIS
# ============================================================================

@app.route('/health')
def health():
    """Health check endpoint"""
    return {
        "status": "ok",
        "service": "WINDI A4 Desk + Template Registry",
        "version": "1.2.0"
    }

@app.route('/api/info')
def info():
    """Information about the service"""
    return {
        "service": "WINDI Template Registry",
        "version": "1.2.0",
        "hardened": True,
        "features": [
            "admin_key_protection",
            "human_only_blocking",
            "template_immutability",
            "document_immutability",
            "security_event_logging",
            "request_correlation"
        ],
        "admin_key_configured": bool(os.environ.get('WINDI_ADMIN_API_KEY')),
        "governance_note": "KI verarbeitet. Der Mensch entscheidet. WINDI garantiert."
    }

# ============================================================================
# DESENVOLVIMENTO APENAS
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*60)
    print("⚠️  DEVELOPMENT MODE - Use gunicorn in production!")
    print("="*60)
    print("\nTo run in production:")
    print("  gunicorn --workers 2 --bind 127.0.0.1:8085 wsgi:app")
    print("\n")
    app.run(host='127.0.0.1', port=8085, debug=True)
