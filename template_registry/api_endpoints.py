#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WINDI Template Registry - REST API Endpoints v1.2.0 (Regulator Ready)
======================================================================
"KI verarbeitet. Der Mensch entscheidet. WINDI garantiert."

Versão: 1.2.0
Atualizado: 27 JAN 2026

Melhorias v1.2.0:
- Middleware para capturar IP, User-Agent, Request ID
- Headers padronizados (X-WINDI-Admin-Key)
- Erro 403 genérico (não revela se key "quase" bateu)
- Proteção contra double-register
- Request context propagado para auditoria
"""

from flask import Blueprint, request, jsonify, g
from functools import wraps
import json
import os
import hashlib
import uuid
from datetime import datetime

# ============================================================================
# CONFIGURAÇÃO DE SEGURANÇA
# ============================================================================

# API Key para operações administrativas
# CRÍTICO: Em produção, usar variável de ambiente ou secrets manager
# NUNCA imprimir esta chave em logs ou console
ADMIN_API_KEY = os.environ.get('WINDI_ADMIN_API_KEY')

if not ADMIN_API_KEY:
    # Gera uma chave padrão APENAS para desenvolvimento
    # Em produção, SEMPRE definir via variável de ambiente
    import warnings
    warnings.warn(
        "WINDI_ADMIN_API_KEY não definida! Usando chave de desenvolvimento. "
        "NUNCA use em produção sem definir a variável de ambiente.",
        UserWarning
    )
    ADMIN_API_KEY = "DEV_ONLY_" + hashlib.sha256(b'windi_dev').hexdigest()[:32]

# API Key para operações de geração (opcional)
GENERATE_API_KEY = os.environ.get('WINDI_GENERATE_API_KEY')  # None = sem restrição

# ============================================================================
# BLUEPRINTS
# ============================================================================

registry_bp = Blueprint('registry', __name__, url_prefix='/api/registry')
documents_bp = Blueprint('documents', __name__, url_prefix='/api/documents')
audit_bp = Blueprint('audit', __name__, url_prefix='/api/audit')

# Flag para evitar double-register
_endpoints_registered = False

# ============================================================================
# REGISTRY INSTANCE
# ============================================================================

_registry = None

def get_registry():
    """Lazy initialization do registry"""
    global _registry
    if _registry is None:
        from template_registry import TemplateRegistry
        _registry = TemplateRegistry()
    return _registry

# ============================================================================
# MIDDLEWARE: REQUEST CONTEXT
# ============================================================================

def setup_request_context():
    """
    Middleware para capturar contexto da requisição.
    Chamado antes de cada request.
    
    Captura:
    - request_id: UUID único para correlação de logs
    - ip_address: IP do cliente
    - user_agent: User-Agent do cliente
    - timestamp: Momento da requisição
    """
    g.request_id = request.headers.get('X-Request-ID', str(uuid.uuid4()))
    g.ip_address = _get_client_ip()
    g.user_agent = request.headers.get('User-Agent', '')
    g.request_timestamp = datetime.utcnow().isoformat()

def _get_client_ip() -> str:
    """
    Extrai IP real do cliente, considerando proxies.
    Ordem de prioridade: X-Forwarded-For > X-Real-IP > remote_addr
    """
    if request.headers.get('X-Forwarded-For'):
        # Pega primeiro IP da lista (cliente original)
        return request.headers['X-Forwarded-For'].split(',')[0].strip()
    elif request.headers.get('X-Real-IP'):
        return request.headers['X-Real-IP']
    else:
        return request.remote_addr or 'unknown'

def get_request_context() -> dict:
    """Retorna contexto da requisição para passar ao registry"""
    return {
        'request_id': getattr(g, 'request_id', str(uuid.uuid4())),
        'ip_address': getattr(g, 'ip_address', 'unknown'),
        'user_agent': getattr(g, 'user_agent', ''),
        'timestamp': getattr(g, 'request_timestamp', datetime.utcnow().isoformat())
    }

# ============================================================================
# DECORATORS DE SEGURANÇA
# ============================================================================

def require_json(f):
    """Garante que request tem JSON"""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not request.is_json:
            return jsonify({"error": "Content-Type must be application/json"}), 400
        return f(*args, **kwargs)
    return decorated

def require_admin_key(f):
    """
    Protege endpoints administrativos.
    
    Header requerido: X-WINDI-Admin-Key
    
    SEGURANÇA: Erro 403 é genérico - não revela se a key está "quase" certa
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        provided_key = request.headers.get('X-WINDI-Admin-Key', '')
        
        # Comparação segura (timing-safe não é crítico aqui, mas boas práticas)
        if not provided_key or provided_key != ADMIN_API_KEY:
            # Log tentativa sem revelar detalhes
            get_registry().log_security_event(
                event_type="unauthorized_admin_access",
                severity="warning",
                endpoint=request.path,
                method=request.method,
                ip_address=getattr(g, 'ip_address', 'unknown'),
                user_agent=getattr(g, 'user_agent', ''),
                details={
                    "reason": "Invalid or missing admin key"
                    # NÃO logar a key fornecida
                },
                request_id=getattr(g, 'request_id', None)
            )
            # Resposta genérica - não revela se key existe ou está errada
            return jsonify({
                "error": "Unauthorized",
                "message": "Administrative access required"
            }), 403
        return f(*args, **kwargs)
    return decorated

def require_generate_key(f):
    """
    Protege endpoint de geração (opcional).
    Se WINDI_GENERATE_API_KEY não estiver definido, permite acesso livre.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        if GENERATE_API_KEY is not None:
            provided_key = request.headers.get('X-WINDI-API-Key', '')
            if not provided_key or provided_key != GENERATE_API_KEY:
                return jsonify({
                    "error": "Unauthorized",
                    "message": "API key required"
                }), 403
        return f(*args, **kwargs)
    return decorated

# ============================================================================
# TENANT ENDPOINTS
# ============================================================================

@registry_bp.route('/tenants', methods=['GET'])
def list_tenants():
    """GET /api/registry/tenants - Lista todos os tenants ativos"""
    try:
        tenants = get_registry().list_tenants()
        return jsonify({
            "success": True,
            "tenants": tenants,
            "count": len(tenants)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@registry_bp.route('/tenants/<tenant_id>/departments', methods=['GET'])
def list_departments(tenant_id):
    """GET /api/registry/tenants/<tenant_id>/departments"""
    try:
        departments = get_registry().list_departments(tenant_id)
        return jsonify({
            "success": True,
            "tenant_id": tenant_id,
            "departments": departments,
            "count": len(departments)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ============================================================================
# TEMPLATE ENDPOINTS
# ============================================================================

@registry_bp.route('/templates', methods=['GET'])
def list_templates():
    """GET /api/registry/templates"""
    try:
        tenant_id = request.args.get('tenant_id')
        templates = get_registry().list_templates(tenant_id=tenant_id)
        return jsonify({
            "success": True,
            "templates": templates,
            "count": len(templates)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@registry_bp.route('/templates/<template_id>', methods=['GET'])
def get_template(template_id):
    """GET /api/registry/templates/<template_id>"""
    try:
        template = get_registry().get_template(template_id)
        if not template:
            return jsonify({"error": "Template not found"}), 404
        
        return jsonify({
            "success": True,
            "template": template
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@registry_bp.route('/templates/find', methods=['GET'])
def find_template():
    """GET /api/registry/templates/find?tenant=X&department=Y&doctype=Z"""
    try:
        tenant_id = request.args.get('tenant')
        department = request.args.get('department')
        doctype = request.args.get('doctype')
        version = request.args.get('version')
        
        if not all([tenant_id, department, doctype]):
            return jsonify({
                "error": "Required params: tenant, department, doctype"
            }), 400
        
        template = get_registry().find_template(
            tenant_id, department, doctype, version
        )
        
        if not template:
            return jsonify({"error": "Template not found"}), 404
        
        return jsonify({
            "success": True,
            "template": template
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@registry_bp.route('/templates', methods=['POST'])
@require_json
@require_admin_key
def create_template():
    """
    POST /api/registry/templates
    
    Requer: X-WINDI-Admin-Key header
    
    Body: {tenant_id, department_code, doctype_code, title_de, tiptap_json, fields, ...}
    """
    try:
        data = request.json
        
        required = ['tenant_id', 'department_code', 'doctype_code', 
                   'title_de', 'tiptap_json', 'fields']
        missing = [f for f in required if f not in data]
        if missing:
            return jsonify({
                "error": f"Missing required fields: {missing}"
            }), 400
        
        template = get_registry().create_template(
            tenant_id=data['tenant_id'],
            department_code=data['department_code'],
            doctype_code=data['doctype_code'],
            title_de=data['title_de'],
            tiptap_json=data['tiptap_json'],
            fields=data['fields'],
            human_only=data.get('human_only', []),
            governance_rules=data.get('governance_rules', []),
            version=data.get('version', '1.0.0'),
            created_by=data.get('created_by'),
            title_en=data.get('title_en'),
            legal_basis=data.get('legal_basis'),
            disclosure_de=data.get('disclosure_de'),
            disclosure_en=data.get('disclosure_en'),
            request_context=get_request_context()
        )
        
        return jsonify({
            "success": True,
            "template": template,
            "message": "Template created (status: draft)"
        }), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@registry_bp.route('/templates/<template_id>/publish', methods=['POST'])
@require_admin_key
def publish_template(template_id):
    """
    POST /api/registry/templates/<template_id>/publish
    
    Requer: X-WINDI-Admin-Key header
    
    GOVERNANÇA: Templates publicados são IMUTÁVEIS
    """
    try:
        data = request.json or {}
        template = get_registry().publish_template(
            template_id,
            published_by=data.get('published_by'),
            request_context=get_request_context()
        )
        
        if not template:
            return jsonify({"error": "Template not found"}), 404
        
        return jsonify({
            "success": True,
            "template": template,
            "message": "Template published (now immutable)"
        })
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@registry_bp.route('/templates/<template_id>/governance', methods=['GET'])
def get_governance_report(template_id):
    """GET /api/registry/templates/<template_id>/governance"""
    try:
        report = get_registry().get_governance_report(template_id)
        if not report:
            return jsonify({"error": "Template not found"}), 404
        
        return jsonify({
            "success": True,
            "governance_report": report
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ============================================================================
# DOCUMENT ENDPOINTS
# ============================================================================

@documents_bp.route('/generate', methods=['POST'])
@require_json
@require_generate_key
def generate_document():
    """
    POST /api/documents/generate
    
    GOVERNANÇA: Campos human_only NÃO PODEM ser enviados no payload.
    Tentativas são rejeitadas e logadas como eventos de segurança.
    
    Body: {tenant, department, doctype, inputs: {...}}
    """
    try:
        data = request.json
        ctx = get_request_context()
        
        required = ['tenant', 'department', 'doctype', 'inputs']
        missing = [f for f in required if f not in data]
        if missing:
            return jsonify({
                "error": f"Missing required fields: {missing}"
            }), 400
        
        registry = get_registry()
        
        # Buscar template para validar human_only ANTES de gerar
        template = registry.find_template(
            data['tenant'], 
            data['department'], 
            data['doctype']
        )
        
        if not template:
            return jsonify({
                "error": f"Template not found: {data['tenant']}/{data['department']}/{data['doctype']}"
            }), 404
        
        # GOVERNANÇA: Bloquear campos human_only no payload
        human_only_codes = {h['field_code'] for h in template['human_only']}
        inputs = data.get('inputs', {})
        
        blocked_fields = [f for f in inputs.keys() if f in human_only_codes]
        
        if blocked_fields:
            # Log violação de governança
            registry.log_security_event(
                event_type="human_only_violation_attempt",
                severity="warning",
                endpoint=request.path,
                method=request.method,
                ip_address=ctx.get('ip_address'),
                user_agent=ctx.get('user_agent'),
                details={
                    "template_id": template['id'],
                    "blocked_fields": blocked_fields,
                    "user": data.get('created_by', 'anonymous'),
                    "governance_rule": "ai_must_not_decide_human_only"
                },
                request_id=ctx.get('request_id')
            )
            return jsonify({
                "error": "Governance violation",
                "message": f"Fields {blocked_fields} are HUMAN_ONLY and cannot be provided via API",
                "governance_rule": "ai_must_not_decide_human_only",
                "blocked_fields": blocked_fields
            }), 400
        
        # Gerar documento
        result = registry.generate_document(
            tenant_id=data['tenant'],
            department_code=data['department'],
            doctype_code=data['doctype'],
            inputs=inputs,
            created_by=data.get('created_by'),
            language=data.get('language', 'de'),
            request_context=ctx
        )
        
        return jsonify({
            "success": True,
            **result
        })
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@documents_bp.route('/<document_id>', methods=['GET'])
def get_document(document_id):
    """GET /api/documents/<document_id>"""
    try:
        registry = get_registry()
        with registry._get_conn() as conn:
            row = conn.execute(
                "SELECT * FROM documents WHERE id = ?",
                (document_id,)
            ).fetchone()
            
            if not row:
                return jsonify({"error": "Document not found"}), 404
            
            doc = dict(row)
            doc['content_json'] = json.loads(doc['content_json'])
            if doc.get('input_data_json'):
                doc['input_data'] = json.loads(doc['input_data_json'])
            
            return jsonify({
                "success": True,
                "document": doc
            })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@documents_bp.route('/<document_id>/fill-human', methods=['POST'])
@require_json
def fill_human_field(document_id):
    """
    POST /api/documents/<document_id>/fill-human
    
    Preenche campo human_only. Documento não pode estar finalizado.
    
    Body: {field_code, value, filled_by, justification?}
    """
    try:
        data = request.json
        
        required = ['field_code', 'value', 'filled_by']
        missing = [f for f in required if f not in data]
        if missing:
            return jsonify({
                "error": f"Missing required fields: {missing}"
            }), 400
        
        result = get_registry().fill_human_field(
            document_id=document_id,
            field_code=data['field_code'],
            value=data['value'],
            filled_by=data['filled_by'],
            justification=data.get('justification'),
            request_context=get_request_context()
        )
        
        return jsonify({
            "success": True,
            **result
        })
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@documents_bp.route('/<document_id>/finalize', methods=['POST'])
@require_json
def finalize_document(document_id):
    """
    POST /api/documents/<document_id>/finalize
    
    GOVERNANÇA: Documentos finalizados são IMUTÁVEIS (write-once)
    
    Body: {finalized_by}
    """
    try:
        data = request.json
        
        if 'finalized_by' not in data:
            return jsonify({
                "error": "Missing required field: finalized_by"
            }), 400
        
        result = get_registry().finalize_document(
            document_id=document_id,
            finalized_by=data['finalized_by'],
            request_context=get_request_context()
        )
        
        return jsonify({
            "success": True,
            **result
        })
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ============================================================================
# AUDIT ENDPOINTS
# ============================================================================

@audit_bp.route('/<entity_type>/<entity_id>', methods=['GET'])
def get_audit_trail(entity_type, entity_id):
    """GET /api/audit/<entity_type>/<entity_id>"""
    try:
        if entity_type not in ('template', 'document', 'tenant'):
            return jsonify({
                "error": "Invalid entity_type. Use: template, document, tenant"
            }), 400
        
        trail = get_registry().get_audit_trail(entity_type, entity_id)
        
        return jsonify({
            "success": True,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "audit_trail": trail,
            "count": len(trail)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@audit_bp.route('/security-events', methods=['GET'])
@require_admin_key
def get_security_events():
    """
    GET /api/audit/security-events
    
    Requer: X-WINDI-Admin-Key header
    
    Query params: event_type, severity, unresolved_only, limit
    """
    try:
        events = get_registry().get_security_events(
            event_type=request.args.get('event_type'),
            severity=request.args.get('severity'),
            unresolved_only=request.args.get('unresolved_only', 'false').lower() == 'true',
            limit=int(request.args.get('limit', 100))
        )
        
        return jsonify({
            "success": True,
            "security_events": events,
            "count": len(events)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ============================================================================
# INTEGRATION
# ============================================================================

def register_registry_endpoints(app):
    """
    Registra todos os blueprints no app Flask.
    
    Uso:
        from api_endpoints import register_registry_endpoints
        register_registry_endpoints(app)
    
    SEGURANÇA: Evita double-register
    """
    global _endpoints_registered
    
    if _endpoints_registered:
        print("⚠️ WINDI Template Registry endpoints already registered, skipping")
        return
    
    # Registrar middleware de request context
    @app.before_request
    def before_request():
        setup_request_context()
    
    # Registrar blueprints
    app.register_blueprint(registry_bp)
    app.register_blueprint(documents_bp)
    app.register_blueprint(audit_bp)
    
    _endpoints_registered = True
    print("✅ WINDI Template Registry endpoints registered (v1.2.0)")

# ============================================================================
# TEMPLATE DEFINITIONS v4.4
# ============================================================================

from template_definitions import list_templates, get_template, generate_template_html, get_template_css

@registry_bp.route('/templates/visual', methods=['GET'])
def get_visual_templates():
    """Lista templates visuais disponiveis."""
    lang = request.args.get('lang', 'de')
    return jsonify({"templates": list_templates(lang), "count": 3})

@registry_bp.route('/templates/visual/<template_id>', methods=['GET'])
def get_visual_template(template_id):
    """Retorna template visual por ID."""
    lang = request.args.get('lang', 'de')
    t = get_template(template_id)
    if not t:
        return jsonify({"error": "Template not found"}), 404
    return jsonify({"template": t, "html": generate_template_html(template_id, lang)})

@registry_bp.route('/templates/visual/<template_id>/css', methods=['GET'])
def get_visual_template_css(template_id):
    """Retorna CSS do template."""
    css = get_template_css(template_id)
    if not css:
        return jsonify({"error": "Template not found"}), 404
    from flask import Response
    return Response(css, mimetype='text/css')

# ============================================================================
# TEMPLATE PACKAGE VALIDATOR v4.5
# ============================================================================

from template_package_schema import TemplateValidator, TemplatePackage, InstitutionalBase, CorporateLayer, TemplateMetadata, BrandingConfig

@registry_bp.route('/templates/validate', methods=['POST'])
def validate_template_package():
    """Valida um Template Package antes de registro."""
    data = request.get_json() or {}
    try:
        pkg = TemplatePackage(
            template_id=data.get('template_id', ''),
            institutional_base=InstitutionalBase(
                base_id=data.get('institutional_base', {}).get('base_id', ''),
                mandatory_sections=data.get('institutional_base', {}).get('mandatory_sections', ["header", "subject_line", "body", "signature_block", "footer"])
            ),
            corporate_layer=CorporateLayer(
                organization_name=data.get('corporate_layer', {}).get('organization_name', ''),
                custom_css=data.get('corporate_layer', {}).get('custom_css', '')
            ),
            metadata=TemplateMetadata(
                created_by_org=data.get('metadata', {}).get('created_by_org', ''),
                reviewed_by_windi=data.get('metadata', {}).get('reviewed_by_windi', False),
                compliance_checked=data.get('metadata', {}).get('compliance_checked', False)
            )
        )
        validator = TemplateValidator()
        is_valid, issues = validator.validate(pkg)
        return jsonify({
            "valid": is_valid,
            "errors": [{"code": e.code, "message": e.message} for e in issues if e.severity == "error"],
            "warnings": [{"code": w.code, "message": w.message} for w in issues if w.severity == "warning"],
            "report": validator.generate_report(pkg)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 400

# ============================================================================
# STANDALONE TEST SERVER
# ============================================================================

if __name__ == "__main__":
    from flask import Flask
    
    app = Flask(__name__)
    register_registry_endpoints(app)
    
    @app.route('/health')
    def health():
        return jsonify({
            "status": "ok",
            "service": "WINDI Template Registry",
            "version": "1.2.0"
        })
    
    print("\n" + "="*60)
    print("WINDI Template Registry API v1.2.0 - Test Server")
    print("="*60)
    print("\n⚠️  Use gunicorn in production!")
    print("\nEndpoints:")
    print("  GET  /api/registry/tenants")
    print("  GET  /api/registry/templates")
    print("  POST /api/documents/generate")
    print("  etc.")
    print("\n")
    
    app.run(host='0.0.0.0', port=8086, debug=True)
