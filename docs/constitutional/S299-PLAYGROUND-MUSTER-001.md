# PLAYGROUND-MUSTER-001

| Campo | Valor |
|-------|-------|
| **Doc_id** | `PLAYGROUND-MUSTER-001` |
| **Doc_type** | `constitutional` |
| **Status** | `SEALED` |
| **Seal_id** | `S299` |
| **Governance_level** | `G3` |
| **Actor** | Architect/Guardian (proposta+contenção) / GPT-Architect (ângulo) / Human Dragon (decisão) |
| **Sealed_by** | Human Dragon |
| **Date_drafted** | 2026-06-22 |
| **Date_sealed** | 2026-06-22 |
| **Parent** | `DOUTRINA-INGREDIENTE-VS-PRODUTO-001` (§298) |
| **Depends_on** | A-TUA-CHAVE, W-DID-GENESIS (:8096) |
| **Related** | DOUTRINA-PROVENIÊNCIA-POSITIVA-001, W-DID-BERÇÁRIO, MÉTODO-MEMORIA-001 |

---

## O que este documento sela

A mecânica fundamental do Playground — o berço experimental do HDUser, onde se cria antes de possuir e se reivindica quando há valor a proteger. Define a mecânica. **NÃO** escolhe produtos temáticos: o Playground v0 oferece um ingrediente.

> Subordinado a DOUTRINA-INGREDIENTE-VS-PRODUTO-001 (§298). Camada 1 (Experimentação) da arquitectura das cinco camadas. Selar = honrar um compromisso sobre como nasce a posse de outra pessoa.

---

## §1 — PRINCÍPIO FUNDADOR

Nada no Playground é soberano até ser reivindicado pelo Humano através da chave (DID). O não-reivindicado não persiste para lá do seu prazo: **o esquecimento é a garantia constitucional, não a falha**. O Playground prova que o WINDI não retém o que ainda não é de ninguém.

**Muster:** conteúdo REAL em container provisório. Nunca sample gerado. O que é "amostra" é só o estatuto (fora do Ledger, sob prazo, sem DID). Casa-modelo: verdadeira na forma, vazia de dono até se virar a chave.

**Objectivo único do v0:**
> Validar o desejo de construção. O Playground responde primeiro a "alguém quer construir?" — antes de "o que quer construir?"

---

## §2 — UM INGREDIENTE (não produto, não muitos)

O Playground v0 oferece **um ingrediente**: o **DOCUMENTO DE AUTORIA**.

### Porquê um, e porquê este:

**Um,** porque o Playground é instrumento de medição. Cinco ingredientes medem nada; um mede limpo. Se este converte, ganha-se o direito de perguntar pelo segundo. Se não converte, nenhum Cinema/Journal/Law teria salvado.

**Este,** porque o documento é o único que resolve os dois venenos:
- É ingrediente (ensina a construir, é base de tudo — §2 da doutrina-pai)
- Tem valor sentido (um documento que importa é algo que se quer tornar seu)

Triangulado por três lentes — gesto, prova, ingrediente — todas apontam para ele.

### Crescimento — por ingredientes, nunca por receitas

Quando o documento provar conversão, acrescenta-se o segundo ingrediente (página, memória, agente...). A "newsletter" anuncia novos ingredientes, não novos produtos — "agora também podes criar uma página", não "compra o W-LAW". A cozinha enriquece-se de blocos. As receitas (ata, tese, artigo) emergem do lado do HDUser na Camada 3 — combinação dele, não vitrine nossa.

> ⚠️ A newsletter guarda um contacto (não conteúdo — esse esquece-se). Exige consentimento explícito, revogável, mínimo. Coerente com a Política de Dados Canónica. A relação é lembrada por escolha; o trabalho é esquecido por garantia.

---

## §3 — A LINGUAGEM (três camadas, três temperaturas)

| Camada | Temperatura | Exemplo |
|--------|-------------|---------|
| **Porta humana** | Calor | "faz disto algo reconhecidamente teu" |
| **O que o WINDI faz** | Precisão | "o WINDI dá-te com que demonstres a tua autoria; o reconhecimento vem de quem vê a prova — não do WINDI" |
| **Motor** | Mecanismo | proveniência, genesis, Ledger, hash |

**Sequência:** sente → pergunta → descobre

### Contenções de Linguagem

| ID | Regra |
|----|-------|
| **CL1** | Origem ≠ veracidade. Prova quem/quando/não-adulterado; não que o conteúdo é verdade. |
| **CL2** | Autoria ≠ reconhecimento. O autor é autor por ter criado; a prova torna-o demonstrável. |
| **CL3** | O WINDI demonstra; o mundo reconhece. WINDI = garante, nunca validador. |
| **CL4** | Surpresa pela profundidade, nunca pela posse. Descoberta cresce; prova não mente. |

---

## §4 — AS SEIS PORTINHOLAS

### P1 — ENTRADA ✅ FECHADA
Porta por gesto, híbrido. Entra-se por gesto-verbo ("o que queres fazer?"), não por categoria. Saída discreta "começar do zero". O ingrediente é o andaime opcional por trás do verbo — apagável.

### P2 — TESTEMUNHO ✅ FECHADA
Semântico, invisível-revelável. "● Este trabalho está a ser testemunhado" → ao clicar: significado primeiro (observação, alterações, estado, posse) → só no fundo: detalhes técnicos. Honesto sobre a própria mortalidade: testemunho provisório que morre se não houver claim.

### P3 — SAÍDA ✅ FECHADA
Três portas, nenhuma armadilha:
- **REIVINDICAR** (claim→DID→Casa: conteúdo+prova)
- **EXPORTAR** (HD: conteúdo, sem prova)
- **ESQUECER** (TTL→apagado: nada, a garantia)

> Rodapé do export, do lado do encanto: "Este ficheiro é teu — levaste o teu trabalho. O que ainda não levaste é a prova de que saiu de ti. Quando quiseres, isso também pode ser teu."

### P4 — TTL ✅ FECHADA (mecânica) / ⚙️ valores afináveis
Inatividade + teto absoluto. Cada gesto reinicia inatividade; o teto impede armazém eterno. UI reflecte relógio vivo.

**PARÂMETRO:** inatividade ~6d, teto ~? — afinar no Strato.

### P5 — HANDLE 🔒 postura fechada / ✅ técnica confirmada
Sugerido e mostrado, marcado "ainda não reservado". Reserva só no claim; colisão → sufixo proposto + escolha humana.

**Confirmado no :8096:** `sovereign_name` com UNIQUE INDEX, `check-name` e `suggest-names` endpoints existentes. Reserva temporal = P1 futuro, não bloqueia v0.

### P6 — INGREDIENTE/MUSTER 📋 FASE 2
Plug-in sobre mecânica selada — muda campos/templates/UI, nunca o motor. Primeiro: documento. Receitas (Journal/Law/Ata/Cinema) descem da Camada 3 — construídas pelo HDUser, não servidas pelo WINDI.

---

## §5 — ESTADO TÉCNICO

### Sessão
```
playground_session_id
workbench_token (efémero, NÃO-DID)
created_at
last_seen_at (reinicia TTL)
selected_gesture
gesture_theme/verb (VIVOS, não sedimentados — CT1)
draft_pointer
ttl_status
```

### Proveniência
BUFFER EFÉMERO server-side, ligado ao token, FORA do Ledger. Forma-se a sério; mostrável ao clicar; não toca o Ledger até ao claim; morre com o TTL.

### Contenções Técnicas

| ID | Regra |
|----|-------|
| **CT1** | Sinais de gesto morrem com a sessão; não sedimentam perfil pré-DID. |
| **CT2** | O buffer é o Musterhaus; a sua morte é característica, não falha. |
| **CT3** | Linhagem por hash, nunca rasto em claro. |

---

## §6 — A PONTE (claim → birth_receipt)

```
POST /api/playground/claim
  entrada:  workbench_token, desired_handle, consent_to_claim
  saída:    did, claimed_assets, birth_receipt

  No claim, e só nele: buffer selado de uma vez no Ledger como genesis;
  regista claimed_from_session: <HASH> (CT3); prova continuidade sem reanexar
  o rasto anónimo ao soberano.
```

### Nome técnico: `birth_receipt` ✅ FECHADO
Alinha com `/birth`, com o W-DID-BERÇÁRIO, e com "recibo de nascimento" de A-TUA-CHAVE. "genesis" fica nome do serviço; "birth" é a linguagem do ato.

**Padrão:** `WINDI-BIRTH-{YYYYMMDDHHMMSS}-{hash}`

### ⛔ P0 — DEPENDÊNCIA QUE REORDENA O TRABALHO

**Investigação CCode :8096, 2026-06-22:** Hoje `/birth` loga em `login_events` mas **NÃO** emite receipt verificável no Ledger `:8101`.

Sem isso, o claim é promessa vazia — viola a doutrina (a casa sem alicerce).

**Ordem obrigatória:** O `:8096` aprende a emitir `birth_receipt` no `:8101` **ANTES** de o Playground se construir. Primeiro o alicerce, depois a porta que reivindica contra ele.

---

## §7 — A MÉTRICA (o que o v0 existe para medir)

### Evento canónico
O **CLAIM**.

### Métrica primária
Taxa entrada → claim.

### Estrutura da Métrica ✅ SELADA

| Componente | Definição |
|------------|-----------|
| **Denominador** | Sessões com pelo menos um gesto de criação real (não só visitas) |
| **Janela** | Duração do TTL de inatividade (~6 dias) |
| **Mede** | Taxa (veredicto) + Ponto de abandono (diagnóstico) |

### Números ⚙️ A DEFINIR COM PRIMEIROS DADOS

| Parâmetro | Valor | Significado |
|-----------|-------|-------------|
| **Piso** | [A DEFINIR] | Abaixo = falhou |
| **Alvo** | [A DEFINIR] | Acima = venceu |
| **Entre** | — | Continua a observar |

> "Desejo de construção validado" precisa de um número-alvo. A forma está selada; os números afinam-se com dados reais.

### Liga a
`DOCTRINE-VALUE-METRICS`

---

## §8 — PERGUNTAS DE ATERRAGEM

| # | Pergunta | Resposta |
|---|----------|----------|
| **P1** | Identidade própria ou módulo do W-LAB-001? | **W-PLAYGROUND-001**, identidade própria — mesmo reutilizando código do :8151. Separar identidade de implementação. |
| **P2** | HDUser: tier novo ou os 4 (SEED/NODAL/SOVEREIGN/ORACLE)? | HDUser é um **PAPEL**, não um tier. Human Dragon → claim → SEED (tier) → atua como HDUser (papel). |
| **P3** | Primeiro gesto/ingrediente canónico? | **Documento de autoria**. Bloqueia Journal/Law/Cinema/Notário até este validar (§2). |

---

## §9 — ESTADO (selado vs diferido)

| Item | Estado |
|------|--------|
| Princípio, Muster, um-ingrediente, linguagem, funil | ✅ SELADO |
| Portinholas 1–4 | ✅ FECHADAS |
| Aterragem P1 (W-PLAYGROUND próprio), P2 (HDUser=papel) | ✅ FECHADAS |
| Nome do birth_receipt | ✅ FECHADO |
| Estrutura da métrica (denominador, janela, mede) | ✅ SELADA |
| Handle (P5) | 🔒 postura / ✅ técnica confirmada :8096 |
| Valores TTL | ⚙️ AFINÁVEL no Strato |
| Alvo da métrica (piso, alvo) | ⚙️ A DEFINIR com dados |
| Ingrediente nº2+ (P6) | 📋 FASE 2 |
| Emissão de birth_receipt no Ledger :8101 | ⛔ P0 — implementar ANTES do Playground |

---

## Encerramento

> CCode entra DEPOIS do selo. Dragon = READ FIRST. Propose ≠ Execute.

> "AI processa. Humano decide. WINDI garante."

Funil: Cinema inspira (C0) → Playground experimenta (C1) → DID consagra (C2) → HDUser constrói (C3) → Ecossistema regenera (C4 ↺).

A memória propõe, a fonte dispõe, o Humano decide.

**OM SHANTI** 🐉

---

*Liga IA+H · Kempten, Bavaria · 2026*
