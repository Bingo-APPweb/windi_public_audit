# §267-ERRATA-VERIFY-PORT

**Status:** SEALED  
**Data:** 2026-05-15  
**Seal State:** Berçário  
**Protocol:** pre-G4 precedent  
**Invariants:** I9, I11  
**Language:** PT (DE/EN derivadas pós-seal)

---

## 1. Preâmbulo Constitucional

Esta Errata é emitida sob autorização explícita do Human Dragon (I9) na sessão de 2026-05-15. Constitui precedente pre-G4: o G4 Errata Protocol está deferido para §247+, portanto esta Errata opera sob schema provisional. Quando G4 for selado, esta Errata será reconciliada com o protocolo canónico.

## 2. Contexto

Divergência intenção/execução detectada na auditoria forense de portos Verify Public:

| Plano | Valor | Fontes |
|-------|-------|--------|
| Intenção (selada) | :8145 | DECREE-001, DECRETO-002, §153 |
| Execução (operacional) | :8114 | nginx, systemd, G5 SEALED PORTS |

A execução em :8114 foi posteriormente canonicalizada por G5 SEALED PORTS como "intocável". A intenção original :8145 nunca foi materializada operacionalmente.

## 3. Declaração

1. **:8114** é declarado porto canónico para W-STATE-CORE-006 (Verify Public)
2. Referências a :8145 nos seguintes loci são **superseded, não apagadas** (I11):
   - DECREE-001-LIVING-TREE.md (linhas 56, 189)
   - DECRETO-002-CORE-VS-APPS.md (linhas 342, 355)
   - §153 W-STATE-CORE-006 (CLAUDE.md linha 175)
   - Port table (CLAUDE.md linha 608)
3. G5 SEALED PORTS (:8101, :8102, :8106, :8114) permanece inalterado
4. Documentos originais preservados verbatim — esta Errata vincula interpretação futura

## 4. Genealogia Constitucional

```
G5 SEALED PORTS (:8114, intocável)
        │
        ├── prevalece sobre ──→ §153 / DECREE-001 / DECRETO-002 (:8145)
        │
        └── gera ──→ §267-ERRATA-VERIFY-PORT (esta Errata)
                          │
                          └── autoriza ──→ conformação textual em CLAUDE.md
```

## 5. Anexo A — Ficheiros Afectados

| Ficheiro | Acção |
|----------|-------|
| CLAUDE.md | CORRIGIR (linhas 175, 608) |
| DECREE-001-LIVING-TREE.md | SUPERSEDED (I11) |
| DECRETO-002-CORE-VS-APPS.md | SUPERSEDED (I11) |
| CLAUDE-HISTORY.md | APPEND-ONLY (não editar) |
| 11 outros .md | Conformar incrementalmente |

---

**Human Dragon Authorization:** Explicit, session 2026-05-15  
**Merkle Chain Position:** append_post_genesis  
**Genesis Root:** 66189307d9094eab1353f9352d141d3bd45a633dada9fe4254c8c56fa9ac59cb

*Liga IA+H · Kempten, Bavaria · 2026-05-15*
