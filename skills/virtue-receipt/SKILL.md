---
name: virtue-receipt
description: Gera Virtue Receipt após decisões - hash + categorias + governance + decisão. Zero dados sensíveis.
triggers:
  - virtue
  - receipt
  - recibo
  - comprovante
  - prova
  - proof
  - hash
  - decisão
  - decision
---

# WINDI Virtue Receipt Generator

Generate ethical governance proof receipts after documented decisions.

## Core Principle

Zero-Knowledge Architecture: Client keeps data, WINDI keeps PROOF of virtue.

## Receipt Structure

1. HASH: WINDI-[DATE]-[TYPE]-[ID]
2. CATEGORIES: doc_type, impact_level, value_range (R1-R5), department_code
3. GOVERNANCE: sge_score, risk_level, validation_status
4. DECISION: action, role, timestamp, ai_recommendation, human_override
5. FLAGS: alerts if any

## Zero-Knowledge Rules

- NEVER include actual values, only ranges (R1-R5)
- NEVER include person names
- NEVER include sensitive data
- Only METADATA and PROOF of process

## Output Format

When generating virtue receipts, use this structure:

WINDI VIRTUE RECEIPT

Hash: [hash]
Generated: [timestamp]

DOCUMENT
Type: [type]
Impact: [level]
Range: [R1-R5]

GOVERNANCE
SGE Score: [score]/100
Risk: R[0-5] [emoji]
Status: [status]

DECISION
Action: [action]
Decided by: [role]
AI Suggested: [suggestion]
Human Override: [yes/no]

FLAGS: [flags or None]
