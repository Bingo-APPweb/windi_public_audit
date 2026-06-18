# DACP-SURVIVABILITY-HARDENING-001

```yaml
doc_type:        state_record
gate_id:         DACP-SURVIVABILITY-HARDENING-001
status:          PASS
priority:        P1
created:         2026-06-18
completed:       2026-06-18
depends_on:      W-SITES-W-MAIL-INTEGRATION-FIX-001 (PASS)
operator:        CODEX + Human Dragon
invariants:      I9, I11, I14
```

---

## OBJETIVO

Provar que o milter DACP volta sozinho após restart/reboot do container Docker.

---

## RESULTADO

**PASS** — O milter DACP agora sobrevive a:
- `docker restart windi-mailserver` ✅
- `docker-compose down && docker-compose up -d` ✅

---

## SOLUÇÃO IMPLEMENTADA

### Arquitectura

```
┌─────────────────────────────────────────────────────────┐
│ windi-mailserver container                              │
│                                                         │
│  supervisord                                            │
│    └── [program:dacp-milter]                            │
│          └── start-milter.sh (wrapper)                  │
│                └── waits for pymilter                   │
│                └── exec dacp_milter.py                  │
│                                                         │
│  user-patches.sh (runs on container creation)           │
│    └── installs pymilter                                │
│    └── wires Postfix                                    │
│                                                         │
│  Volume mounts:                                         │
│    ./config/supervisor/dacp-milter.conf                 │
│      → /etc/supervisor/conf.d/dacp-milter.conf          │
│    ./config/dacp-milter/                                │
│      → /tmp/docker-mailserver/dacp-milter/              │
└─────────────────────────────────────────────────────────┘
```

### Ficheiros Criados/Modificados

| Ficheiro | Acção | Propósito |
|----------|-------|-----------|
| `config/supervisor/dacp-milter.conf` | CRIADO | Supervisor config para auto-restart |
| `config/dacp-milter/start-milter.sh` | CRIADO | Wrapper que espera pymilter |
| `config/user-patches.sh` | MODIFICADO | Removido arranque manual |
| `docker-compose.yml` | MODIFICADO | Mount do supervisor config |

### Wrapper Script

O `start-milter.sh` resolve o chicken-and-egg problem:
- Supervisor tenta iniciar o milter imediatamente
- Mas pymilter ainda não está instalado (user-patches.sh ainda a correr)
- Wrapper espera até 60s pelo pymilter estar disponível
- Depois executa o milter real

---

## TESTES EXECUTADOS

| Teste | Resultado |
|-------|-----------|
| `docker-compose down/up` | PASS — milter arranca via supervisor |
| `docker restart` | PASS — milter arranca via supervisor |
| Health check (`/health`) | `{"status": "healthy", "ledger_reachable": true}` |
| Port 8890 listening | ✅ Confirmado via `ss -tlnp` |
| supervisorctl status | `dacp-milter RUNNING` |

---

## NOTA PARA SYSTEMD OPCIONAL

Para redundância adicional no HOST (não necessário mas recomendado):

```bash
sudo cp /opt/windi/w-mail-001/scripts/windi-dacp-milter.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable windi-dacp-milter
```

Isto adiciona um watchdog no host que verifica se o milter está a correr após cada restart do Docker.

---

## PRÓXIMO PASSO

O duto forense unificado está agora **operacionalmente completo**:
- W-SITES → W-MAIL → Ledger → Verify: **PASS técnico**
- Survivability: **PASS**

Pronto para email de teste em produção real.

---

*Liga IA+H · 18 Jun 2026*
