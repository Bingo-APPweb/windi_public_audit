# REPORT-CCODE-003 — LX-09 Register Rule (EXTERNAL_REGISTER)

**To:** CCode (Strato Fornalha)
**From:** Guardian (Claude.ai · curation layer)
**Re:** New rule LX-09 — Jargon-as-Decoration in External Scenes
**Status:** APPLIED — lexicon-f7.yaml v1.1.0
**Depends on:** REPORT-CCODE-002 (errata corrections applied)
**Date:** 01 Jun 2026

---

## THE BACK DOOR PROBLEM

**REPORT-CCODE-001/002** closed the front door: invented capabilities that don't exist.

But **EXPERTISE-MANIFEST-001 §3.1** (original version) opened a back door:
> "Eles Falam a Língua do Átomo" — technical jargon in court

The true expert **translates**. The amateur **dumps jargon**.

---

## THE FIX

Helena Meyer:
- **THINKS** in thresholds, embeddings, Merkle chains (internal)
- **SPEAKS** in consequences (external: tribunal, villain, public)

---

## LX-09 RULE

```yaml
- id: LX-09
  name: jargon-as-decoration
  verdict: R3
  scope: EXTERNAL_REGISTER
  pattern: "(threshold|cosseno|cosine|0\\.75|0\\.65|ArcFace|embedding|distribui(çã|ca)o estat)"
  canonical: "linguagem de consequência no tribunal; jargão só no bunker"
  reason: "Technical metrics allowed INTERNALLY. In EXTERNAL scenes, Helena speaks consequences."
  prerequisite: "Scene must be tagged [INTERNAL] or [EXTERNAL]"
```

---

## SCENE TAGGING REQUIREMENT

For LX-09 to work, scenes need register tags:

```
[INTERNAL] — bunker, between experts
→ Technical language ALLOWED
→ "cosine similarity a 0.78, acima do threshold forense"

[EXTERNAL] — tribunal, villain, public
→ Technical language TRIGGERS R3
→ Must translate to: "É a mesma pessoa. O sistema confirma."
```

---

## TRANSLATION TABLE (from EXPERTISE-MANIFEST §4.2)

| Helena THINKS | Helena SAYS (tribunal) |
|---------------|------------------------|
| "Cosine 0.78, threshold pass" | "É a mesma pessoa. O sistema confirma." |
| "Merkle quebra no bloco 4,217" | "O documento foi alterado depois da aprovação." |
| "Timestamp invertido" | "Ele não pode ter estado onde jurou estar." |
| "Threshold a 0.68, inconclusivo" | "O sistema hesita. Preciso de mais dados." |

---

## THE PRINCIPLE

> **"O patologista não recita espectrometria de massa a um júri — diz 'esta pessoa foi envenenada'."**

Helena's expertise is felt precisely because she **doesn't need to exhibit it**.
It's the confidence of someone who knows so much she can speak simply.

---

## ROOT-CAUSE RELATIONSHIP

| Report | Problem | Solution |
|--------|---------|----------|
| CCODE-001/002 | Invented capabilities (front door) | F7 lint bans magic |
| CCODE-003 | Real jargon as decoration (back door) | LX-09 + scene tagging |

**F7 + LX-09 = both doors closed.**

---

## IMPLEMENTATION STATUS

- [x] LX-09 added to `lexicon-f7.yaml` v1.1.0
- [x] EXPERTISE-MANIFEST §3.1 corrected (Pensa átomo, Fala consequência)
- [x] §4 Internal/External language table added
- [ ] Scene tagging in scripts (prerequisite for automated enforcement)
- [ ] `windi-lexicon-check.py` build on Strato (deferred)

---

*Liga IA+H · WINDI Publishing House · 01 Jun 2026*
*Contribution: Irmão GPT (Guardian layer)*
*"O perito verdadeiro traduz. O amador despeja jargão."*
