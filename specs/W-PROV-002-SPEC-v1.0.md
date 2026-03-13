# W-PROV-002 — Propagation Index
## Formal Specification v1.0
### WINDI Publishing House · Kempten, Bavaria · 2026-03-13
### SEALED: WINDI-SPEC-W-PROV-002-20260313

---

## 0. Preâmbulo Constitucional

> *"W-PROV-001 criou documentos que carregam prova.*
> *W-PROV-002 cria um ecossistema que observa a circulação da prova."*

Este agente não é um crawler da internet.
É um **observatório da circulação soberana de artefatos**.

**Princípio fundamental:** o sistema observa **artefatos**, nunca pessoas.

---

## 1. Identidade

| Campo            | Valor                                          |
|------------------|------------------------------------------------|
| ID               | W-PROV-002                                     |
| Nome             | Propagation Index                              |
| Versão           | 1.0.0                                          |
| Família          | W-PROV (Provenance)                            |
| Predecessor      | W-PROV-001 (Proof Injection)                   |
| Sucessor planejado | W-PROV-003 (Trust Constellations)            |
| Arquitetura      | Blueprint em Sandbox Core (:8091)              |
| Filesystem       | /opt/windi/agents/constitutional-agent/blueprints/propagation_blueprint.py |
| Base de dados    | /opt/windi/data/propagation_index.db           |

---

## 4. Invariantes Constitucionais Aplicáveis

| Invariante | Aplicação neste agente                         |
|------------|------------------------------------------------|
| I9         | Nunca decide autonomamente por crawling agressivo |
| I11        | Todos os eventos de propagação são selados no Ledger |
| C-PROV-001 | Sistema observa artefatos, nunca pessoas       |
| C-PROV-002 | Fingerprints são anônimos — sem dados pessoais |
| C-PROV-003 | Crawlers externos são opt-in e cirúrgicos      |

---

## 6. Schema da Base de Dados

### Tabela: propagation_events
```sql
CREATE TABLE propagation_events (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    ledger_anchor   TEXT NOT NULL,
    event_type      TEXT NOT NULL,
    source_type     TEXT NOT NULL,
    origin_domain   TEXT,
    country_hint    TEXT,
    verify_node     TEXT,
    client_fp       TEXT,
    timestamp       INTEGER NOT NULL,
    created_at      TEXT DEFAULT (datetime('now'))
);
```

### Tabela: artifact_stats
```sql
CREATE TABLE artifact_stats (
    ledger_anchor       TEXT PRIMARY KEY,
    total_verifications INTEGER DEFAULT 0,
    unique_domains      INTEGER DEFAULT 0,
    unique_countries    INTEGER DEFAULT 0,
    first_seen          TEXT,
    last_seen           TEXT,
    last_updated        TEXT DEFAULT (datetime('now'))
);
```

---

## 7. Endpoints da API

| Endpoint                          | Método | Descrição                    |
|-----------------------------------|--------|------------------------------|
| /propagation/event                | POST   | Registrar evento             |
| /propagation/artifact/{anchor}   | GET    | Stats de um artefato         |
| /propagation/network              | GET    | Mapa global                  |
| /propagation/feed                 | GET    | Feed recente                 |
| /propagation/health               | GET    | Health check                 |
| /propagation/dashboard            | GET    | Observatory UI               |

---

## 13. Plano de Deploy

- Fase 1: Hook no Verify Public
- Fase 2: Blueprint W-PROV-002
- Fase 3: Nginx + Ledger invariants
- Fase 4: Seed Collector
- Fase 5: Dashboard
- Fase 6: Ledger Milestones

---

*Sealed by Human Dragon — CGO, WINDI Publishing House*
*2026-03-13*
