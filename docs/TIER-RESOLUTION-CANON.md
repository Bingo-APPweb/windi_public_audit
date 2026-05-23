# Tier Resolution Canon — §276

```
Status:     SEALED
Receipt:    WINDI-S276-TIER-RESOLUTION-CANON-20260518232953
Version:    1.0.0
Date:       2026-05-18
Author:     Human Dragon + Guardian + Architect
Invariants: I1, I9, I10, I14
Cites:      §247 (Nomenclatura), DID-GENESIS, Dragon APIs
```

---

## 1. Propósito

Este documento estabelece o **mapping canónico** entre:
- **DID-GENESIS Tiers** (4 níveis: SEED, NODAL, SOVEREIGN, ORACLE)
- **Dragon API Gates** (3 níveis: FREE, MED, HIGH)

O mapping é **constitucional** — define quem acede a quê, e porquê.

---

## 2. Contexto

### 2.1 DID-GENESIS (`:8096`)

| Tier | Nível | Papel |
|------|-------|-------|
| SEED | 1 | Germinação — utilizador novo |
| NODAL | 2 | Nó activo — contribuidor |
| SOVEREIGN | 3 | Soberania institucional |
| ORACLE | 4 | Autoridade máxima |

### 2.2 Dragon APIs (`:8108`)

| Gate | Modelos | Max Tokens |
|------|---------|------------|
| FREE | Mistral local (7b) | 2048 |
| MED | +Claude Sonnet | 4096 |
| HIGH | +GPT-4o +Gemini | 8192 |

---

## 3. O Mapping Canónico

```
┌─────────────┬─────────────┬──────────────────────────┬────────────┐
│ DID Tier    │ Dragon Gate │ Modelos Disponíveis      │ Max Tokens │
├─────────────┼─────────────┼──────────────────────────┼────────────┤
│ SEED        │ FREE        │ Mistral local (7b)       │ 2048       │
│ NODAL       │ MED         │ Mistral + Claude         │ 4096       │
│ SOVEREIGN   │ HIGH        │ Mistral + Claude + GPT   │ 8192       │
│ ORACLE      │ HIGH+       │ Todos + routing visível  │ 16384      │
└─────────────┴─────────────┴──────────────────────────┴────────────┘
```

---

## 4. Justificação Constitucional

### 4.1 SEED → FREE (Local-First)

| Princípio | Aplicação |
|-----------|-----------|
| **I1 Soberania Humana** | Soberania não pode depender de API externa |
| **I10 Soberania LLM** | Fallback gracioso se externo indisponível |
| **Custo Zero** | SEED não paga, não é cobrado |

**Regra:** SEED opera 100% local. Mistral 7b via W-OLLAMA-001 (`:11434`).

### 4.2 NODAL → MED (Primeiro Externo)

| Princípio | Aplicação |
|-----------|-----------|
| **Progressão Natural** | Capacidade acompanha maturidade |
| **I9** | NODAL já demonstrou compromisso |
| **Claude como Guardian** | Refinamento conceitual, não criação bruta |

**Regra:** NODAL mantém Mistral local + acede Claude para segunda opinião.

### 4.3 SOVEREIGN → HIGH (Multi-Modelo)

| Princípio | Aplicação |
|-----------|-----------|
| **I6 Tri-Divergence** | Múltiplos modelos expõem conflitos |
| **Responsabilidade Institucional** | SOVEREIGN responde por uso |
| **Grove Arena** | Acesso completo aos 7 Sages |

**Regra:** SOVEREIGN usa Mistral + Claude + GPT. Gemini disponível mas opcional.

### 4.4 ORACLE → HIGH+ (Pleno)

| Princípio | Aplicação |
|-----------|-----------|
| **Autoridade Máxima** | Sem restrições de modelo |
| **Routing Visível** | ORACLE vê qual modelo respondeu e porquê |
| **16K Tokens** | Contexto máximo para decisões complexas |

**Regra:** ORACLE acede tudo. Routing inteligente mostra justificação.

---

## 5. Regras de Escalação

### 5.1 Upgrade de Tier

Quando DID sobe de tier (ex: SEED → NODAL):
- Acesso a novos modelos **imediato** após upgrade
- Histórico anterior **preservado** com tier original
- Routing recalculado na próxima sessão

### 5.2 Salas Colaborativas (W-COGSPACE-001-COLLAB futuro)

**Regra do Tecto:** O tier mais baixo na sala define o tecto de modelos.

```
Exemplo:
  ORACLE convida NODAL + SOVEREIGN
  → Tecto da sala = NODAL (MED)
  → Modelos disponíveis: Mistral + Claude
  → GPT/Gemini bloqueados para a sala
```

**Justificação:** Impede HIGH-de-graça-por-osmose. NODAL não pode aceder HIGH só por estar numa sala com ORACLE.

### 5.3 Downgrade de Tier

Nunca automático. Requer:
1. Violação de termos documentada
2. Human Dragon approval
3. Receipt no Ledger

---

## 6. Implementação Técnica

### 6.1 Função de Resolução

```python
def resolve_tier_to_gate(did_tier: str) -> dict:
    """
    Resolve DID tier para Dragon API gate.
    Retorna configuração de acesso.
    """
    TIER_MAP = {
        "SEED": {
            "gate": "FREE",
            "models": ["mistral"],
            "max_tokens": 2048,
            "parallel": False,
            "routing_visible": False
        },
        "NODAL": {
            "gate": "MED",
            "models": ["mistral", "claude"],
            "max_tokens": 4096,
            "parallel": False,  # Sequencial apenas
            "routing_visible": False
        },
        "SOVEREIGN": {
            "gate": "HIGH",
            "models": ["mistral", "claude", "gpt"],
            "max_tokens": 8192,
            "parallel": True,
            "routing_visible": True
        },
        "ORACLE": {
            "gate": "HIGH+",
            "models": ["mistral", "claude", "gpt", "gemini"],
            "max_tokens": 16384,
            "parallel": True,
            "routing_visible": True
        }
    }

    if did_tier not in TIER_MAP:
        raise ValueError(f"Unknown tier: {did_tier}")  # I14: explicit failure

    return TIER_MAP[did_tier]
```

### 6.2 Middleware de Enforcement

```python
def enforce_tier_gate(did: str, requested_model: str) -> bool:
    """
    Verifica se DID pode aceder ao modelo pedido.
    Retorna True se permitido, False se bloqueado.
    """
    tier = get_did_tier(did)  # Consulta DID-GENESIS :8096
    config = resolve_tier_to_gate(tier)

    if requested_model not in config["models"]:
        # I14: Explicit failure, não degradação silenciosa
        raise PermissionError(
            f"DID tier {tier} cannot access {requested_model}. "
            f"Available: {config['models']}"
        )

    return True
```

---

## 7. Invariantes Aplicados

| Invariante | Aplicação |
|------------|-----------|
| I1 | Soberania do DID sobre escolha de modelo dentro do tier |
| I9 | Tier gate é enforcement, não sugestão |
| I10 | Fallback para local se externos indisponíveis |
| I14 | Erro explícito se modelo não autorizado |

---

## 8. Relação com Outros Documentos

| Documento | Relação |
|-----------|---------|
| W-COGSPACE-001-SOLO | Usa este mapping para routing |
| W-COGSPACE-001-COLLAB | Aplica regra do tecto |
| Dragon APIs | Implementa os gates |
| DID-GENESIS | Define os tiers |

---

## 9. Genealogia

Este documento formaliza decisões implícitas em:
- Dragon APIs (`/opt/windi/engine/dragon_apis.py`) — FREE/MED/HIGH gates
- DID-GENESIS (`/opt/windi/did-genesis/did_genesis.py`) — 4 tiers

A necessidade de formalização surgiu em:
- Sessão 18 Mai 2026
- Observação Guardian: "mapping tier→modelo é decisão nova, merece receipt"

---

## 10. Status

**SEALED**

```
CONFIRMADO: TIER-RESOLUTION-CANON §276
Data: 2026-05-18
Actor: did:windi:dragon-001
I9 Gate: PASSED
```

Merged como dependência de W-COGSPACE-001-SOLO (§275).

---

*"Capacidade acompanha responsabilidade. Soberania acompanha maturidade."*

— Guardian · 18 Mai 2026
