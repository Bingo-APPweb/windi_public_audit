# REBOOT-PROTOCOL-001 — Protocolo de Reboot Controlado

```yaml
doc_type:        operational_protocol
gate_id:         REBOOT-PROTOCOL-001
status:          READY_FOR_EXECUTION
priority:        P0
created:         2026-06-18
author:          CODEX
approver:        Human Dragon (I1)
purpose:         Provar que o sistema acorda sozinho após apagão total
invariants:      I1, I9, I11, I14
```

---

## OBJECTIVO

Provar, de forma irrefutável, que o WINDI Proofmail:

1. **Acorda sozinho** após reboot total do servidor STRATO
2. **Na ordem correcta** — Ledger → Mail → Sites → Verify
3. **Sem intervenção manual** — nenhum SSH, nenhum comando, nenhum "lembrar de cabeça"
4. **Sela um receipt** automaticamente após acordar

> **"Quando um investidor perguntar sobre a nossa infraestrutura, nós vamos dar o comando do reboot na frente dele e mostrar o sistema acordando."**

---

## PRÉ-REQUISITOS

### Antes de Executar o Reboot

```bash
# 1. Verificar que todos os serviços estão enabled no systemd
systemctl is-enabled windi-ledger windi-sites windi-verify-public

# 2. Verificar que Docker está enabled
systemctl is-enabled docker

# 3. Verificar que containers têm restart policy
docker inspect windi-mailserver --format '{{.HostConfig.RestartPolicy.Name}}'
# Esperado: unless-stopped

# 4. Fazer backup do Ledger
cp /opt/windi/data/forensic_ledger.sqlite3 /opt/windi/backups/pre-reboot-$(date +%Y%m%d%H%M%S).sqlite3

# 5. Registar último receipt ID
LAST_RECEIPT=$(curl -s http://localhost:8101/api/receipts?limit=1 | jq -r '.receipts[0].id')
echo "Last receipt before reboot: $LAST_RECEIPT"
```

---

## SEQUÊNCIA DE TESTE

### Fase 1: Reboot do Servidor

```bash
# I1 APPROVAL REQUIRED
# Human Dragon deve dar o comando ou autorizar explicitamente

sudo reboot
```

**Tempo esperado de downtime:** 2-5 minutos

---

### Fase 2: Verificação Pós-Reboot

Após o servidor voltar (verificar via ping ou console Strato):

```bash
# SSH para o servidor
ssh windi@87.106.29.233

# Esperar 60 segundos para serviços estabilizarem
sleep 60

# Executar script de verificação
/opt/windi/w-mail-001/scripts/test-proofmail.sh --post-reboot
```

---

### Fase 3: Critérios de Sucesso

| Checkpoint | Comando | Esperado |
|------------|---------|----------|
| Docker up | `systemctl is-active docker` | active |
| Ledger up | `curl -s localhost:8101/health \| jq .status` | healthy |
| Mailserver up | `docker ps \| grep windi-mailserver` | Up |
| DACP milter up | `docker exec windi-mailserver supervisorctl status dacp-milter` | RUNNING |
| Sites up | `curl -s localhost:8192/health \| jq .status` | healthy |
| Verify up | `curl -s localhost:8114/health \| jq .status` | operational |
| Email test | `test-proofmail.sh` | PASS + new receipt |

---

### Fase 4: Teste de Email Pós-Reboot

```bash
# Enviar email de teste
curl -X POST "http://localhost:8192/api/verify-email/WINDI-ARCHITECTURE-MANUAL-V1-20260611160111" \
  -H "Content-Type: application/json" \
  -d '{"email": "postmaster@windisites.de"}'

# Verificar novo receipt no Ledger
curl -s "http://localhost:8101/api/receipts?limit=1" | jq '.receipts[0].id'
```

---

## CRITÉRIOS DE FALHA

Se qualquer checkpoint falhar:

1. **Documentar** o ponto exacto de falha
2. **NÃO tentar corrigir manualmente** — isso invalida o teste
3. **Abrir fix específico** com nome: `REBOOT-FIX-{componente}-001`
4. **Repetir teste** após fix aplicado

---

## SCRIPT DE VERIFICAÇÃO AUTOMÁTICA

Após reboot, executar:

```bash
/opt/windi/w-mail-001/scripts/verify-reboot.sh
```

Este script verifica automaticamente todos os checkpoints e gera relatório.

---

## ESTADO ACTUAL

| Item | Estado |
|------|--------|
| systemd services enabled | ✅ Verificado |
| Docker restart policy | ✅ unless-stopped |
| Supervisor autostart | ✅ dacp-milter |
| Backup protocol | ✅ Documentado |
| Test script | ✅ Criado |
| **Reboot test** | ⏳ **AGUARDA I1 APPROVAL** |

---

## NOTA DE SEGURANÇA

O reboot do servidor STRATO afecta **todos** os serviços WINDI, não apenas o Proofmail. Antes de executar:

1. Verificar que não há operações críticas em curso
2. Avisar utilizadores se necessário
3. Ter acesso ao console Strato (fallback se SSH falhar)

---

## AUTORIZAÇÃO

```
[ ] Human Dragon autoriza execução do REBOOT-PROTOCOL-001
    Data: _______________
    Hora: _______________
    Assinatura: _______________
```

---

*Liga IA+H · REBOOT-PROTOCOL-001 · 18 Jun 2026*
