-- ============================================================================
-- WINDI TEMPLATE REGISTRY - Schema SQLite v1.2.0 (Regulator Ready)
-- Multi-tenant, Versionado, Auditável, Compliance-Grade
-- "KI verarbeitet. Der Mensch entscheidet. WINDI garantiert."
-- ============================================================================
-- Atualizado: 27 JAN 2026
-- Versão: 1.2.0
-- ============================================================================

-- TENANTS (Clientes/Instituições)
CREATE TABLE IF NOT EXISTS tenants (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    display_name TEXT NOT NULL,
    country TEXT DEFAULT 'DE',
    region TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    active INTEGER DEFAULT 1,
    config_json TEXT DEFAULT '{}'
);

-- DEPARTMENTS (Abteilungen por Tenant)
CREATE TABLE IF NOT EXISTS departments (
    id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    code TEXT NOT NULL,
    name_de TEXT NOT NULL,
    name_en TEXT,
    name_pt TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    active INTEGER DEFAULT 1,
    FOREIGN KEY (tenant_id) REFERENCES tenants(id),
    UNIQUE(tenant_id, code)
);

-- DOCUMENT TYPES (Tipos de Documento)
CREATE TABLE IF NOT EXISTS doctypes (
    id TEXT PRIMARY KEY,
    code TEXT NOT NULL UNIQUE,
    name_de TEXT NOT NULL,
    name_en TEXT,
    name_pt TEXT,
    category TEXT DEFAULT 'general',
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- TEMPLATES (Versionados e Publicáveis)
CREATE TABLE IF NOT EXISTS templates (
    id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    department_id TEXT NOT NULL,
    doctype_id TEXT NOT NULL,
    version TEXT NOT NULL DEFAULT '1.0.0',
    status TEXT DEFAULT 'draft',  -- draft, review, published, archived
    
    -- Conteúdo do Template
    tiptap_json TEXT NOT NULL,
    
    -- Metadados
    title_de TEXT NOT NULL,
    title_en TEXT,
    legal_basis TEXT,
    disclosure_de TEXT,
    disclosure_en TEXT,
    
    -- Auditoria
    created_by TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    published_by TEXT,
    published_at TIMESTAMP,
    
    FOREIGN KEY (tenant_id) REFERENCES tenants(id),
    FOREIGN KEY (department_id) REFERENCES departments(id),
    FOREIGN KEY (doctype_id) REFERENCES doctypes(id),
    UNIQUE(tenant_id, department_id, doctype_id, version)
);

-- FIELD SPECIFICATIONS (Campos do Template)
CREATE TABLE IF NOT EXISTS template_fields (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    template_id TEXT NOT NULL,
    field_code TEXT NOT NULL,
    field_type TEXT NOT NULL,  -- string, date, richtext, list, number, boolean
    source TEXT NOT NULL,      -- system, user, ai, human_only
    required INTEGER DEFAULT 0,
    
    -- Labels multilíngue
    label_de TEXT NOT NULL,
    label_en TEXT,
    label_pt TEXT,
    
    -- Descrição/Ajuda
    help_de TEXT,
    help_en TEXT,
    
    -- Validação
    validation_regex TEXT,
    validation_min TEXT,
    validation_max TEXT,
    default_value TEXT,
    
    -- Ordenação visual
    display_order INTEGER DEFAULT 0,
    display_group TEXT,
    
    FOREIGN KEY (template_id) REFERENCES templates(id),
    UNIQUE(template_id, field_code)
);

-- HUMAN-ONLY CONSTRAINTS (Campos que só humano decide)
CREATE TABLE IF NOT EXISTS human_only_fields (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    template_id TEXT NOT NULL,
    field_code TEXT NOT NULL,
    reason_de TEXT NOT NULL,
    reason_en TEXT,
    requires_signature INTEGER DEFAULT 0,
    requires_justification INTEGER DEFAULT 0,
    FOREIGN KEY (template_id) REFERENCES templates(id),
    UNIQUE(template_id, field_code)
);

-- GOVERNANCE CONSTRAINTS (Regras que a IA deve seguir)
CREATE TABLE IF NOT EXISTS governance_rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    template_id TEXT NOT NULL,
    rule_code TEXT NOT NULL,
    rule_type TEXT NOT NULL,  -- prohibition, requirement, warning
    description_de TEXT NOT NULL,
    description_en TEXT,
    enforcement TEXT DEFAULT 'strict',  -- strict, advisory
    FOREIGN KEY (template_id) REFERENCES templates(id)
);

-- GENERATED DOCUMENTS (Instâncias geradas)
-- IMPORTANTE: Documentos com status='finalized' são IMUTÁVEIS (write-once)
CREATE TABLE IF NOT EXISTS documents (
    id TEXT PRIMARY KEY,
    template_id TEXT NOT NULL,
    template_version TEXT NOT NULL,
    
    -- Status do documento
    -- draft: em criação
    -- pending_human: aguardando campos human_only
    -- finalized: IMUTÁVEL, não pode ser alterado
    -- archived: arquivado
    status TEXT DEFAULT 'draft',
    
    -- Conteúdo preenchido
    content_json TEXT NOT NULL,
    content_html TEXT,
    content_pdf_path TEXT,
    
    -- Campos humanos preenchidos?
    human_fields_complete INTEGER DEFAULT 0,
    
    -- Integridade
    content_hash TEXT NOT NULL,
    windi_receipt TEXT,
    final_hash TEXT,  -- Hash após finalização (imutável)
    
    -- Metadados
    created_by TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    finalized_by TEXT,
    finalized_at TIMESTAMP,
    
    -- Dados de input (para auditoria)
    input_data_json TEXT,
    
    FOREIGN KEY (template_id) REFERENCES templates(id)
);

-- ============================================================================
-- TABELAS DE AUDITORIA (SEPARADAS PARA COMPLIANCE)
-- ============================================================================

-- AUDIT_LOG: Ações normais do sistema (CRUD, geração, finalização)
CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    request_id TEXT,  -- UUID para correlacionar múltiplas ações
    
    -- O que aconteceu
    action TEXT NOT NULL,
    entity_type TEXT NOT NULL,  -- template, document, tenant, department
    entity_id TEXT NOT NULL,
    
    -- Quem fez
    actor_type TEXT NOT NULL,  -- system, user, ai
    actor_id TEXT,
    
    -- Contexto
    details_json TEXT,
    ip_address TEXT,
    user_agent TEXT,
    session_id TEXT
);

-- SECURITY_EVENTS: Eventos de segurança (violações, tentativas não autorizadas)
-- Tabela separada para facilitar monitoramento e alertas
CREATE TABLE IF NOT EXISTS security_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    request_id TEXT,
    
    -- Classificação do evento
    event_type TEXT NOT NULL,  -- unauthorized_access, human_only_violation, rate_limit, template_confusion, etc.
    severity TEXT DEFAULT 'warning',  -- info, warning, critical
    
    -- Contexto da requisição
    endpoint TEXT,
    method TEXT,
    ip_address TEXT,
    user_agent TEXT,
    
    -- Detalhes
    details_json TEXT,
    
    -- Resolução (para gestão de incidentes)
    resolved INTEGER DEFAULT 0,
    resolved_by TEXT,
    resolved_at TIMESTAMP,
    resolution_notes TEXT
);

-- ============================================================================
-- ÍNDICES PARA PERFORMANCE E AUDITORIA
-- ============================================================================

-- Templates
CREATE INDEX IF NOT EXISTS idx_templates_tenant ON templates(tenant_id);
CREATE INDEX IF NOT EXISTS idx_templates_status ON templates(status);
CREATE INDEX IF NOT EXISTS idx_templates_lookup ON templates(tenant_id, department_id, doctype_id, status);

-- Documents
CREATE INDEX IF NOT EXISTS idx_documents_template ON documents(template_id);
CREATE INDEX IF NOT EXISTS idx_documents_status ON documents(status);
CREATE INDEX IF NOT EXISTS idx_documents_created ON documents(created_at);
CREATE INDEX IF NOT EXISTS idx_documents_finalized ON documents(finalized_at);

-- Audit Log (CRÍTICO para compliance - queries frequentes)
CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_log(timestamp);
CREATE INDEX IF NOT EXISTS idx_audit_entity ON audit_log(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_audit_entity_time ON audit_log(entity_type, entity_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_audit_actor ON audit_log(actor_type, actor_id);
CREATE INDEX IF NOT EXISTS idx_audit_action ON audit_log(action);
CREATE INDEX IF NOT EXISTS idx_audit_ip ON audit_log(ip_address);
CREATE INDEX IF NOT EXISTS idx_audit_request ON audit_log(request_id);

-- Security Events (CRÍTICO para monitoramento)
CREATE INDEX IF NOT EXISTS idx_security_timestamp ON security_events(timestamp);
CREATE INDEX IF NOT EXISTS idx_security_type ON security_events(event_type);
CREATE INDEX IF NOT EXISTS idx_security_severity ON security_events(severity);
CREATE INDEX IF NOT EXISTS idx_security_ip ON security_events(ip_address);
CREATE INDEX IF NOT EXISTS idx_security_unresolved ON security_events(resolved, timestamp);

-- ============================================================================
-- DADOS INICIAIS - Prefeitura de Kempten (Exemplo)
-- ============================================================================

-- Tenant: Stadt Kempten
INSERT OR IGNORE INTO tenants (id, name, display_name, region) VALUES 
('kempten', 'stadt_kempten', 'Stadt Kempten (Allgäu)', 'Bavaria');

-- Departments
INSERT OR IGNORE INTO departments (id, tenant_id, code, name_de, name_en) VALUES
('kempten_bauamt', 'kempten', 'bauamt', 'Bauamt', 'Building Authority'),
('kempten_ordnungsamt', 'kempten', 'ordnungsamt', 'Ordnungsamt', 'Public Order Office'),
('kempten_sozialamt', 'kempten', 'sozialamt', 'Sozialamt', 'Social Services'),
('kempten_finanzamt', 'kempten', 'finanzamt', 'Finanzamt', 'Finance Office'),
('kempten_standesamt', 'kempten', 'standesamt', 'Standesamt', 'Registry Office'),
('kempten_buergeramt', 'kempten', 'buergeramt', 'Bürgeramt', 'Citizens Office'),
('kempten_umweltamt', 'kempten', 'umweltamt', 'Umweltamt', 'Environmental Office');

-- Document Types
INSERT OR IGNORE INTO doctypes (id, code, name_de, name_en, category) VALUES
('bescheid_baugenehmigung', 'bescheid_baugenehmigung', 'Bescheid Baugenehmigung', 'Building Permit Decision', 'bescheid'),
('bescheid_ablehnung', 'bescheid_ablehnung', 'Ablehnungsbescheid', 'Rejection Notice', 'bescheid'),
('bescheid_gewerbe', 'bescheid_gewerbe', 'Gewerbebescheid', 'Business Permit', 'bescheid'),
('bescheid_sozialleistung', 'bescheid_sozialleistung', 'Sozialleistungsbescheid', 'Social Benefits Decision', 'bescheid'),
('bescheid_steuern', 'bescheid_steuern', 'Steuerbescheid', 'Tax Assessment', 'bescheid'),
('mitteilung', 'mitteilung', 'Amtliche Mitteilung', 'Official Notice', 'mitteilung'),
('bestaetigung', 'bestaetigung', 'Bestätigung', 'Confirmation', 'bestaetigung'),
('antrag_formular', 'antrag_formular', 'Antragsformular', 'Application Form', 'formular');

-- ============================================================================
-- VIEWS ÚTEIS PARA AUDITORIA
-- ============================================================================

-- View: Templates publicados por tenant
CREATE VIEW IF NOT EXISTS v_published_templates AS
SELECT 
    t.id,
    t.tenant_id,
    tn.display_name as tenant_name,
    d.code as department,
    d.name_de as department_name,
    dt.code as doctype,
    dt.name_de as doctype_name,
    t.version,
    t.title_de,
    t.published_at
FROM templates t
JOIN tenants tn ON t.tenant_id = tn.id
JOIN departments d ON t.department_id = d.id
JOIN doctypes dt ON t.doctype_id = dt.id
WHERE t.status = 'published';

-- View: Campos human-only por template
CREATE VIEW IF NOT EXISTS v_human_only_summary AS
SELECT 
    t.id as template_id,
    t.title_de,
    GROUP_CONCAT(hof.field_code, ', ') as human_only_fields,
    COUNT(hof.id) as human_only_count
FROM templates t
LEFT JOIN human_only_fields hof ON t.id = hof.template_id
GROUP BY t.id;

-- View: Eventos de segurança não resolvidos
CREATE VIEW IF NOT EXISTS v_unresolved_security AS
SELECT 
    id,
    timestamp,
    event_type,
    severity,
    endpoint,
    ip_address,
    details_json
FROM security_events
WHERE resolved = 0
ORDER BY 
    CASE severity 
        WHEN 'critical' THEN 1 
        WHEN 'warning' THEN 2 
        ELSE 3 
    END,
    timestamp DESC;

-- View: Documentos finalizados (imutáveis)
CREATE VIEW IF NOT EXISTS v_finalized_documents AS
SELECT 
    d.id,
    d.template_id,
    d.template_version,
    d.windi_receipt,
    d.final_hash,
    d.finalized_by,
    d.finalized_at,
    t.title_de as template_title
FROM documents d
JOIN templates t ON d.template_id = t.id
WHERE d.status = 'finalized';

-- ============================================================================
-- TRIGGERS PARA IMUTABILIDADE
-- ============================================================================

-- Trigger: Bloquear UPDATE em documentos finalizados
CREATE TRIGGER IF NOT EXISTS tr_document_immutable_update
BEFORE UPDATE ON documents
WHEN OLD.status = 'finalized'
BEGIN
    SELECT RAISE(ABORT, 'GOVERNANCE VIOLATION: Finalized documents are immutable (write-once). Cannot modify document with status=finalized.');
END;

-- Trigger: Bloquear DELETE em documentos finalizados
CREATE TRIGGER IF NOT EXISTS tr_document_immutable_delete
BEFORE DELETE ON documents
WHEN OLD.status = 'finalized'
BEGIN
    SELECT RAISE(ABORT, 'GOVERNANCE VIOLATION: Finalized documents are immutable. Cannot delete document with status=finalized.');
END;

-- Trigger: Bloquear UPDATE em templates publicados
CREATE TRIGGER IF NOT EXISTS tr_template_immutable_update
BEFORE UPDATE ON templates
WHEN OLD.status = 'published' AND NEW.status != 'archived'
BEGIN
    SELECT RAISE(ABORT, 'GOVERNANCE VIOLATION: Published templates are immutable. Create a new version instead.');
END;
