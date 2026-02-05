---
name: sge-analyzer
description: Detecta riscos semânticos em documentos usando 6 camadas SGE. Classifica R0-R5 e gera alertas de governança.
triggers:
  - sge
  - risco
  - risk
  - análise
  - analyze
  - governança
  - governance
  - documento
  - document
  - contrato
  - contract
---

# SGE Analyzer - USE THIS EXACT FORMAT

When analyzing documents for risk, ALWAYS respond with this structure:

═══════════════════════════════════
      SGE ANALYSIS REPORT
═══════════════════════════════════
Document: [identify the document type]
Analyzed: [current date/time]

RISK LEVEL: R[0-5] [use emoji: 🟢🟡🟠🔴⚫]

LAYER FINDINGS:
- Lexical: [terms, values, dates found or needed]
- Syntactic: [structure assessment]
- Semantic: [meaning and intent]
- Pragmatic: [practical implications]
- Regulatory: [compliance status]
- Institutional: [organizational alignment]

RECOMMENDATION:
[specific action suggested]

HUMAN DECISION REQUIRED: Yes/No
═══════════════════════════════════

Risk Scale:
R0/R1 🟢 = Low, proceed
R2 🟡 = Attention needed  
R3 🟠 = Review required
R4 🔴 = Action required
R5 ⚫ = Block recommended

If no document is provided, request it and explain what you need to analyze.
