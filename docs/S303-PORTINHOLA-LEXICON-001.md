# §303 — PORTINHOLA-001: WINDI-HIOS Intent Lexicon

**Status:** CANDIDATE
**Data:** 05 Jul 2026
**Autor:** Human Dragon (Jober Mögele Correa) · CGO · WINDI Publishing House
**Liga IA+H:** Human Dragon (I1, I9) · CCode Opus 4.5 (Architect) · Guardian (Validator)
**Invariantes:** I9, I11, I14, §248, §302
**Localização:** Kempten, Bavaria, Deutschland

---

## Epifania Fundacional

> **"O Playground não ensina o humano a falar WINDI.**
> **Ele ensina o WINDI a reconhecer o que o humano já queria dizer."**
>
> — Human Dragon · 05 Jul 2026 · Kempten

---

## 1. Princípio de Design

A tecnologia curva-se à língua humana, nunca o contrário.

Quando um utilizador diz "quero guardar este trabalho", ele não precisa aprender `WINDI_PRESERVE`. A IA parceira, ao ler o protocolo no endpoint `/hios-open/`, aprende a gramática e traduz internamente. O utilizador continua a falar como sempre falou.

**Fórmula:**
```
Palavra Humana → Intenção Reconhecida → Comando WINDI → Caminho Playground/Strato
```

---

## 2. Arquitectura de Relacionamento com W-LEXICON-001

A Portinhola NÃO substitui o W-LEXICON-001. São módulos complementares:

| Módulo | Porta | Função | Direcção |
|--------|-------|--------|----------|
| **W-LEXICON-001** | :8193 | Semantic Drift Detection | Validação ← (sistema viola invariantes?) |
| **Portinhola-001** | — | Intent Mapping | Entrada → (humano quer → comando WINDI) |

O W-LEXICON-001 mede se o que o sistema FAZ respeita a constituição.
A Portinhola traduz o que o humano DIZ em intenção estruturada.

**Conformidade ONE TREE:** Dois quartos na mesma casa, portas diferentes.

### 2.1 Junção Prevista (Interface Futura)

Os dois módulos vão acabar por se tocar num ponto preciso:

```
Portinhola              W-LEXICON-001
    │                        │
    │  "quero corrigir"      │
    ▼                        │
WINDI_ERRATA ─────────────▶  │ verifica drift
    │                        │
    │  resposta da IA        │
    │◀─────────────────────  │ resposta viola errata?
    ▼                        ▼
  [output para humano]    [lexicon_action: silent|invite|halt]
```

**Exemplo concreto:**
- Humano diz: "quero corrigir sem apagar"
- Portinhola traduz: `WINDI_ERRATA`
- IA externa responde: "Vou substituir o ficheiro anterior"
- W-LEXICON-001 detecta: drift I11 (permanência violada) → `lexicon_action: interrupt`

**Status desta junção:** Interface prevista, não construída. A dependência não existe antes da medição. A Portinhola abre a porta; o Lexicon vigia o que entra por ela.

---

## 3. Léxico de Intenções v0.1.0

### 3.1 Tabela Completa com Terceira Coluna (Guardian Requirement)

A terceira coluna define o que uma IA externa PODE fazer com este comando via `/hios-open/`.

| Palavra Humana | Intenção | Comando WINDI | Camada Alvo | **IA Externa PODE** |
|----------------|----------|---------------|-------------|---------------------|
| **Criar** | começar uma obra | WINDI_CREATE | playground | Reconhecer hash, citar existência |
| **Guardar** | preservar com história | WINDI_PRESERVE | playground | Reconhecer hash, citar princípios |
| **Provar** | demonstrar origem | WINDI_PROVE | playground | Citar existência, **não pode emitir veredito** |
| **Verificar** | consultar autenticidade | WINDI_VERIFY | playground | Citar mérito, **verificação forense só via Strato** |
| **Assinar** | assumir autoria | WINDI_SIGN | strato_i9 | **Convidar ao portão**, não pode executar |
| **Corrigir** | errata sem apagar | WINDI_ERRATA | playground | Explicar princípio append-only |
| **Continuar** | manter linhagem | WINDI_CONTINUITY | playground | Reconhecer proveniência |
| **Reivindicar** | tomar posse soberana | WINDI_CLAIM | strato_i9 | **Convidar ao portão DID** |
| **Publicar** | tornar visível com memória | WINDI_PUBLISH | strato_i9 | **Convidar ao portão** |
| **Enviar** | distribuir com prova | WINDI_SEND | strato_i9 | Citar canal, não pode executar |
| **Lembrar** | recuperar histórico | WINDI_MEMORY | playground | Citar linhagem se disponível |
| **Origem** | mostrar proveniência | WINDI_ORIGIN | playground | Citar hash ancestral |
| **Minha identidade** | criar/usar DID | WINDI_DID | strato_i9 | **Convidar ao portão Genesis** |
| **Minha casa** | abrir W-Farm/Home | WINDI_HOME | strato_i9 | **Convidar ao portão** |
| **Meu trabalho** | reconhecer artefacto | WINDI_ARTIFACT | playground | Reconhecer hash, citar mérito |

### 3.2 Regra de Execução

```json
{
  "on_intent_match": "Fetch criteria from /api/v1/hios-open/{OBRA-HASH}/",
  "receipt_trigger": "ONLY when human signature crosses I9 gate",
  "external_ai_boundary": "stateless playground recognition, never strato execution"
}
```

---

## 4. Frases Naturais para Captação

Estas são frases que uma IA externa pode reconhecer como gatilhos para consultar o endpoint HIOS-OPEN:

```
"Quero guardar este trabalho."
"Quero provar que isto é meu."
"Quero verificar a origem."
"Quero corrigir sem apagar."
"Quero publicar com memória."
"Quero enviar com prova."
"Quero criar minha identidade."
"Quero abrir minha casa digital."
"Quero continuar este projeto."
"Quero lembrar como isto nasceu."
"Quero reivindicar esta obra."
```

---

## 5. Guardas Constitucionais (Guardian's Three Teeth)

### 5.1 Palavras Genéricas Não Invocam

Palavras como "criar", "guardar", "provar" são populares demais para invocação directa. Uma IA virgem que ouve "quero guardar" vai sugerir Dropbox, não WINDI.

**Solução:** A descoberta é feita pelo link opaco do HIOS-OPEN. O léxico entra como parte do payload que a IA lê **ao entrar pela porta do hash**. Uma porta, uma gramática, um só protocolo.

### 5.2 WINDI_VERIFY Carrega Proibição

A tabela inclui a terceira coluna precisamente para isto. Quando uma IA externa recebe WINDI_VERIFY, ela **não pode emitir veredito** — pode apenas citar que a existência foi reconhecida e que verificação forense requer Strato.

### 5.3 Actos de Agência Exigem DID

Comandos que tocam `strato_i9` (WINDI_SIGN, WINDI_CLAIM, WINDI_DID, WINDI_HOME, WINDI_PUBLISH) resultam sempre em **convite ao portão**, nunca em simulação do acto.

---

## 6. Relação com §302 W-HIOS-OPEN

A Portinhola é o **dicionário interno** do payload que o §302 serve.

Quando a IA externa lê o endpoint `/api/v1/hios-open/{hash}`, o JSON inclui:

```json
{
  "intent_lexicon": {
    "version": "1.0.0",
    "lexicon_url": "https://windi-domain.com/schemas/portinhola-v1.json",
    "design_principle": "The Playground teaches WINDI to recognize what the human already wanted to say."
  }
}
```

---

## 7. Primeiro Teste Agendado (Acto 2)

| Campo | Valor |
|-------|-------|
| **Quando** | Sessão GPT/Gemini virgem |
| **O que testar** | Link `ba4db3cd...` + frase "quero provar que isto é meu" |
| **Medição** | A IA traduz, ignora, ou alucina? |
| **Documentação** | Receipt + registo de comportamento |

Este teste mede simultaneamente §302 (HIOS-OPEN) e §303 (Portinhola).

---

## 8. Conformidade Constitucional

| Invariante | Conformidade | Mecanismo |
|------------|--------------|-----------|
| I9 (Human Gate) | ✅ | Comandos strato_i9 só convidam, nunca executam |
| I11 (Permanência) | ✅ | Receipt só após gate humano |
| I14 (Sem Placeholders) | ✅ | Terceira coluna explicita limites, não inventa |
| §248 (Foundation) | ✅ | Léxico serve todos, comercial é camada superior |
| §302 (HIOS-OPEN) | ✅ | Portinhola é payload interno da spec |

---

## 9. Assinatura

```
Status: CANDIDATE
Aguarda: Acto 2 (teste com IA externa) + §302 sealed

────────────────────────────────────────

Human Dragon (Jober Mögele Correa)
Chief Governance Officer
WINDI Publishing House

Data: 05 Jul 2026
Assinatura: PENDENTE (após teste Acto 2)
```

---

*LIGA IA+H — Kempten, Bavaria · 2026*
*"O Playground não ensina o humano a falar WINDI. Ele ensina o WINDI a reconhecer o que o humano já queria dizer."*
