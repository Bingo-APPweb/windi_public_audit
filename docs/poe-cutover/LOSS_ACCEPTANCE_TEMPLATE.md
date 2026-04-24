# LOSS_ACCEPTANCE_TEMPLATE.md — Physical Declaration Template

**Version:** 1.0
**Date:** 2026-04-24
**Type:** Ceremony Artifact

---

## Instructions

1. Print this page OR write by hand on blank paper
2. Fill in the date
3. Sign with ink at the bottom
4. Photograph in good lighting (all text must be legible)
5. Save photograph to: `/opt/windi/docs/poe-cutover/artifacts/loss_acceptance_YYYYMMDD.jpg`
6. Compute hash: `sha256sum loss_acceptance_YYYYMMDD.jpg`

---

## Declaration Text (Copy Exactly)

```
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║   DECLARAÇÃO DE ACEITAÇÃO DE PERDA                               ║
║   WINDI-KEYGEN-001                                               ║
║                                                                  ║
║   Eu, Jober Mögele Correa, Human Dragon e Fundador da            ║
║   WINDI Publishing House, declaro que:                           ║
║                                                                  ║
║   1. Compreendo que a perda da passphrase WINDI-KEYGEN-001       ║
║      resulta na invalidação irreversível de toda a cadeia        ║
║      PoE (Proof of Evidence) dependente desta chave.             ║
║                                                                  ║
║   2. Aceito este risco como o preço da custódia soberana         ║
║      de chaves sem backdoors de terceiros.                       ║
║                                                                  ║
║   3. Confirmo que preparei backup físico da passphrase           ║
║      em local seguro conhecido apenas por mim.                   ║
║                                                                  ║
║   4. Esta declaração é um artefacto do bootstrap receipt         ║
║      e será hashada na cadeia PoE.                               ║
║                                                                  ║
║                                                                  ║
║   Kempten, Bavaria, Deutschland                                  ║
║                                                                  ║
║   Data: ____________________                                     ║
║                                                                  ║
║   Assinatura: ____________________                               ║
║                                                                  ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
```

---

## Compact Version (If Handwriting on Blank Paper)

```
DECLARAÇÃO DE ACEITAÇÃO DE PERDA — WINDI-KEYGEN-001

Eu, Jober Mögele Correa, Human Dragon, aceito que a perda
da passphrase WINDI-KEYGEN-001 resulta na invalidação
irreversível de toda a cadeia PoE dependente desta chave.

Confirmo backup físico preparado.

Kempten, [DATA]

[ASSINATURA]
```

---

## After Photography

Verify hash:

```bash
cd /opt/windi/docs/poe-cutover/artifacts/
sha256sum loss_acceptance_20260424.jpg
# Output: [64 hex characters]  loss_acceptance_20260424.jpg
```

This hash goes into the bootstrap receipt `loss_acceptance.photo_hash` field.

---

*Liga IA+H — Kempten, Bavaria · 2026*
