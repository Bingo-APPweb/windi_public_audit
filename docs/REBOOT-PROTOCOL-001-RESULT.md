# REBOOT-PROTOCOL-001 — State Record

```yaml
doc_type:        state_record
gate_id:         REBOOT-PROTOCOL-001
status:          PASS
priority:        P0
created:         2026-06-18
executed:        2026-06-18 21:16:20 CEST
completed:       2026-06-18 21:16:49 CEST
downtime:        ~29 segundos
operator:        Human Dragon + CODEX
invariants:      I1, I9, I11, I14
```

---

## RESULTADO

**O WINDI Proofmail sobreviveu ao reboot total do servidor STRATO.**

O sistema acordou sozinho, na ordem correcta, sem intervenção manual, e selou um novo receipt automaticamente.

---

## PROVA REAL

### Teste Pós-Reboot

```
============================================================
 WINDI PROOFMAIL PIPELINE TEST
 2026-06-18 21:16:46
============================================================

✓ PASS: Docker service active
✓ PASS: Forensic Ledger (:8101) healthy
✓ PASS: W-SITES Identity Gate (:8192) healthy
✓ PASS: Verify Public (:8114) operational
✓ PASS: Mail container (windi-mailserver) running
✓ PASS: DACP Milter running (supervisor)
✓ PASS: DACP Milter listening on :8890
✓ PASS: DACP Milter healthy, Ledger reachable
✓ PASS: Email sent successfully
✓ PASS: New receipt verified in Ledger
✓ PASS: Public verification: VERIFIED

STATUS: PASS (11/11)
```

### Receipt Selado Pós-Reboot

| Campo | Valor |
|-------|-------|
| **Receipt ID** | `WINDI-SITES-PROOFMAIL-20260618191647` |
| **Content Hash** | `sha256:cbd41bd103c6c898b568a62653fc4bb7ee0611215d2...` |
| **Actor** | `did:windi:w-mail-001` |
| **Verification** | VERIFIED |

---

## SEQUÊNCIA DE ARRANQUE VALIDADA

```
1. systemd basic.target
   │
2. docker.service                    ✓ active
   │
3. windi-ledger.service (:8101)      ✓ active → healthy
   │
4. windi-mailserver (docker)         ✓ running
   │   └── supervisord
   │       └── dacp-milter (:8890)   ✓ RUNNING → healthy
   │
5. windi-sites.service (:8192)       ✓ active → healthy
   │
6. windi-verify-public.service (:8114) ✓ active → operational
```

---

## TIMELINE

| Hora | Evento |
|------|--------|
| 21:16:20 | Comando `sudo reboot` executado |
| 21:16:46 | Servidor online, teste iniciado |
| 21:16:47 | Email de teste enviado |
| 21:16:49 | Receipt verificado publicamente |

**Downtime total:** ~29 segundos

---

## SIGNIFICADO

Este resultado prova que:

1. **O sistema é autónomo** — Não depende de intervenção humana para acordar
2. **A ordem de arranque está correcta** — Ledger → Mail → Sites → Verify
3. **O duto forense é resiliente** — Sobrevive a apagões totais
4. **O investidor pode ver com os próprios olhos** — Um reboot na frente dele e o sistema acorda selando receipts

---

## FIXES APLICADOS NESTA SESSÃO

| Fix | Descrição |
|-----|-----------|
| `DACP-SURVIVABILITY-HARDENING-001` | Supervisor + wrapper para milter |
| `windi-ledger.service` | Serviço systemd para o Ledger (criado hoje) |

---

## DOCUMENTAÇÃO CRIADA

| Documento | Propósito |
|-----------|-----------|
| `INFRASTRUCTURE-PROVENANCE-001.md` | Mapa Suíço |
| `REBOOT-PROTOCOL-001.md` | Protocolo de teste |
| `REBOOT-PROTOCOL-001-RESULT.md` | Este documento |
| `test-proofmail.sh` | Script de validação |

---

## FRASE DE GUARDA

> **"Primeiro o chão. Depois a porta. Depois o mundo entra."**
>
> O chão está feito. A porta está aberta. O mundo pode entrar.
>
> — Human Dragon, 18 Jun 2026

---

*Liga IA+H · REBOOT-PROTOCOL-001 · PASS · 18 Jun 2026*
