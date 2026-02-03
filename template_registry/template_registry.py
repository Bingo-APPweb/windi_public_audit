#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WINDI Template Registry - Core Module v1.2.0 (Regulator Ready)
===============================================================
Multi-tenant, Versionado, Auditável, Compliance-Grade
"KI verarbeitet. Der Mensch entscheidet. WINDI garantiert."

Versão: 1.2.0
Atualizado: 27 JAN 2026

Melhorias v1.2.0:
- Tabelas separadas: audit_log (ações) vs security_events (violações)
- Função log_event() centralizada
- Documentos finalizados são imutáveis (write-once via triggers SQL)
- Proteção contra template confusion (validação tenant)
- Request ID para correlação de logs
"""

import sqlite3
import json
import hashlib
import uuid
import os
from datetime import datetime
from typing import Optional, Dict, List, Any
from pathlib import Path

# ============================================================================
# CONFIGURAÇÃO
# ============================================================================

DEFAULT_DB_PATH = os.environ.get(
    'WINDI_DB_PATH', 
    '/opt/windi/data/template_registry.db'
)
SCHEMA_PATH = os.environ.get(
    'WINDI_SCHEMA_PATH',
    '/opt/windi/templates/schema.sql'
)

VERSION = "1.2.0"

# ============================================================================
# TEMPLATE REGISTRY CLASS
# ============================================================================

class TemplateRegistry:
    """
    Gerencia templates documentais com governança WINDI.
    
    Princípios:
    - Templates são versionados e auditáveis
    - Templates publicados são IMUTÁVEIS
    - Campos human_only nunca são preenchidos por IA
    - Documentos finalizados são IMUTÁVEIS (write-once)
    - Toda operação é registrada no audit_log
    - Eventos de segurança vão para tabela separada
    """
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or DEFAULT_DB_PATH
        self._ensure_db()
    
    def _ensure_db(self):
        """Garante que o banco existe com o schema correto"""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        schema_file = Path(SCHEMA_PATH)
        if schema_file.exists():
            with open(schema_file, 'r') as f:
                schema_sql = f.read()
            with sqlite3.connect(self.db_path) as conn:
                conn.executescript(schema_sql)
    
    def _get_conn(self) -> sqlite3.Connection:
        """Retorna conexão com row_factory para dict"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    # ========================================================================
    # LOGGING CENTRALIZADO
    # ========================================================================
    
    def log_event(self, 
                  action: str,
                  entity_type: str,
                  entity_id: str,
                  actor_type: str = "system",
                  actor_id: str = None,
                  details: dict = None,
                  ip_address: str = None,
                  user_agent: str = None,
                  request_id: str = None,
                  conn: sqlite3.Connection = None):
        """
        Registra evento no audit_log.
        
        Args:
            action: Ação realizada (document_generated, template_published, etc.)
            entity_type: Tipo de entidade (template, document, tenant)
            entity_id: ID da entidade
            actor_type: Tipo de ator (system, user, ai)
            actor_id: ID do ator (email, user_id, etc.)
            details: Detalhes adicionais em JSON
            ip_address: IP do requisitante
            user_agent: User-Agent do requisitante
            request_id: UUID para correlacionar múltiplas ações
            conn: Conexão existente (para transações)
        """
        should_close = False
        if conn is None:
            conn = self._get_conn()
            should_close = True
        
        try:
            conn.execute("""
                INSERT INTO audit_log 
                (request_id, action, entity_type, entity_id, actor_type, actor_id, 
                 details_json, ip_address, user_agent)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                request_id or str(uuid.uuid4()),
                action,
                entity_type,
                entity_id,
                actor_type,
                actor_id,
                json.dumps(details) if details else None,
                ip_address,
                user_agent
            ))
            
            if should_close:
                conn.commit()
        finally:
            if should_close:
                conn.close()
    
    def log_security_event(self,
                           event_type: str,
                           severity: str = "warning",
                           endpoint: str = None,
                           method: str = None,
                           ip_address: str = None,
                           user_agent: str = None,
                           details: dict = None,
                           request_id: str = None):
        """
        Registra evento de segurança em tabela separada.
        
        Args:
            event_type: Tipo do evento (unauthorized_access, human_only_violation, etc.)
            severity: Severidade (info, warning, critical)
            endpoint: Endpoint acessado
            method: Método HTTP
            ip_address: IP do requisitante
            user_agent: User-Agent
            details: Detalhes adicionais
            request_id: UUID para correlação
        """
        with self._get_conn() as conn:
            conn.execute("""
                INSERT INTO security_events
                (request_id, event_type, severity, endpoint, method, 
                 ip_address, user_agent, details_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                request_id or str(uuid.uuid4()),
                event_type,
                severity,
                endpoint,
                method,
                ip_address,
                user_agent,
                json.dumps(details) if details else None
            ))
            conn.commit()
    
    # Aliases para compatibilidade
    def _audit(self, conn, action, entity_type, entity_id, 
               actor_type="system", actor_id=None, details=None, ip_address=None):
        """Alias para compatibilidade com código existente"""
        self.log_event(
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            actor_type=actor_type,
            actor_id=actor_id,
            details=details,
            ip_address=ip_address,
            conn=conn
        )
    
    def _audit_security_event(self, event_type, endpoint=None, ip_address=None, details=None):
        """Alias para compatibilidade"""
        self.log_security_event(
            event_type=event_type,
            endpoint=endpoint,
            ip_address=ip_address,
            details=details
        )
    
    # ========================================================================
    # TENANT MANAGEMENT
    # ========================================================================
    
    def create_tenant(self, tenant_id: str, name: str, display_name: str,
                      region: str = None, config: dict = None,
                      created_by: str = None, request_context: dict = None) -> dict:
        """Cria novo tenant (cliente/instituição)"""
        ctx = request_context or {}
        
        with self._get_conn() as conn:
            conn.execute("""
                INSERT INTO tenants (id, name, display_name, region, config_json)
                VALUES (?, ?, ?, ?, ?)
            """, (tenant_id, name, display_name, region, 
                  json.dumps(config) if config else '{}'))
            
            self.log_event(
                action="tenant_created",
                entity_type="tenant",
                entity_id=tenant_id,
                actor_type="user" if created_by else "system",
                actor_id=created_by,
                details={"name": name, "display_name": display_name, "region": region},
                ip_address=ctx.get('ip_address'),
                request_id=ctx.get('request_id'),
                conn=conn
            )
            conn.commit()
        
        return {"id": tenant_id, "name": name, "display_name": display_name}
    
    def get_tenant(self, tenant_id: str) -> Optional[dict]:
        """Retorna dados do tenant"""
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT * FROM tenants WHERE id = ? AND active = 1", 
                (tenant_id,)
            ).fetchone()
            return dict(row) if row else None
    
    def list_tenants(self) -> List[dict]:
        """Lista todos os tenants ativos"""
        with self._get_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM tenants WHERE active = 1 ORDER BY display_name"
            ).fetchall()
            return [dict(row) for row in rows]
    
    # ========================================================================
    # DEPARTMENT MANAGEMENT
    # ========================================================================
    
    def create_department(self, tenant_id: str, code: str, name_de: str,
                          name_en: str = None, name_pt: str = None) -> dict:
        """Cria departamento para um tenant"""
        dept_id = f"{tenant_id}_{code}"
        with self._get_conn() as conn:
            conn.execute("""
                INSERT INTO departments (id, tenant_id, code, name_de, name_en, name_pt)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (dept_id, tenant_id, code, name_de, name_en, name_pt))
            
            self.log_event(
                action="department_created",
                entity_type="department",
                entity_id=dept_id,
                details={"tenant": tenant_id, "code": code},
                conn=conn
            )
            conn.commit()
        
        return {"id": dept_id, "tenant_id": tenant_id, "code": code, "name_de": name_de}
    
    def list_departments(self, tenant_id: str) -> List[dict]:
        """Lista departamentos de um tenant"""
        with self._get_conn() as conn:
            rows = conn.execute("""
                SELECT * FROM departments 
                WHERE tenant_id = ? AND active = 1 
                ORDER BY name_de
            """, (tenant_id,)).fetchall()
            return [dict(row) for row in rows]
    
    # ========================================================================
    # TEMPLATE MANAGEMENT
    # ========================================================================
    
    def create_template(self, tenant_id: str, department_code: str, 
                        doctype_code: str, title_de: str, tiptap_json: dict,
                        fields: List[dict], human_only: List[dict] = None,
                        governance_rules: List[dict] = None,
                        version: str = "1.0.0", created_by: str = None,
                        title_en: str = None, legal_basis: str = None,
                        disclosure_de: str = None, disclosure_en: str = None,
                        request_context: dict = None) -> dict:
        """
        Cria novo template (status: draft)
        """
        ctx = request_context or {}
        template_id = f"{tenant_id}_{department_code}_{doctype_code}_v{version.replace('.', '_')}"
        department_id = f"{tenant_id}_{department_code}"
        
        with self._get_conn() as conn:
            # Insere template
            conn.execute("""
                INSERT INTO templates (
                    id, tenant_id, department_id, doctype_id, version, status,
                    tiptap_json, title_de, title_en, legal_basis,
                    disclosure_de, disclosure_en, created_by
                ) VALUES (?, ?, ?, ?, ?, 'draft', ?, ?, ?, ?, ?, ?, ?)
            """, (template_id, tenant_id, department_id, doctype_code, version,
                  json.dumps(tiptap_json), title_de, title_en, legal_basis,
                  disclosure_de, disclosure_en, created_by))
            
            # Insere campos
            for i, field in enumerate(fields):
                conn.execute("""
                    INSERT INTO template_fields (
                        template_id, field_code, field_type, source, required,
                        label_de, label_en, help_de, help_en,
                        validation_regex, default_value, display_order, display_group
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    template_id,
                    field['code'],
                    field.get('type', 'string'),
                    field.get('source', 'user'),
                    1 if field.get('required', False) else 0,
                    field['label_de'],
                    field.get('label_en'),
                    field.get('help_de'),
                    field.get('help_en'),
                    field.get('validation'),
                    field.get('default'),
                    field.get('order', i),
                    field.get('group')
                ))
            
            # Insere campos human_only
            if human_only:
                for hof in human_only:
                    conn.execute("""
                        INSERT INTO human_only_fields (
                            template_id, field_code, reason_de, reason_en,
                            requires_signature, requires_justification
                        ) VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        template_id,
                        hof['field_code'],
                        hof['reason_de'],
                        hof.get('reason_en'),
                        1 if hof.get('requires_signature', False) else 0,
                        1 if hof.get('requires_justification', False) else 0
                    ))
            
            # Insere regras de governança
            if governance_rules:
                for rule in governance_rules:
                    conn.execute("""
                        INSERT INTO governance_rules (
                            template_id, rule_code, rule_type, 
                            description_de, description_en, enforcement
                        ) VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        template_id,
                        rule['code'],
                        rule.get('type', 'requirement'),
                        rule['description_de'],
                        rule.get('description_en'),
                        rule.get('enforcement', 'strict')
                    ))
            
            self.log_event(
                action="template_created",
                entity_type="template",
                entity_id=template_id,
                actor_type="user" if created_by else "system",
                actor_id=created_by,
                details={
                    "doctype": doctype_code,
                    "version": version,
                    "fields_count": len(fields),
                    "human_only_count": len(human_only) if human_only else 0,
                    "governance_rules_count": len(governance_rules) if governance_rules else 0
                },
                ip_address=ctx.get('ip_address'),
                request_id=ctx.get('request_id'),
                conn=conn
            )
            conn.commit()
        
        return self.get_template(template_id)
    
    def get_template(self, template_id: str) -> Optional[dict]:
        """Retorna template completo com campos e regras"""
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT * FROM templates WHERE id = ?", 
                (template_id,)
            ).fetchone()
            
            if not row:
                return None
            
            template = dict(row)
            template['tiptap_json'] = json.loads(template['tiptap_json'])
            
            # Campos
            fields = conn.execute(
                "SELECT * FROM template_fields WHERE template_id = ? ORDER BY display_order",
                (template_id,)
            ).fetchall()
            template['fields'] = [dict(f) for f in fields]
            
            # Human-only
            human_only = conn.execute(
                "SELECT * FROM human_only_fields WHERE template_id = ?",
                (template_id,)
            ).fetchall()
            template['human_only'] = [dict(h) for h in human_only]
            
            # Governance rules
            rules = conn.execute(
                "SELECT * FROM governance_rules WHERE template_id = ?",
                (template_id,)
            ).fetchall()
            template['governance_rules'] = [dict(r) for r in rules]
            
            return template
    
    def publish_template(self, template_id: str, published_by: str = None,
                         request_context: dict = None) -> dict:
        """
        Publica template (draft -> published)
        
        GOVERNANÇA: Templates publicados são IMUTÁVEIS.
        Para alterações, criar nova versão.
        """
        ctx = request_context or {}
        
        current = self.get_template(template_id)
        if not current:
            raise ValueError(f"Template não encontrado: {template_id}")
        
        if current['status'] == 'published':
            raise ValueError(
                f"Template '{template_id}' já está publicado e é IMUTÁVEL. "
                f"Para alterações, crie uma nova versão do template."
            )
        
        if current['status'] == 'archived':
            raise ValueError(
                f"Template '{template_id}' está arquivado e não pode ser republicado."
            )
        
        with self._get_conn() as conn:
            now = datetime.utcnow().isoformat()
            conn.execute("""
                UPDATE templates 
                SET status = 'published', published_by = ?, published_at = ?
                WHERE id = ? AND status = 'draft'
            """, (published_by, now, template_id))
            
            self.log_event(
                action="template_published",
                entity_type="template",
                entity_id=template_id,
                actor_type="user" if published_by else "system",
                actor_id=published_by,
                details={
                    "version": current['version'],
                    "governance_note": "Template is now immutable"
                },
                ip_address=ctx.get('ip_address'),
                request_id=ctx.get('request_id'),
                conn=conn
            )
            conn.commit()
        
        return self.get_template(template_id)
    
    def find_template(self, tenant_id: str, department_code: str, 
                      doctype_code: str, version: str = None) -> Optional[dict]:
        """
        Encontra template publicado.
        
        SEGURANÇA: Valida que o template pertence ao tenant solicitado
        para prevenir "template confusion attacks".
        """
        with self._get_conn() as conn:
            department_id = f"{tenant_id}_{department_code}"
            
            if version:
                row = conn.execute("""
                    SELECT id FROM templates 
                    WHERE tenant_id = ? AND department_id = ? AND doctype_id = ?
                    AND version = ? AND status = 'published'
                """, (tenant_id, department_id, doctype_code, version)).fetchone()
            else:
                row = conn.execute("""
                    SELECT id FROM templates 
                    WHERE tenant_id = ? AND department_id = ? AND doctype_id = ?
                    AND status = 'published'
                    ORDER BY published_at DESC LIMIT 1
                """, (tenant_id, department_id, doctype_code)).fetchone()
            
            if row:
                template = self.get_template(row['id'])
                
                # SEGURANÇA: Validação adicional contra template confusion
                if template and template['tenant_id'] != tenant_id:
                    self.log_security_event(
                        event_type="template_confusion_detected",
                        severity="critical",
                        details={
                            "requested_tenant": tenant_id,
                            "template_tenant": template['tenant_id'],
                            "template_id": template['id']
                        }
                    )
                    return None
                
                return template
            return None
    
    def list_templates(self, tenant_id: str = None, status: str = None) -> List[dict]:
        """Lista templates com filtros opcionais"""
        with self._get_conn() as conn:
            query = "SELECT * FROM v_published_templates WHERE 1=1"
            params = []
            
            if tenant_id:
                query += " AND tenant_id = ?"
                params.append(tenant_id)
            
            query += " ORDER BY tenant_name, department_name, doctype_name"
            
            rows = conn.execute(query, params).fetchall()
            return [dict(row) for row in rows]
    
    # ========================================================================
    # DOCUMENT GENERATION
    # ========================================================================
    
    def generate_document(self, tenant_id: str, department_code: str,
                          doctype_code: str, inputs: dict,
                          created_by: str = None, language: str = "de",
                          request_context: dict = None) -> dict:
        """
        Gera documento a partir de template.
        
        GOVERNANÇA: 
        - Campos human_only NÃO são preenchidos
        - Validação de bloqueio deve ser feita na camada de API
        - Template deve pertencer ao tenant solicitado
        
        Returns:
            Dict com document_id, status, content_json, human_only_missing, receipt
        """
        ctx = request_context or {}
        request_id = ctx.get('request_id', str(uuid.uuid4()))
        
        # Encontra template (já valida tenant)
        template = self.find_template(tenant_id, department_code, doctype_code)
        if not template:
            raise ValueError(f"Template não encontrado: {tenant_id}/{department_code}/{doctype_code}")
        
        # Identifica campos human_only
        human_only_codes = {h['field_code'] for h in template['human_only']}
        
        # Preenche campos permitidos
        filled_content = self._fill_template(template, inputs, human_only_codes)
        
        # Campos human_only faltantes
        human_only_missing = []
        for hof in template['human_only']:
            if hof['field_code'] not in inputs:
                human_only_missing.append({
                    'field_code': hof['field_code'],
                    'reason_de': hof['reason_de'],
                    'reason_en': hof.get('reason_en'),
                    'requires_signature': bool(hof.get('requires_signature')),
                    'requires_justification': bool(hof.get('requires_justification'))
                })
        
        # Gera hash de integridade
        content_str = json.dumps(filled_content, sort_keys=True)
        content_hash = hashlib.sha256(content_str.encode()).hexdigest()[:16].upper()
        
        # Cria documento no banco
        doc_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        
        receipt = {
            "document_id": doc_id,
            "template_id": template['id'],
            "template_version": template['version'],
            "content_hash": content_hash,
            "generated_at": now,
            "human_fields_pending": len(human_only_missing),
            "generator": f"windi_template_registry_v{VERSION}"
        }
        
        windi_receipt = f"WINDI-RECEIPT-{content_hash}-{now[:10].replace('-','')}"
        
        with self._get_conn() as conn:
            conn.execute("""
                INSERT INTO documents (
                    id, template_id, template_version, status,
                    content_json, content_hash, windi_receipt,
                    created_by, input_data_json, human_fields_complete
                ) VALUES (?, ?, ?, 'pending_human', ?, ?, ?, ?, ?, 0)
            """, (
                doc_id, template['id'], template['version'],
                json.dumps(filled_content), content_hash, windi_receipt,
                created_by, json.dumps(inputs)
            ))
            
            self.log_event(
                action="document_generated",
                entity_type="document",
                entity_id=doc_id,
                actor_type="ai",
                details={
                    "template_id": template['id'],
                    "template_version": template['version'],
                    "content_hash": content_hash,
                    "human_only_pending": len(human_only_missing),
                    "human_only_fields": [h['field_code'] for h in human_only_missing],
                    "input_fields_provided": list(inputs.keys()),
                    "created_by": created_by,
                    "language": language
                },
                ip_address=ctx.get('ip_address'),
                request_id=request_id,
                conn=conn
            )
            conn.commit()
        
        return {
            "document_id": doc_id,
            "status": "pending_human" if human_only_missing else "ready",
            "content_json": filled_content,
            "human_only_missing": human_only_missing,
            "receipt": receipt,
            "windi_receipt": windi_receipt,
            "template": {
                "id": template['id'],
                "title_de": template['title_de'],
                "version": template['version'],
                "disclosure_de": template.get('disclosure_de')
            }
        }
    
    def _fill_template(self, template: dict, inputs: dict, 
                       human_only_codes: set) -> dict:
        """Preenche template Tiptap com inputs."""
        tiptap = json.loads(json.dumps(template['tiptap_json']))  # Deep copy
        
        def replace_placeholders(node):
            if isinstance(node, dict):
                if node.get('type') == 'text' and 'text' in node:
                    text = node['text']
                    for field in template['fields']:
                        code = field['field_code']
                        placeholder = f"{{{{{code}}}}}"
                        
                        if placeholder in text:
                            if code in human_only_codes:
                                replacement = f"[NUR MENSCH: {field['label_de']}]"
                            elif code in inputs:
                                replacement = str(inputs[code])
                            else:
                                replacement = f"[{field['label_de']}]"
                            
                            text = text.replace(placeholder, replacement)
                    node['text'] = text
                
                if 'content' in node:
                    for child in node['content']:
                        replace_placeholders(child)
            
            return node
        
        return replace_placeholders(tiptap)
    
    def fill_human_field(self, document_id: str, field_code: str, 
                         value: Any, filled_by: str,
                         justification: str = None,
                         request_context: dict = None) -> dict:
        """
        Preenche campo human_only.
        
        GOVERNANÇA: Documento não pode estar finalizado.
        """
        ctx = request_context or {}
        
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT * FROM documents WHERE id = ?",
                (document_id,)
            ).fetchone()
            
            if not row:
                raise ValueError(f"Documento não encontrado: {document_id}")
            
            doc = dict(row)
            
            # GOVERNANÇA: Verificar se documento já está finalizado
            if doc['status'] == 'finalized':
                self.log_security_event(
                    event_type="finalized_document_modification_attempt",
                    severity="warning",
                    details={
                        "document_id": document_id,
                        "field_code": field_code,
                        "attempted_by": filled_by
                    },
                    ip_address=ctx.get('ip_address'),
                    request_id=ctx.get('request_id')
                )
                raise ValueError(
                    f"Documento '{document_id}' está finalizado e é IMUTÁVEL. "
                    f"Não é possível alterar campos."
                )
            
            content = json.loads(doc['content_json'])
            
            # Verifica se campo é human_only
            hof = conn.execute("""
                SELECT * FROM human_only_fields 
                WHERE template_id = ? AND field_code = ?
            """, (doc['template_id'], field_code)).fetchone()
            
            if not hof:
                raise ValueError(f"Campo não é human_only: {field_code}")
            
            if hof['requires_justification'] and not justification:
                raise ValueError(f"Campo {field_code} requer justificativa")
            
            # Atualiza conteúdo
            content_str = json.dumps(content)
            template = self.get_template(doc['template_id'])
            
            for field in template['fields']:
                if field['field_code'] == field_code:
                    old_marker = f"[NUR MENSCH: {field['label_de']}]"
                    content_str = content_str.replace(old_marker, str(value))
                    break
            
            content = json.loads(content_str)
            
            # Recalcula hash
            new_hash = hashlib.sha256(
                json.dumps(content, sort_keys=True).encode()
            ).hexdigest()[:16].upper()
            
            conn.execute("""
                UPDATE documents 
                SET content_json = ?, content_hash = ?
                WHERE id = ?
            """, (json.dumps(content), new_hash, document_id))
            
            self.log_event(
                action="human_field_filled",
                entity_type="document",
                entity_id=document_id,
                actor_type="user",
                actor_id=filled_by,
                details={
                    "field_code": field_code,
                    "justification": justification,
                    "new_hash": new_hash
                },
                ip_address=ctx.get('ip_address'),
                request_id=ctx.get('request_id'),
                conn=conn
            )
            conn.commit()
        
        return {"success": True, "new_hash": new_hash}
    
    def finalize_document(self, document_id: str, finalized_by: str,
                          request_context: dict = None) -> dict:
        """
        Finaliza documento após todos os campos human_only preenchidos.
        
        GOVERNANÇA: Documentos finalizados são IMUTÁVEIS (write-once).
        O trigger SQL impede qualquer modificação posterior.
        """
        ctx = request_context or {}
        
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT * FROM documents WHERE id = ?",
                (document_id,)
            ).fetchone()
            
            if not row:
                raise ValueError(f"Documento não encontrado: {document_id}")
            
            doc = dict(row)
            
            if doc['status'] == 'finalized':
                raise ValueError(f"Documento '{document_id}' já está finalizado.")
            
            # Verifica se tem campos pendentes
            content = json.loads(doc['content_json'])
            if "[NUR MENSCH:" in json.dumps(content):
                raise ValueError("Ainda há campos NUR MENSCH pendentes")
            
            now = datetime.utcnow().isoformat()
            
            # Hash final (imutável)
            final_hash = hashlib.sha256(
                json.dumps(content, sort_keys=True).encode()
            ).hexdigest().upper()
            
            conn.execute("""
                UPDATE documents 
                SET status = 'finalized', 
                    human_fields_complete = 1,
                    final_hash = ?,
                    finalized_by = ?, 
                    finalized_at = ?
                WHERE id = ?
            """, (final_hash, finalized_by, now, document_id))
            
            self.log_event(
                action="document_finalized",
                entity_type="document",
                entity_id=document_id,
                actor_type="user",
                actor_id=finalized_by,
                details={
                    "final_hash": final_hash,
                    "governance_note": "Document is now immutable (write-once)"
                },
                ip_address=ctx.get('ip_address'),
                request_id=ctx.get('request_id'),
                conn=conn
            )
            conn.commit()
        
        return {
            "success": True, 
            "finalized_at": now,
            "final_hash": final_hash,
            "governance_note": "Document is now immutable"
        }
    
    # ========================================================================
    # AUDIT & COMPLIANCE
    # ========================================================================
    
    def get_audit_trail(self, entity_type: str, entity_id: str) -> List[dict]:
        """Retorna trilha de auditoria de uma entidade"""
        with self._get_conn() as conn:
            rows = conn.execute("""
                SELECT * FROM audit_log 
                WHERE entity_type = ? AND entity_id = ?
                ORDER BY timestamp DESC
            """, (entity_type, entity_id)).fetchall()
            return [dict(row) for row in rows]
    
    def get_security_events(self, 
                            event_type: str = None,
                            severity: str = None,
                            unresolved_only: bool = False,
                            limit: int = 100) -> List[dict]:
        """Retorna eventos de segurança com filtros"""
        with self._get_conn() as conn:
            query = "SELECT * FROM security_events WHERE 1=1"
            params = []
            
            if event_type:
                query += " AND event_type = ?"
                params.append(event_type)
            
            if severity:
                query += " AND severity = ?"
                params.append(severity)
            
            if unresolved_only:
                query += " AND resolved = 0"
            
            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
            
            rows = conn.execute(query, params).fetchall()
            return [dict(row) for row in rows]
    
    def get_governance_report(self, template_id: str) -> dict:
        """Gera relatório de governança do template"""
        template = self.get_template(template_id)
        if not template:
            return None
        
        return {
            "template_id": template_id,
            "title": template['title_de'],
            "version": template['version'],
            "total_fields": len(template['fields']),
            "ai_fillable_fields": len([f for f in template['fields'] 
                                       if f['source'] in ('ai', 'system')]),
            "user_input_fields": len([f for f in template['fields'] 
                                      if f['source'] == 'user']),
            "human_only_fields": len(template['human_only']),
            "human_only_list": [h['field_code'] for h in template['human_only']],
            "governance_rules": len(template['governance_rules']),
            "legal_basis": template.get('legal_basis'),
            "disclosure": template.get('disclosure_de')
        }


# ============================================================================
# EXEMPLO DE USO
# ============================================================================

if __name__ == "__main__":
    print(f"WINDI Template Registry v{VERSION}")
    print("=" * 50)
    
    registry = TemplateRegistry("/tmp/test_registry.db")
    
    tenants = registry.list_tenants()
    print(f"Tenants: {[t['display_name'] for t in tenants]}")
    
    if tenants:
        depts = registry.list_departments(tenants[0]['id'])
        print(f"Departments: {[d['name_de'] for d in depts]}")
    
    print("\n✅ Template Registry funcionando!")
