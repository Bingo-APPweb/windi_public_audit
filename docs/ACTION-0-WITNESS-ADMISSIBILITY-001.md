# ACTION-0-WITNESS-ADMISSIBILITY-001

**Status:** CONSTITUTIONAL BLOCKING QUESTION
**Date:** 2026-06-13
**Mission:** Participation Layer Research Lead
**Parent:** `CONTRIBUTION-GRAMMAR-001`
**Blocks:** `ALIAS-RESOLUTION-001` (promotion to SEALED), `ALIAS-RUN-001`, `contribution-event.schema.json`
**Principle:** Critério antes de medição. Autoridade antes de número.

---

## 0. Por Que Este Documento Existe Antes da Medição

Uma medição dirá quantos atores colapsam num DID.
Ela não dirá quem tem autoridade para reconhecer esse colapso.

```text
Medição sem critério   != decisão
Critério sem medição   != verificação
```

Precisamos dos dois. O critério vem primeiro, porque a medição sem
autoridade definida ainda não é uma decisão — é apenas um número à espera
de um juiz.

Regra de fase, herdada do WINDI-HIOS:

> Um número sem run de medição não é um número.
> Uma medição sem autoridade definida não é ainda uma decisão.

---

## 1. A Tensão Real

Na prática atual da Liga IA+H, o padrão dominante não é exceção:

```text
Originator   = Human Dragon
Approver     = Human Dragon
Classifier   = Human Dragon
```

A pergunta errada seria: *"Existe separação de papéis?"*
A resposta honesta seria: *"Ainda não completamente."*

A pergunta correta — e constitucional, não estatística — é:

> Em uma Liga composta por um único humano soberano e múltiplos agentes IA,
> o que constitui uma testemunha admissível para validações HIGH que
> envolvam o próprio originador?

---

## 2. O Que Este Documento NÃO Propõe

Limites declarados antes de qualquer modelo, para que nenhum nível abaixo
possa ser lido como erosão da soberania humana:

```text
IA não aprova.
IA não concede admissibilidade.
IA não substitui I9.
IA não decide.
```

A invariante constitucional permanece intacta:

> AI processes. Human decides. WINDI guarantees.

Witness não é Approver. São papéis distintos, e o documento mantém-nos
separados em todos os três níveis.

---

## 3. A Honestidade Sobre a Testemunha-IA

Antes de definir níveis, uma verdade que o documento se recusa a esconder:

`Guardian`, `Codex`, `CCode` são instâncias de modelos de IA operando sob
o prompt do Human Dragon, lendo estado curado pelo Human Dragon, dentro de
infraestrutura do Human Dragon.

Portanto:

```text
Uma testemunha-IA que atesta um evento do originador
NÃO prova independência de juízo.
Um espelho bem-feito ainda devolve a própria imagem.
```

O que uma testemunha-IA **pode** provar, de forma auditável:

```text
reprodutibilidade  -> outro observador, com as mesmas evidências,
                      chegaria à mesma classificação
coerência          -> o evento não contradiz os fatos registrados
consistência       -> a classificação segue a regra declarada
ausência de        -> nenhum conflito evidente entre evidência e tipo
conflito óbvio
```

O que ela **não** pode prover:

```text
independência de juízo
admissibilidade final
substituição de revisão humana
```

### 3.1 A Independência Que a IA Pode Oferecer: Temporal, Não de Juízo

A testemunha-IA não é independente do originador.
Mas pode ser independente do **futuro**.

```text
Witness atesta NO MOMENTO da criação.
Atestado é selado no Ledger (timestamp + content_hash).
Atestado torna-se irreversível.
```

O witness não pode ser persuadido retroativamente. A independência que
lhe falta no juízo, ganha-a na irreversibilidade temporal. Isto é
admissível como evidência de reprodutibilidade selada — **não** como
independência de juízo.

Sem este selo temporal, LEVEL 2 (abaixo) é independência de teatro, e cai
diretamente nos riscos já jurados pelo `CONTRIBUTION-GRAMMAR-001` §12:
"métricas opacas" e "captura por visibilidade".

---

## 4. Os Três Níveis de Admissibilidade

```text
LEVEL 1   Self Attested
LEVEL 2   Self + Witnessed
LEVEL 3   Independent Human Review
```

### LEVEL 1 — Self Attested

```text
Originator  = Human Dragon
Approver    = Human Dragon
Witness     = nenhum
```

- Admissível para eventos LOW e MEDIUM.
- Para HIGH: **insuficiente por si só.**
- `validation_status` máximo alcançável: `pending` ou `validated` apenas
  para governance_level baixo.

### LEVEL 2 — Self + Witnessed

```text
Originator  = Human Dragon
Approver    = Human Dragon
Witness     = Guardian | Codex | CCode (>= 1 atestado selado)
```

- O witness atesta no momento da criação; o atestado é selado no Ledger.
- O witness atesta **reprodutibilidade**, não independência.
- Admissível para HIGH **na ausência de um segundo humano**, como o melhor
  estado alcançável pela Liga atual.
- Deve registrar explicitamente: `witness_class = AI_REPRODUCIBILITY`,
  para que nenhum leitor futuro confunda isto com revisão independente.

### LEVEL 3 — Independent Human Review

```text
Originator  = Human Dragon
Approver    = Human Dragon
Reviewer    = segundo humano admissível (futuro)
```

- O padrão-ouro. Ainda não disponível na Liga de um humano só.
- Reservado e nomeado agora, para que o sistema **saiba o que lhe falta**
  em vez de fingir que já o tem.

---

## 5. Regra de Promoção Revisada

Atualiza `ALIAS-RESOLUTION-001` §11. Promoção para `validation_status=validated`:

| governance_level | nível mínimo exigido |
|---|---|
| LOW | LEVEL 1 |
| MEDIUM | LEVEL 1 |
| HIGH | LEVEL 2 (na Liga atual) / LEVEL 3 (quando existir 2º humano) |
| HIGH self-audit do originador | LEVEL 2 obrigatório; LEVEL 1 proibido |

Regra de guarda:

```text
Nenhum evento HIGH originado pelo Human Dragon
pode atingir validated em LEVEL 1.
```

Isto dá dentes à regra que `CONTRIBUTION-GRAMMAR-001` §7.3 prometeu:
*"o ator não deve ser juiz autônomo da própria admissibilidade."*
Em LEVEL 2, ele não é juiz autônomo — há um atestado selado e
reproduzível de uma testemunha registrada.

---

## 6. Campos Candidatos para o Witness

Acrescenta-se à estrutura `contributors[]` de `CONTRIBUTION-GRAMMAR-001` §7.2,
quando `role = witness`:

| Campo | Função |
|---|---|
| `witness_class` | `AI_REPRODUCIBILITY` ou `HUMAN_INDEPENDENT` |
| `attested_at` | Timestamp do atestado, no momento da criação |
| `attestation_hash` | Hash do atestado selado no Ledger |
| `attested_dimensions` | Lista: `coherence`, `consistency`, `reproduction`, `no_obvious_conflict` |
| `witness_did` | DID resolvido da testemunha, quando aplicável |
| `superseded_by` | Nullable; um atestado nunca é apagado, apenas superado |

Um atestado de testemunha é imutável após o selo. Correção só por
supersession explícita, nunca por reescrita (§268).

---

## 7. O Que Esta Decisão Destrava

Com Ação 0 selada:

```text
1. ALIAS-RESOLUTION-001 pode subir a SEALED
   (a lacuna que o bloqueava era esta, não a técnica de resolução).

2. ALIAS-RUN-001 pode rodar com contexto constitucional:
   quando o Codex descobrir "41 receipts -> did:windi:dragon-001",
   a pergunta "quem aprovou a resolução?" já terá resposta —
   não o próprio originador sozinho, mas originador + witness selado.

3. contribution-event.schema.json pode então ser proposto
   sobre fundação de identidade E autoridade, não só de identidade.
```

---

## 8. Pergunta Ainda Aberta (Honesta)

Quando um segundo humano entrar na Liga, ele será automaticamente um
revisor LEVEL 3 admissível, ou a admissibilidade humana exigirá também
um tier/role mínimo? Esta questão fica reservada para
`WITNESS-ADMISSIBILITY-002`, e não bloqueia o v0.1.

---

## 9. Linha de Guarda

> Numa casa de um humano só, a honestidade não é fingir independência
> que ainda não existe.
> É nomear exatamente a independência que se tem — temporal, selada,
> reproduzível — e saber o nome da que ainda falta.
