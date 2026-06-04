# JCS-RFC8785-VECTORS.md

**Documento de Conformidade — JSON Canonicalization Scheme (RFC 8785)**
**Sistema:** W-HIOS-TWIN-PROTOCOL-001
**Objecto canonicalizado:** `SignedProvenance`
**Estado:** SEALED — §300
**Referência cruzada:** `W-HIOS-TWIN-PROTOCOL-001-CANDIDATE.ts:294-320, 307, 429-430`

---

## 0. Princípio

> "O hash protege a forma; a reconciliação protege a substância."

Este documento prova a **forma**. Define os vectores de teste que demonstram que a
canonicalização WINDI do objecto `SignedProvenance` é **determinística** e **conforme
ao RFC 8785**, de modo que o `signed_digest` seja reproduzível byte-a-byte por um
auditor externo sem acesso ao código WINDI.

Um vector só é admissível se um terceiro o puder reproduzir partindo apenas de:
(a) o `input` JSON, (b) o algoritmo RFC 8785, (c) a função de digest declarada.
Se a reprodução exigir conhecimento interno da implementação, o vector é rejeitado.

---

## 1. Escopo e conformidade

### 1.1 Objecto em escopo

O **único** objecto canonicalizado-e-assinado no protocolo TWIN é o `SignedProvenance`
(`CANDIDATE.ts:294-320`):

```ts
export interface SignedProvenance {
  did: string;                       // ex. 'did:windi:cinema:001'
  key_id: string;                    // lookup local; a chave nunca viaja
  algorithm: 'ed25519' | 'ecdsa-p256';
  canonicalization: 'jcs-rfc8785';   // OBRIGATÓRIO — valor fixo
  signed_digest: string;             // 'sha256:...'
  signature: string;
  tier: 'FORENSIC' | 'STANDARD' | 'UNVERIFIED';
  receipt_ref?: ReceiptRef;          // opcional
}

export interface ReceiptRef {
  receipt_id: string;       // ex. 'WINDI-RCP-001', 'ABC12345'
  ledger_anchor?: string;   // root/commit onde foi ancorado (ex. 'sha256:abc123...')
}
```

### 1.2 Fronteira crítica de escopo

A `TwinMessage` (`CANDIDATE.ts:349-372`) **NÃO** é o objecto canonicalizado.
A `TwinMessage` *contém* o `SignedProvenance` no campo `provenance`, mas a assinatura
e o `signed_digest` cobrem **apenas** o objecto `SignedProvenance`. Canonicalizar a
mensagem inteira seria assinar a forma errada — selo a apontar para a sombra ao lado.

### 1.3 Regra de pré-imagem — DECISÃO CONSTITUCIONAL

O campo `signed_digest` é membro do próprio `SignedProvenance`. Um objecto não pode
conter o digest da sua própria forma completa sem recursão.

**DECISÃO (Human Dragon, 04 Jun 2026):** A pré-imagem do `signed_digest` é o
`SignedProvenance` **com os campos `signed_digest` e `signature` EXCLUÍDOS**
(Convenção 1: "sign-then-fill").

**Procedimento:**
1. Construir o `SignedProvenance` sem `signed_digest` e `signature`
2. Canonicalizar os 6 campos restantes com JCS (RFC 8785)
3. Computar SHA-256 da forma canónica → `signed_digest`
4. Assinar o `signed_digest` → `signature`
5. Injectar ambos no objecto final que viaja

### 1.4 Conformidade RFC 8785 declarada

A implementação garante o subconjunto RFC 8785 necessário para `SignedProvenance`:

- Ordenação lexicográfica de chaves por code unit UTF-16 (RFC 8785 §3.2.3)
- Serialização de números por ECMAScript `Number.prototype.toString` (RFC 8785 §3.2.2)
- Escape mínimo de strings (RFC 8785 §3.2.2.2)
- Ausência total de whitespace insignificante
- UTF-8 na saída final

**Fora de escopo declarado** (não por omissão): números fora do intervalo seguro
IEEE 754, dado que todos os campos de `SignedProvenance` são strings ou enums string
— **não há campos numéricos**.

---

## 2. Vectores universais (independentes do TWIN)

Provam a conformidade RFC 8785 base. Reproduzíveis com qualquer biblioteca JCS.

### V-U1 — Ordenação lexicográfica de chaves
```
input:    {"canonicalization":"jcs-rfc8785","algorithm":"ed25519","did":"x"}
expected: {"algorithm":"ed25519","canonicalization":"jcs-rfc8785","did":"x"}
```
Critério: chaves reordenadas `algorithm < canonicalization < did` por code unit UTF-16.

### V-U2 — Escape mínimo de string
```
input:    {"did":"did:windi:cinema:001"}
expected: {"did":"did:windi:cinema:001"}
```
Critério: dois-pontos não é escapado; sem aspas redundantes.

### V-U3 — Whitespace eliminado
```
input:    { "tier" :  "FORENSIC" }
expected: {"tier":"FORENSIC"}
```

### V-U4 — Unicode em valor (caso de controlo)
```
input:    {"key_id":"chave-é-única"}
expected: {"key_id":"chave-é-única"}
```
Critério: code points fora de ASCII preservados como UTF-8, não escapados em `\u`.

---

## 3. Vectores sobre `SignedProvenance` real

### V-P1 — SignedProvenance mínimo (sem `receipt_ref`)
```
input (pré-imagem, signed_digest+signature excluídos):
{
  "algorithm": "ed25519",
  "canonicalization": "jcs-rfc8785",
  "did": "did:windi:cinema:001",
  "key_id": "wk-2026-001",
  "tier": "FORENSIC"
}

expected_canonical (ordenação lexicográfica):
{"algorithm":"ed25519","canonicalization":"jcs-rfc8785","did":"did:windi:cinema:001","key_id":"wk-2026-001","tier":"FORENSIC"}

expected_digest: sha256:d32399115620b04a1b27e3ed16cc1bd6e7158a72005d29a790c35a4e48d520bc
(computado 04 Jun 2026 · Convenção 1 · verificável com: printf '%s' '<canonical>' | sha256sum)
```

### V-P2 — SignedProvenance com `receipt_ref` presente
```
input (pré-imagem):
{
  "algorithm": "ecdsa-p256",
  "canonicalization": "jcs-rfc8785",
  "did": "did:windi:cinema:001",
  "key_id": "wk-2026-002",
  "receipt_ref": {
    "ledger_anchor": "sha256:0000000000000000000000000000000000000000000000000000000000000000",
    "receipt_id": "WINDI-EXAMPLE-0001"
  },
  "tier": "STANDARD"
}

expected_canonical (ordenação lexicográfica, receipt_ref nested também ordenado):
{"algorithm":"ecdsa-p256","canonicalization":"jcs-rfc8785","did":"did:windi:cinema:001","key_id":"wk-2026-002","receipt_ref":{"ledger_anchor":"sha256:0000000000000000000000000000000000000000000000000000000000000000","receipt_id":"WINDI-EXAMPLE-0001"},"tier":"STANDARD"}

expected_digest: sha256:c18264afbf2ad4c733dc4170fb81aa7137e8924a3128053f04b15176f1c446ae
(computado 04 Jun 2026 · Convenção 1 · verificável com: printf '%s' '<canonical>' | sha256sum)
```

### V-P3 — Campo opcional ausente vs. presente
Critério: a presença/ausência de `receipt_ref` produz formas canónicas distintas e,
portanto, digests distintos.
```
expected: V-P1.digest ≠ V-P2.digest    (verificação relacional, não absoluta)
```

---

## 4. Critério de falha

Um vector **falha** (e a conformidade é rejeitada) se:

- **F1** — a forma canónica produzida diferir, num único byte, da `expected_canonical`.
- **F2** — o `signed_digest` reproduzido por auditor externo diferir do declarado.
- **F3** — campos opcionais ausentes forem serializados como `null` (viola RFC 8785 §3.2.1).
- **F4** — a ordenação de chaves não for por code unit UTF-16.
- **F5** — a pré-imagem incluir `signature` ou `signed_digest` (recursão; viola §1.3).

---

## 5. Reprodutibilidade (auditor externo)

```bash
# Dado um SignedProvenance em prov.json (forma completa):
# 1. Remover signed_digest e signature (regra §1.3)
jq 'del(.signed_digest, .signature)' prov.json > preimage.json

# 2. Canonicalizar com biblioteca JCS independente (NÃO a do WINDI)
#    ex. npm 'canonicalize' (referência RFC 8785)
node -e "console.log(require('canonicalize')(require('./preimage.json')))" > canon.txt

# 3. Digest
printf '%s' "$(cat canon.txt)" | sha256sum

# 4. Comparar com o signed_digest declarado (sem o prefixo 'sha256:')
```

Se os quatro passos reproduzirem o digest declarado **com biblioteca de terceiros**,
a forma está provada. Caso contrário, falha F2.

---

## 6. Tabela de Conformidade

| Bloqueio | Resolução | Status |
|----------|-----------|--------|
| B1 | Pré-imagem exclui `signed_digest` + `signature` (Convenção 1) | ✅ DECIDIDO (I9) |
| B2 | `ReceiptRef` = `{receipt_id, ledger_anchor?}` | ✅ CONFIRMADO |
| B3 | Digests computados e verificáveis (V-P1, V-P2) | ✅ VERIFICADO |

### 6.1 Nota sobre B1 — Convenção 1

A Convenção 1 é uma **decisão constitucional (I9)**, não uma verificação de código existente.
A spec `CANDIDATE.ts` define o contrato; implementações futuras **DEVEM** seguir esta convenção.
Os digests V-P1 e V-P2 são a referência de verificação — qualquer implementação que produza
digests diferentes viola o contrato.

---

*Conformidade ancorada em `W-HIOS-TWIN-PROTOCOL-001-CANDIDATE.ts`.*
*Não certificamos intenção — certificamos comportamento observável.*
*Liga IA+H · 04 Jun 2026*
