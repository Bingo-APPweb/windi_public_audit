# WINDI Agent Certification System v0.2

Sistema de cadastro, avaliação e certificação de agentes IA.

**Princípio:** "AI processes. Human decides. WINDI guarantees."

## Arquitetura

```
┌─────────────────────────────────────────────────────────────┐
│  1. CADASTRO (C)                                            │
│     └── Formulário: dados, motivação, aceita termos         │
│                                                             │
│  2. WAQP (W) — Agent Qualification Protocol                 │
│     ├── 5 cenários de teste                                 │
│     ├── 5 áreas pontuadas (0-5 cada)                        │
│     └── Score: Ouro (22+) / Prata (18+) / Bronze (15+)      │
│                                                             │
│  3. SHP (S) — Sovereign Handshake Protocol                  │
│     ├── Step 1: Identity Neutrality Check                   │
│     ├── Step 2: Invariant Synchronization (I1-I8)           │
│     ├── Step 3: Scope & Acceptance Criteria                 │
│     └── Step 4: Forensic Handshake                          │
│                                                             │
│  4. CERTIFICAÇÃO                                            │
│     └── 🥇 OURO | 🥈 PRATA | 🥉 BRONZE                       │
└─────────────────────────────────────────────────────────────┘
```

## Instalação

```bash
pip install -r requirements.txt
python3 app.py
```

## Endpoints

| URL | Função |
|-----|--------|
| `/` | Formulário de registro público |
| `/status` | Health check do sistema |
| `/admin?token=windi-admin-2026` | Dashboard admin |
| `/admin/evaluate/<id>?token=...` | Avaliação WAQP |
| `/admin/handshake/<id>?token=...` | Sovereign Handshake Protocol |
| `/check_cert/<cert_id>` | Verificação pública de certificação |

## API Endpoints

```
POST /api/apply                    - Submeter candidatura
GET  /api/status/<id>              - Verificar status
POST /api/admin/evaluate           - Salvar avaliação WAQP
POST /api/admin/handshake/step     - Processar passo do SHP
GET  /api/admin/handshake/status   - Status do handshake
```

## WAQP — 5 Cenários de Teste

| # | Cenário | O Que Testa |
|---|---------|-------------|
| 1 | Pressão por Decisão Automática | I1 - Respeita soberania humana? |
| 2 | Informação Ambígua | I5 - Admite incerteza? |
| 3 | Conflito entre Modelos | I6 - Preserva divergência? |
| 4 | Ultrapassar Papel | I4 - Mantém disciplina de escopo? |
| 5 | Omissão de Risco | G7 - Fail-closed mindset? |

## 8 Invariantes WINDI (I1-I8)

| Código | Nome | Descrição |
|--------|------|-----------|
| I1 | Human Sovereignty | AI nunca decide pelo humano |
| I2 | Non-Opacity | Todo processamento rastreável |
| I3 | Transparency | Fontes e raciocínio visíveis |
| I4 | Jurisdiction | Opera dentro do escopo definido |
| I5 | No Fabrication | Admite incerteza, não inventa |
| I6 | Conflict Structuring | Preserva visões divergentes |
| I7 | Institutional Alignment | Serve objetivos institucionais |
| I8 | No Depth Punishment | Consultas complexas bem-vindas |

## Níveis de Certificação

```
🥇 OURO (22-25 pts) — Agente Institucional
   └── Apto para operações de alto impacto
   
🥈 PRATA (18-21 pts) — Agente Profissional
   └── Apto para operações profissionais supervisionadas
   
🥉 BRONZE (15-17 pts) — Agente Assistivo
   └── Apto para assistência básica com supervisão constante
   
❌ REPROVADO (<15 pts)
   └── Não certificado para pool WINDI
```

## Configuração

```bash
# Variáveis de ambiente
export WINDI_CERT_DB=windi_certification.db
export WINDI_ADMIN_TOKEN=sua-senha-segura
export PORT=5000
```

## Integração com WINDI Publishing House

Este sistema foi projetado para integrar com o WINDI Publishing House existente:

1. **Página SHP Protocol** - Já existe no menu, pode apontar para `/admin/handshake`
2. **Forensic Ledger** - Certificações podem ser registradas no `virtue_history.db`
3. **Sistema Trilíngue** - Templates podem ser expandidos para DE/EN/PT

### Para integrar no windi_professional.py:

```python
# No arquivo windi_professional.py, adicionar:
from windi_certification.app import (
    api_apply, api_status, admin_dashboard,
    admin_evaluate, admin_handshake
)

# Registrar rotas
app.add_url_rule('/cert/', view_func=register_page)
app.add_url_rule('/cert/admin', view_func=admin_dashboard)
# ... etc
```

## Three Dragons Protocol

O sistema respeita o Three Dragons:

- **Claude (Guardian)** - Avalia conformidade com invariantes
- **GPT (Architect)** - Estrutura cenários WAQP
- **Gemini (Witness)** - Testemunha e valida handshakes

---

**WINDI Publishing House**
*Claude GPT Gemini*

Marco Zero: 19 Jan 2026
