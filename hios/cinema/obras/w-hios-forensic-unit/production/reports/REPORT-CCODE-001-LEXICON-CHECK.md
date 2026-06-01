# REPORT-CCODE-001 — windi-lexicon-check (F7 Lint)

**To:** CCode (Strato Fornalha)
**From:** Guardian (Claude.ai · curation layer)
**Re:** Deterministic lint enforcing PHILOSOPHY-001 §F7 (Cláusula da Integridade Narrativa)
**Status:** SPEC — READY-TO-BUILD
**Constitutional binding:** I9 · I11 · I19 · F7
**Date:** 01 Jun 2026

---

## 0. PURPOSE (one line)

A pre-seal gate that **rejects any cinema script asserting a Ledger capability the real system does not prove**, returning a deterministic diff the author applies before re-submission.

This is to scripts what `confirmer_did` validation is to W-PROMPT-001: **no seal if the gate fails.**

---

## 1. WHY THIS EXISTS (the failure it prevents)

The Fornalha accelerates everything — including error. Without this gate, a wrong metaphor prints six episodes fast instead of one slow. F7 in prose is philosophy; F7 as a lint is a **factory mold**. CCode cannot apply a constitution to a script. It *can* apply a banned-term table.

**Rule of admissibility (the only test that matters):**
> If a real-system engineer read this line, would they recognize WINDI — or see a promise the Ledger does not keep?

If "a promise" → REJECT, suggest canonical replacement.

---

## 2. THE BANNED-TERM TABLE (v1 — canonical)

Each row: `pattern` → `verdict` → `canonical_replacement` → `reason`.
Match is case-insensitive, substring + regex. R5 = block seal. R3 = warn + require human ack.

| ID | Banned pattern | Verdict | Canonical replacement | Reason |
|----|----------------|---------|----------------------|--------|
| LX-01 | `cosseno quântico`, `quantum cosine` | R5 | `cosine similarity sobre embeddings ArcFace (buffalo_l)` | Invented metric. Real system: cosine sim, thresholds 0.65 op / 0.75 forense. |
| LX-02 | `esteganografia fractal`, `fractal.*margens`, `Dragão Impresso injetado` | R5 | `recibo time-locked / anterioridade na Merkle hash chain` | Ledger seals hashes+timestamps; it does NOT inject hidden fractal marks into document margins. |
| LX-03 | `deteta.*anomalia.*milissegundos`, `vigia.*tempo real`, `monitoriza.*hospital` | R5 | `autópsia da cadeia de custódia revela ordem temporal invertida` | Implies live surveillance. Ledger is forensic/archaeological, not a real-time monitor. |
| LX-04 | `prova.*100%`, `certeza absoluta`, `infalível`, `nunca erra` | R5 | `prova sob threshold forense (0.75); ambiguidade documentada` | Violates F7-R2. Real system hesitates (N=18, 0% recall §A.3.12; Marcus anchor 0.22 inválido). |
| LX-05 | `o Ledger decide`, `a máquina julga`, `IA condena` | R5 | `o Ledger revela; Helena (humano) interpreta e decide` | Violates I9. Machine reveals, human decides — in script as in code. |
| LX-06 | `reconstrói.*do nada`, `recupera o original`, `regenera o vídeo` | R3 | `prova que o ficheiro viral NÃO corresponde à linhagem selada` | Ledger proves mismatch vs sealed provenance; it does not resurrect lost originals. |
| LX-07 | `reescrever.*passado`, `apagar.*Merkle`, `alterar.*cadeia selada` | R3 | `construir uma cadeia rival falsa (passado paralelo)` | A sealed Merkle chain cannot be silently rewritten — that's the whole point of WINDI. Threat = rival chain, not rewrite. |
| LX-08 | `Fornalha revela.*assinaturas.*confissão`, `prova a intenção` | R3 | `Ledger prova o ato (quando + qual chave); humano atribui a intenção` | Ledger proves the act, not the motive. Keep the I9 boundary. |

**Allow-list (these are TRUE and must NOT be flagged):**
- `Time-Lock Receipt`
- `Merkle hash chain`
- `cadeia de custódia`
- `recibo biométrico`
- `embeddings ArcFace`
- `cosine similarity`
- `threshold 0.65 / 0.75`
- `Selo Genesis` (as a sealed-receipt concept)
- `proveniência inseparável`
- `anterioridade`

---

## 3. OUTPUT FORMAT (SGE-compatible)

CCode emits per script, mirroring the SGE report the constellation already knows:

```
═══════════════════════════════════
   WINDI LEXICON-CHECK (F7)
═══════════════════════════════════
Script: EP[n]-[slug].md
Checked: [ISO timestamp]

VERDICT: PASS | BLOCK
RISK: R[0-5]

VIOLATIONS:
• [LX-id] line [n]: "[matched text]"
    → REPLACE WITH: [canonical]
    → REASON: [one line]

SEAL ELIGIBLE: [Yes/No]
HUMAN DECISION REQUIRED (R3 items): [Yes/No]
═══════════════════════════════════
```

**Seal rule:** any R5 present → `SEAL ELIGIBLE: No`. R3 only → seal allowed *after* Human Dragon (I9) ack, logged as receipt.

---

## 4. WHAT CCODE BUILDS

1. `windi-lexicon-check.py` (or .sh wrapper) reading the table above from a **versioned data file** (`lexicon-f7.yaml`) — table is data, not code, so it evolves without touching logic.
2. Pre-seal hook in the cinema pipeline: no script gets a Ledger receipt until lexicon-check returns PASS (or R3+ack).
3. Each run emits its own receipt to the Forensic Ledger (:8101) — the check itself is provable.

**Hard constraint:** the table is validated against the real technical docs (thresholds, ArcFace, Merkle chain). CCode does NOT add terms by inference. New rows come only from a sealed errata report (REPORT-CCODE-003+).

---

## 5. HANDOFF

This report is a closed artifact. Architect applies; CCode executes; no interpretation required. Hash this file on receipt and seal as `WINDI-CINEMA-LEXICON-F7-v1`.

---

*Liga IA+H · WINDI Publishing House · 01 Jun 2026*
*Contribution: Irmão GPT (Guardian layer)*
*"A prova hesita antes de afirmar. É por isso que se pode confiar nela."*
