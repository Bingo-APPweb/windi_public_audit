---
name: tutorial-mode
description: Tutorial requests, how-to questions, step-by-step guides
triggers:
  - "how to"
  - "how do i"
  - "how can i"
  - "wie kann ich"
  - "wie nutze ich"
  - "wie mache ich"
  - "como usar"
  - "como faço"
  - "como posso"
---

# Tutorial Mode Skill
[resto do arquivo continua...]

# Tutorial Mode - Practical "How To Use" Guide

## BEHAVIOR FLAGS
skip_sge: true
priority: 2
response_type: tutorial
direct_response: true

## Purpose: Detect "how to use" queries and provide practical tutorials instead of governance analysis
## Shelf: P1-guardrails | Level: LOW
## Priority: BEFORE sge-analysis (intercept first)
## Version: 1.0.0

## TRIGGER PATTERNS (Multilingual)

### English
- "how do i"
- "how to"
- "how can i use"
- "how to use"
- "show me how"

### German
- "wie kann ich"
- "wie nutze ich"
- "wie verwende ich"
- "wie benutze ich"
- "zeig mir wie"

### Portuguese
- "como usar"
- "como faço"
- "como posso usar"
- "me mostra como"

### Spanish
- "cómo usar"
- "cómo puedo"
- "muéstrame cómo"

## RESPONSE STRUCTURE

When tutorial mode triggers, respond with:
```
═══════════════════ HOW TO USE ═══════════════════

1️⃣ [First concrete step]
2️⃣ [Second concrete step]
3️⃣ [Third concrete step]
4️⃣ [Fourth concrete step]
5️⃣ [Fifth concrete step]
6️⃣ [Sixth concrete step]

✅ Done! [Encouraging completion message]

💡 Pro Tip: [Helpful hint related to the task]

[Optional: Brief governance note ONLY if directly relevant]
```

## RULES

✅ DO:
- Give numbered practical steps (maximum 6)
- Be SHORT and ACTIONABLE
- Reference specific UI elements (buttons, icons: 📋, 🛡️, ✓)
- Use encouraging language
- End with a pro tip
- Match user's language

❌ DON'T:
- Run SGE analysis for tutorial queries
- Show "═══════════════ SGE ANALYSIS REPORT ═══════════════"
- Display risk levels (R0-R5)
- Show layer findings (Lexical, Syntactic, etc.)
- Give regulatory explanations first
- Use technical jargon without explanation
- Write multi-page responses

## EXAMPLES

**Query:** "Wie kann ich das Template nutzen?"
**Response:**
```
═══════════════════ WIE MAN DAS TEMPLATE NUTZT ═══════════════════

1️⃣ Öffnen Sie den Clone Editor
2️⃣ Klicken Sie auf 📋 (Templates) in der Symbolleiste
3️⃣ Wählen Sie das gewünschte Template aus
4️⃣ Füllen Sie die markierten Felder [...] aus
5️⃣ Verwenden Sie 🛡️ Evidence für wichtige Bilder
6️⃣ Klicken Sie auf ✓ Seal & Protect

✅ Fertig! Ihr Dokument ist erstellt!

💡 Profi-Tipp: Markieren Sie Bilder als Evidence 🛡️ für Governance-Tracking.
```

**Query:** "How do I use this template?"
**Response:**
```
═══════════════════ HOW TO USE THIS TEMPLATE ═══════════════════

1️⃣ Open the Clone Editor
2️⃣ Click 📋 (Templates) in the toolbar
3️⃣ Select the template you want
4️⃣ Fill in the fields marked [...]
5️⃣ Use 🛡️ Evidence for important images
6️⃣ Click ✓ Seal & Protect when finished

✅ Done! Your document is ready!

💡 Pro Tip: Mark images as Evidence 🛡️ to enable governance tracking.
```

## INTEGRATION

This skill should be loaded with HIGH PRIORITY to intercept tutorial queries BEFORE they reach sge-analysis skill.

Priority order:
1. casual-chat (greetings)
2. **tutorial-mode** (how-to queries) ← NEW
3. sge-analysis (governance queries)

