# ALIAS-ADMISSION-DOCTRINE-001

**Status:** SEALED  
**Date:** 2026-06-13  
**Mission:** Participation Layer Research Lead  
**Depends on:** `ACTION-0-WITNESS-ADMISSIBILITY-001`, `ALIAS-RESOLUTION-001`, `ALIAS-RUN-001`, `ALIAS-PROMOTE-001`  
**Purpose:** Definir a diferenca entre resolucao tecnica de alias e admissao governada de identidade.
**I9 Decision:** Selado pelo Human Dragon em 2026-06-13.

---

## Art. 1 — Resolution vs Admission

Alias Resolution e uma tecnica.

Alias Admission e um ato governado.

```text
Resolution:
  o algoritmo encontrou uma correspondencia candidata.

Admission:
  uma autoridade reconheceu, sob criterio e testemunha,
  que um actor observado carrega uma identidade canonica.
```

Portanto:

```text
Receipt
  -> Observed Actor
  -> Alias Resolution
  -> Alias Admission
  -> Canonical Identity
  -> Contribution
  -> Recognition
```

Nenhum matching tecnico, por si so, deve ser tratado como admissao final de identidade quando o efeito for atribuir contribuicao, impacto ou reconhecimento.

---

## Art. 2 — Invariante de Imputabilidade

> Receipt define o fato.  
> Alias Admission define quem carrega o fato.

O `actor` em um receipt e o identificador historicamente observado.

O `canonical_did` e uma normalizacao adicional, admissivel apenas quando sustentada por regra, evidencia e autoridade.

Regra de guarda:

```text
actor_original nunca e apagado.
canonical_did nunca substitui a historia.
Alias Admission acrescenta imputabilidade; nao reescreve o fato.
```

Sem admissao, nao ha atribuicao final.

Com admissao falsa, reconhece-se o actor errado.

---

## Art. 3 — Regra das Duas Observacoes

Admissao formal de alias exige, por default:

```text
>= 2 observacoes independentes
```

ou:

```text
I9 explicito com ressalva de baixo volume registrada
```

Esta regra nao remove a soberania humana. Ela cria o default conservador.

Aplicacao:

```text
1 observacao  -> candidato
2+ observacoes independentes -> elegivel para admissao
alias formal existente -> resolucao direta conforme regra vigente
```

### 3.1 Observacao Independente

Observacao independente nao significa apenas repeticao da mesma string em varios receipts.

Para fins de Alias Admission, duas observacoes sao independentes quando surgem de fontes causais distintas, por exemplo:

```text
receipt em app A + receipt em app B com contexto diferente
receipt + login_event/DID Genesis
receipt + alias formal externo
receipt + documento institucional assinado
```

Repeticao de uma mesma grafia dentro do mesmo app, pipeline ou mecanismo automatizado aumenta volume, mas nao prova independencia por si so.

Regra de guarda:

```text
volume reforca suspeita.
fonte causal distinta reforca admissibilidade.
```

### 3.2 Proibicao de Raciocinio Circular

Cada Alias Admission deve sustentar-se na propria evidencia contra DID Genesis, Ledger, documento institucional ou atestado admissivel.

Uma admissao anterior nao pode, sozinha, validar outra admissao por semelhanca textual.

Exemplo proibido:

```text
dragon-001 foi admitido
logo windi-hd-001 tambem deve ser admitido porque parece semelhante
```

Sem evidencia independente, isto e cadeia de semelhanca, nao admissao.

Quando houver apenas uma observacao, o estado preferido e:

```text
resolution_status = pending_review
admission_status  = deferred_low_volume
```

Promocao com uma unica observacao so deve ocorrer com ressalva explicita no ato I9 e witness LEVEL 2 quando envolver o DID do fundador.

---

## Art. 4 — Relação com ACTION-0

Alias Admission sobre o DID do fundador e ato HIGH.

Na Liga atual:

```text
Originator = Human Dragon
Approver   = Human Dragon
Witness    = Guardian | Codex | CCode
```

O witness nao aprova.

O witness atesta reprodutibilidade temporal selada:

```text
witness_class = AI_REPRODUCIBILITY
```

Isto nao prova independencia de juizo. Prova que a classificacao foi atestada no tempo, selada, e nao pode ser persuadida retroativamente.

---

## Art. 5 — Efeito Sobre ALIAS-PROMOTE-001

`ALIAS-PROMOTE-001` deve ser lido como instrumento de Alias Admission, nao como simples lista de aliases detectados.

Cada candidato exige decisao individual.

O caso `HD-DRAGON-001`, com apenas 1 receipt, cai no default:

```text
deferred_low_volume
```

salvo I9 explicito com ressalva.

Os demais candidatos com 2+ receipts podem seguir para decisao I9 linha a linha, sempre preservando `actor_original` e registrando witness LEVEL 2 quando admitidos para `did:windi:dragon-001`.

Alias Admission e reversivel apenas por supersession, nunca por reescrita.

Se uma admissao futura for descoberta como incorreta:

```text
actor_original permanece intacto
canonical_did admitido e superado por novo registro
atribuicoes derivadas devem ser recalculadas
```

Corrigir sem reescrever (§268) aplica-se tambem a identidade admitida.

---

## Linha de Guarda

> Fundir identidade nao e descobrir uma semelhanca.
> E admitir responsabilidade historica sobre um fato observado.
