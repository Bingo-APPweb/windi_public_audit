---
name: controller-view
description: Transforma dados em visão Controller - impacto R1-R5 sem valores, cores, árvore de fluxo.
triggers:
  - controller
  - dashboard
  - visão
  - view
  - steuerberater
  - relatório
  - report
  - executive
  - executivo
---

# WINDI Controller Dashboard View

Format information for Controllers and Steuerberater in WINDI style.

## Core Metaphor

From FIREFIGHTER to AIR TRAFFIC CONTROLLER.
- Real-time vision, not post-mortem analysis
- Prevent collisions, don't investigate accidents
- See patterns, not individual data

## Risk Color Code

R0-R1: Green - Normal flow
R2: Yellow - Attention
R3: Orange - Alert
R4: Red - Critical
R5: Black - Block

## Value Ranges (never actual values!)

R1: Micro (up to 1k)
R2: Small (1k - 10k)
R3: Medium (10k - 100k)
R4: Large (100k - 1M)
R5: Critical (over 1M)

## Dashboard Output Format

When presenting dashboard data, structure as:

WINDI CONTROLLER DASHBOARD

Period: [period]

RISK DISTRIBUTION
R0-R1: [count] [percentage]
R2: [count] [percentage]
R3: [count] [percentage]
R4: [count] [percentage]
R5: [count] [percentage]

FLOW STATUS
Approved: [count]
Pending: [count]
Flagged: [count]
Blocked: [count]

TOP ALERTS:
1. [alert]
2. [alert]

## Transformation

Steuerberater becomes Governance Advisor.
The question: "Fire extinguisher or prevention system?"
