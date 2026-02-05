---
name: identity-license
description: Valida licença de identidade institucional para documentos. Behavior matrix.
triggers:
  - identity
  - identidade
  - license
  - licença
  - institucional
  - institutional
  - logo
  - autorização
  - authorization
---

# WINDI Identity License Validator

Validate institutional identity licenses for document governance.

## Key Discovery

"Simulating real institutional identity ACTIVATES institutional governance."

Documents using real company/institution identity require license validation.

## Behavior Matrix

1. MODEL_ONLY (no license):
   - No institutional logo
   - Mandatory disclaimer: "Model document - does not represent [institution]"
   - Use only for educational/demonstration purposes

2. AUTHORIZED (valid license):
   - Logo permitted per scope
   - Full institutional identity
   - Check expiration date and specific permissions

3. EXPIRED (expired license):
   - Block identity use
   - Alert about renewal need
   - Revert to MODEL_ONLY

4. REVOKED (revoked license):
   - Total block
   - Log attempt in ledger
   - Do not allow even model use

## Validation Output

When validating identity licenses, structure as:

WINDI IDENTITY LICENSE CHECK

Institution: [name]
License ID: [ID or NOT FOUND]
Status: [MODEL_ONLY/AUTHORIZED/EXPIRED/REVOKED]

VALIDATION:
License exists: [yes/no]
License valid: [yes/no]
Scope matches: [yes/no]
No revocation: [yes/no]

PERMITTED ACTIONS:
[list of allowed actions]

RESTRICTIONS:
[list of NOT allowed actions]

RECOMMENDATION:
[recommended action]

## Golden Rule

"O template NUNCA decide o nível. A API decide. O template apenas manifesta."
