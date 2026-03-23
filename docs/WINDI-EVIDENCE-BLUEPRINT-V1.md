# WINDI EVIDENCE — Blueprint v1.0

**Vertical:** WINDI PROTOCOL
**Tagline:** "Da cena ao tribunal — prova soberana."
**Status:** BLUEPRINT | AWAITING SEAL
**Author:** Human Dragon + Council of Dragons
**Date:** 2026-03-23

---

## 1. ARQUITECTURA TÉCNICA

### 1.1 — O que REUTILIZA (já existe)

```
┌─────────────────────────────────────────────────────────────┐
│                    WINDI PROTOCOL CORE                      │
├─────────────────────────────────────────────────────────────┤
│  Forensic Ledger :8101    ← Seal imutável + receipt         │
│  W-TRAVEL-001             ← Field capture (foto/vídeo/GPS)  │
│  W-LEGAL-001              ← Evidence Git + 4 jurisdições    │
│  W-NOTARY-001             ← Assinatura digital + timestamp  │
│  W-AUDIT-001              ← Verificação de integridade      │
│  DID System               ← Identidade soberana do agente   │
│  Verify Public :8114      ← Verificação pública             │
└─────────────────────────────────────────────────────────────┘
```

**Reutilização estimada: 85%**

### 1.2 — O que CRIA de novo

| Componente | Função | Esforço |
|------------|--------|---------|
| **W-CUSTODY-001** | Chain of Custody — quem, quando, transferiu para quem | Médio |
| **W-COURT-001** | Court Export Package — PDF + hashes + metadata | Médio |
| **Field UX** | Interface para agente no campo (não turista) | Baixo |
| **Evidence Templates** | Formulários: cena de crime, acidente, perícia | Baixo |
| **Compliance Pack** | BKA, Interpol, GDPR Art.6(1)(c), eIDAS | Documentação |

### 1.3 — Pipeline Completo

```
CAMPO                    CUSTÓDIA                 TRIBUNAL
─────                    ────────                 ────────

Agente no campo          Transferência            Apresentação
      │                        │                        │
      ▼                        ▼                        ▼
┌──────────────┐    ┌──────────────────┐    ┌──────────────────┐
│ W-TRAVEL-001 │───▶│  W-CUSTODY-001   │───▶│   W-COURT-001    │
│              │    │                  │    │                  │
│ • Captura    │    │ • Chain links    │    │ • PDF forense    │
│ • GPS ±1km   │    │ • Actor DID      │    │ • Hashes         │
│ • Timestamp  │    │ • Timestamp      │    │ • QR verify      │
│ • Hash       │    │ • Motivo         │    │ • Metadata       │
└──────┬───────┘    └────────┬─────────┘    └────────┬─────────┘
       │                     │                       │
       ▼                     ▼                       ▼
┌──────────────────────────────────────────────────────────────┐
│                    FORENSIC LEDGER :8101                     │
│                                                              │
│   EVIDENCE_CAPTURED → CUSTODY_TRANSFERRED → COURT_EXPORTED   │
│                                                              │
│   Cada evento = receipt imutável + hash + actor DID          │
└──────────────────────────────────────────────────────────────┘
```

### 1.4 — Chain of Custody Schema

```json
{
  "custody_id": "CUSTODY-20260323-0001",
  "evidence_id": "EVIDENCE-20260323-0001",
  "chain": [
    {
      "seq": 1,
      "action": "CAPTURED",
      "actor_did": "did:windi:agent-mueller",
      "timestamp": "2026-03-23T14:30:00Z",
      "geo": { "lat": 47.72, "lon": 10.31, "precision": "1km" },
      "device_fp": "a1b2c3d4",
      "hash": "sha256:abc123...",
      "ledger_receipt": "WINDI-EVIDENCE-20260323-143000"
    },
    {
      "seq": 2,
      "action": "TRANSFERRED",
      "from_did": "did:windi:agent-mueller",
      "to_did": "did:windi:forensic-lab-munich",
      "timestamp": "2026-03-23T16:45:00Z",
      "reason": "Forensic analysis required",
      "ledger_receipt": "WINDI-CUSTODY-20260323-164500"
    },
    {
      "seq": 3,
      "action": "ANALYZED",
      "actor_did": "did:windi:forensic-lab-munich",
      "timestamp": "2026-03-24T09:00:00Z",
      "findings_hash": "sha256:def456...",
      "ledger_receipt": "WINDI-ANALYSIS-20260324-090000"
    },
    {
      "seq": 4,
      "action": "EXPORTED_TO_COURT",
      "actor_did": "did:windi:prosecutor-schmidt",
      "timestamp": "2026-03-25T11:00:00Z",
      "court": "Amtsgericht München",
      "case_ref": "123 Js 456/26",
      "package_hash": "sha256:ghi789...",
      "ledger_receipt": "WINDI-COURT-20260325-110000"
    }
  ],
  "integrity": {
    "chain_hash": "sha256:final_chain_hash...",
    "all_receipts_valid": true,
    "verified_at": "2026-03-25T11:01:00Z"
  }
}
```

### 1.5 — Court Export Package

```
WINDI_COURT_PACKAGE_123Js456-26/
├── evidence/
│   ├── EVIDENCE-20260323-0001.jpg       ← Ficheiro original
│   ├── EVIDENCE-20260323-0001.hash      ← SHA-256
│   └── EVIDENCE-20260323-0001.meta.json ← Metadata
├── custody/
│   └── CUSTODY-20260323-0001.json       ← Chain completa
├── receipts/
│   ├── WINDI-EVIDENCE-20260323-143000.json
│   ├── WINDI-CUSTODY-20260323-164500.json
│   ├── WINDI-ANALYSIS-20260324-090000.json
│   └── WINDI-COURT-20260325-110000.json
├── verification/
│   ├── verify_instructions_DE.pdf       ← Como verificar
│   ├── verify_instructions_EN.pdf
│   └── qr_codes.pdf                     ← QR para cada receipt
├── COURT_SUMMARY.pdf                    ← Resumo para juiz
└── PACKAGE_MANIFEST.json                ← Hash de todo o pacote
```

---

## 2. PITCH 1 PÁGINA — REGULADORES DE/EU

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                      WINDI EVIDENCE
           "Da cena ao tribunal — prova soberana."
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

O PROBLEMA
──────────
Provas digitais são facilmente contestadas em tribunal.
- Fotos podem ser alteradas após captura
- Metadados podem ser manipulados
- Cadeia de custódia é burocrática, não criptográfica
- Peritos gastam horas a provar autenticidade

A SOLUÇÃO
─────────
WINDI EVIDENCE cria prova digital com integridade matemática.

No momento da captura:
  ✓ Hash SHA-256 do ficheiro
  ✓ Timestamp criptográfico
  ✓ Geolocalização (±1km, GDPR-compliant)
  ✓ DID do agente capturador
  ✓ Selo imutável no Ledger

Cada transferência de custódia:
  ✓ Novo selo no Ledger
  ✓ Actor identificado por DID
  ✓ Motivo registado
  ✓ Chain ligada criptograficamente

Exportação para tribunal:
  ✓ Pacote completo com verificação independente
  ✓ QR codes para cada receipt
  ✓ Instruções de verificação em DE/EN
  ✓ Hash do pacote completo

COMPLIANCE
──────────
✓ GDPR Art. 6(1)(c) — Processamento para cumprimento legal
✓ GDPR Art. 6(1)(e) — Interesse público / autoridade oficial
✓ eIDAS — Assinaturas e selos electrónicos qualificados
✓ BSI TR-03125 — Preservação de valor probatório (TR-ESOR)
✓ StPO §94 — Apreensão de objectos como prova
✓ StPO §244 — Exame de provas

DIFERENCIAL
───────────
                    Tradicional          WINDI EVIDENCE
Autenticidade       Testemunhal          Matemática
Cadeia custódia     Papel/assinaturas    Ledger imutável
Verificação         Perito necessário    Qualquer pessoa
Contestação         Fácil                Impossível (hash)
Tempo tribunal      Horas de debate      Segundos de verificação

PRÓXIMOS PASSOS
───────────────
1. Piloto com unidade policial (6 meses)
2. Certificação BSI/BKA
3. Integração com sistemas existentes (POLAS, SIS II)
4. Expansão EU via Interpol

CONTACTO
────────
WINDI Publishing House
Kempten, Bavaria, Deutschland
windi-domain.com/protocol/evidence

"AI processes. Human decides. WINDI guarantees."
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## 3. USE CASES REAIS

### 3.1 — Agente no Campo

**Cenário:** Polícia chega a cena de crime. Precisa de documentar evidência.

```
FLUXO:
1. Agente abre WINDI EVIDENCE no telemóvel
2. Autentica com DID (biométrico ou PIN)
3. Captura foto/vídeo da cena
4. Sistema gera automaticamente:
   - Hash SHA-256
   - Timestamp ISO 8601
   - GPS ±1km
   - Device fingerprint
5. Selo imediato no Ledger
6. Receipt no ecrã: "Evidência selada ✓"
7. Agente continua trabalho — prova já é imutável

RESULTADO:
- Prova existe desde o momento exacto
- Ninguém pode alegar manipulação posterior
- Cadeia de custódia começa automaticamente
```

### 3.2 — Perito Forense

**Cenário:** Laboratório recebe evidência para análise.

```
FLUXO:
1. Perito recebe notificação de transferência
2. Abre WINDI EVIDENCE
3. Verifica hash do ficheiro recebido vs Ledger
4. Se match → "Evidência íntegra ✓"
5. Regista recepção (novo link na chain)
6. Faz análise
7. Sela findings no Ledger
8. Transfere para próximo actor

RESULTADO:
- Perito prova que recebeu ficheiro inalterado
- Análise também tem hash verificável
- Chain de custódia é contínua e auditável
```

### 3.3 — Advogado de Defesa

**Cenário:** Defesa quer contestar autenticidade de prova.

```
FLUXO:
1. Defesa recebe Court Export Package
2. Abre windi-domain.com/verify-public/
3. Faz upload do ficheiro de evidência
4. Sistema compara hash com Ledger
5. Se match → "Verificado ✓ | Selado em 2026-03-23T14:30:00Z"
6. Defesa vê toda a chain de custódia
7. Cada transferência tem receipt verificável

RESULTADO:
- Defesa não pode alegar manipulação (hash prova integridade)
- Defesa pode verificar cada passo da cadeia
- Se houver quebra na chain → visível imediatamente
- Processo mais rápido, menos contestações frívolas
```

### 3.4 — Ministério Público

**Cenário:** Procurador prepara caso para tribunal.

```
FLUXO:
1. Procurador abre WINDI EVIDENCE
2. Selecciona todas as evidências do caso
3. Clica "Exportar para Tribunal"
4. Sistema gera pacote completo:
   - Ficheiros originais
   - Hashes
   - Chain de custódia
   - Receipts do Ledger
   - QR codes de verificação
   - Instruções para o juiz
5. Pacote tem hash próprio (integridade do conjunto)
6. Envia ao tribunal

RESULTADO:
- Juiz recebe pacote auto-verificável
- Qualquer perito pode validar em segundos
- Defesa não pode contestar autenticidade
- Processo judicial mais eficiente
```

---

## 4. ROADMAP

| Fase | Duração | Entregas |
|------|---------|----------|
| **F1** | 4 semanas | W-CUSTODY-001 + Field UX adaptada |
| **F2** | 4 semanas | W-COURT-001 + Export Package |
| **F3** | 6 semanas | Compliance docs + Piloto BKA |
| **F4** | Ongoing | Certificação + Expansão EU |

---

## 5. CONSTITUTIONAL ALIGNMENT

| Invariante | Aplicação em EVIDENCE |
|------------|----------------------|
| I1 | Agente humano captura — sistema processa |
| I2 | Pipeline visível — cada passo no Ledger |
| I3 | Evidência é IRREMEDIÁVEL após seal |
| I9 | human_approved sempre antes de seal |
| I11 | Ledger receipt = prova forense permanente |
| I12 | DE/EN obrigatório para tribunais EU |

---

## 6. SEAL DECLARATION

Este blueprint estabelece WINDI EVIDENCE como vertical do WINDI PROTOCOL.

```
Blueprint ID:    WINDI-EVIDENCE-BLUEPRINT-V1.0
Author:          Human Dragon + Council of Dragons
Date:            2026-03-23
Status:          AWAITING LEDGER SEAL
Classification:  STRATEGIC | CONSTITUTIONAL
```

---

*LIGA IA+H — Kempten, Bavaria · 2026*
*"AI processes. Human decides. WINDI guarantees."*
