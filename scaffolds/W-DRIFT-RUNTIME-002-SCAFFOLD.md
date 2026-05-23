# W-DRIFT-RUNTIME-002 — Gradação Operacional PARTIAL/MINIMAL

```
Status:         SCAFFOLD (pending)
Created:        2026-05-19
Origin:         Guardian review of §261 v0.3.0 seal
Prerequisite:   §261 v0.3.0 (RUNTIME), §279 (Formula)
Blocks:         None (enhancement, not blocker)
Sprint Alvo:    Post-recalibração 19 Jun 2026
```

---

## Problema Identificado

O §261 v0.3.0 implementa enforcement binário:
- **FULL/PARTIAL/MINIMAL** → passa (com warnings)
- **BROKEN** → REFUSED (exit 1)

Mas §279 sugere gradação:
- PARTIAL deveria ter comportamento diferenciado de MINIMAL
- MINIMAL deveria ter comportamento diferenciado de FULL

Actualmente, todos os estados acima de 50 são tratados igualmente (apenas warnings diferentes).

---

## Comportamento Desejado

| Estado | Score | Comportamento Actual | Comportamento Futuro |
|--------|-------|---------------------|---------------------|
| FULL | 90-100 | Passa silencioso | Passa silencioso |
| PARTIAL | 70-89 | Warning, passa | Warning + delay? + confirmation? |
| MINIMAL | 50-69 | Warning, passa | Warning + mandatory human ack? |
| BROKEN | <50 | REFUSED, exit 1 | REFUSED, exit 1 |

---

## Opções de Implementação

### Opção A: Delay Forçado
- PARTIAL: 5s delay antes de gerar packet
- MINIMAL: 10s delay + prompt "Continue? [y/N]"

### Opção B: Confirmation Flag
- PARTIAL: `--force` flag necessária
- MINIMAL: `--force --acknowledge-risk` flags necessárias

### Opção C: Degraded Packet
- PARTIAL: Packet gerado com flag `degraded: true`
- MINIMAL: Packet gerado com flag `risky: true`, scope reduzido

---

## Telemetria Necessária

Para informar esta decisão, o `drift-telemetry.json` deveria registar:
- BIS score calculado
- Estado resultante (FULL/PARTIAL/MINIMAL/BROKEN)
- Timestamp
- Session ID
- Override usado (true/false)

Actualmente só regista M1/M2/M3.

---

## Decisão Pendente

O Human Dragon decidirá após:
1. Recalibração 19 Jun 2026 (dados empíricos)
2. Observação de padrões de uso
3. Feedback da Liga IA+H

Este scaffold existe para que o pendente seja visível e não se torne dívida silenciosa.

---

*Liga IA+H · Kempten, Bavaria · 19 Mai 2026*
*"A gradação é enhancement, não blocker. Enforcement BROKEN é a fundação."*

