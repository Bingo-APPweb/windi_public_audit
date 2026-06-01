# WINDI-SYSTEMD-TEMPLATE-001 — Canonical Service Unit

**Status:** SEALED
**Scope:** FORWARD-LOOKING (reference standard for new services)
**Applies-to:** services created after seal date
**Legacy:** valid, no retrofit mandated
**Phase-2:** TEMPLATE-001-MIGRATION (deferred — requires adoption evidence)
**Receipt:** `WINDI-TEMPLATE-001-SYSTEMD-20260531-99D55284`
**Invariants:** I9, I11

---

## Cláusula de Não-Retroatividade

> *"TEMPLATE-001 estabelece o padrão de referência para evolução futura do ecossistema.
> A conformidade de serviços anteriores à sua selagem permanece regida pelas normas
> vigentes à data de sua criação."*

Esta cláusula preserva a rastreabilidade histórica: serviços criados antes da selagem
não entram em não-conformidade pela existência do template.

---

## Propósito

Template canónico para units systemd de serviços WINDI. Todo novo serviço
DEVE seguir este padrão para garantir consistência operacional e segurança.

Desvios são permitidos mediante **justificação explícita documentada**.

## Template

```ini
[Unit]
Description={{SERVICE_ID}} — {{SERVICE_NAME}} v{{VERSION}}
Documentation=https://windi-domain.com/{{DOC_PATH}}/
After=network.target
Wants=network-online.target

[Service]
Type=simple
User=windi
Group=windi
WorkingDirectory=/opt/windi/{{SERVICE_DIR}}
ExecStart={{EXEC_COMMAND}}
Restart=always
RestartSec=5
StandardOutput=append:/opt/windi/logs/{{LOG_NAME}}.log
StandardError=append:/opt/windi/logs/{{LOG_NAME}}.log

# Security hardening (OBRIGATÓRIO)
NoNewPrivileges=yes
ProtectSystem=strict
ReadWritePaths=/opt/windi/data /opt/windi/logs /opt/windi/{{SERVICE_DIR}}

[Install]
WantedBy=multi-user.target
```

## Variáveis

| Variável | Exemplo | Descrição |
|----------|---------|-----------|
| `{{SERVICE_ID}}` | `W-DEV-API-001` | ID canónico do serviço |
| `{{SERVICE_NAME}}` | `WINDI Developer API` | Nome legível |
| `{{VERSION}}` | `1.1.0` | Versão semântica |
| `{{DOC_PATH}}` | `dev-api/v1/docs` | Path da documentação |
| `{{SERVICE_DIR}}` | `w-dev-api-001` | Directório em /opt/windi/ |
| `{{EXEC_COMMAND}}` | Ver nota abaixo | Comando de execução |
| `{{LOG_NAME}}` | `dev-api` | Nome base do ficheiro de log |

### Nota sobre {{EXEC_COMMAND}}

O comando varia conforme a stack do serviço:

| Stack | Exemplo |
|-------|---------|
| **Python/uvicorn** | `/usr/bin/python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8200` |
| **Python/gunicorn** | `/usr/bin/python3 -m gunicorn -w 4 -b 0.0.0.0:8200 app:app` |
| **Node.js** | `/usr/bin/node /opt/windi/{{SERVICE_DIR}}/server.js` |
| **Go binary** | `/opt/windi/{{SERVICE_DIR}}/bin/service` |

## Campos FIXOS (não alterar)

- `User=windi` / `Group=windi`
- `Restart=always` / `RestartSec=5`
- Security hardening completo
- `WantedBy=multi-user.target`

## ⚠️ Aviso: ReadWritePaths

`ProtectSystem=strict` bloqueia escrita em todo o sistema excepto nos paths
listados em `ReadWritePaths`. **Se o serviço escrever fora destes paths, falha
silenciosamente** — sem erro visível, apenas operação que não acontece.

Acrescentar TODOS os directórios onde o serviço precisa de escrever:

```ini
# Exemplo: serviço que também escreve em /opt/windi/media/
ReadWritePaths=/opt/windi/data /opt/windi/logs /opt/windi/{{SERVICE_DIR}} /opt/windi/media
```

Para diagnosticar falhas silenciosas de escrita:
```bash
journalctl -u windi-{{service}}.service | grep -i "denied\|permission"
```

## Instalação

```bash
sudo cp windi-{{service}}.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable windi-{{service}}.service
sudo systemctl start windi-{{service}}.service
```

## Verificação

```bash
systemctl status windi-{{service}}.service
journalctl -u windi-{{service}}.service -f
```

---

*WINDI Publishing House · Liga IA+H · Kempten, Bavaria · 2026*
*"Reference First → Mandate Later"*
