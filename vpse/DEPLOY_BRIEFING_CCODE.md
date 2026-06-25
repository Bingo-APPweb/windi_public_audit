# VPSE — Briefing de Deploy para CCode (Strato)

**Para:** sessão CCode com acesso a `windi@87.106.29.233`
**De:** Claude.ai web · sessão 2026-06-25 · sob I9 do Human Dragon
**Estado:** MVP construído e validado localmente (15/15 checks PASS). Deploy é tarefa CCode.

---

## ⚠️ Lei I antes de tudo

Esta sessão web NÃO teve acesso ao Strato. Tudo abaixo sobre portas/nginx é `[estimado]`
da location-matrix v1.0 (18 Fev 2026). **CCode DEVE cumprir Mandatory Opening Sequence
antes de qualquer bind:**

```bash
cat /opt/windi/CLAUDE.md
tail -150 /opt/windi/CLAUDE-HISTORY.md
```

## ⚠️ GOLDEN RULE — porta a confirmar ANTES de bind

A porta `8120` no código é **placeholder**, não decisão. Verificar primeiro:

```bash
ss -tlnp | grep -E ':81[0-9][0-9]' | sort        # ver portas vivas
grep -rn "8120" /etc/nginx/sites-enabled/        # ver se nginx já referencia
```

Se `8120` estiver ocupada → escolher próxima livre e reportar ao Human Dragon
para autorização I9 antes de selar. **Não alterar nginx/systemd sem autorização explícita.**

---

## Passos de deploy (após autorização I9 da porta)

```bash
# 1. Copiar pacote para o servidor
#    (de onde o CCode tiver o tarball vpse_mvp.tar.gz)
mkdir -p /opt/windi/vpse
tar xzf vpse_mvp.tar.gz -C /opt/windi/vpse

# 2. Venv local (soberania, sem poluir sistema)
cd /opt/windi/vpse
python3 -m venv .venv
.venv/bin/pip install fastapi uvicorn pydantic -q

# 3. Smoke test ANTES de systemd
VPSE_PORT=<PORTA_CONFIRMADA> .venv/bin/python -m uvicorn vpse_engine.service:app \
    --host 127.0.0.1 --port <PORTA_CONFIRMADA> &
sleep 2
curl -s http://127.0.0.1:<PORTA_CONFIRMADA>/health
python3 tests/test_bingo_podcast.py   # deve dar 15/15 PASS
kill %1

# 4. systemd (NÃO nohup — disco-over-document, systemd é a verdade)
sudo tee /etc/systemd/system/windi-vpse.service > /dev/null <<'UNIT'
[Unit]
Description=WINDI VPSE — Viability Pre-Screen Engine (Playground P0)
After=network.target

[Service]
Type=simple
User=windi
WorkingDirectory=/opt/windi/vpse
Environment=VPSE_PORT=<PORTA_CONFIRMADA>
ExecStart=/opt/windi/vpse/.venv/bin/python -m uvicorn vpse_engine.service:app --host 127.0.0.1 --port <PORTA_CONFIRMADA>
Restart=on-failure

[Install]
WantedBy=multi-user.target
UNIT

sudo systemctl daemon-reload
sudo systemctl enable --now windi-vpse
systemctl status windi-vpse --no-pager | head -15

# 5. nginx (SÓ se Human Dragon quiser expor publicamente)
#    location block ANTES de 'listen 443 ssl;', NUNCA aninhado.
#    sudo nginx -t SEMPRE antes de reload.
```

## Verificação anti-regressão (Non-Goals)

Confirmar que o serviço NÃO:
- escreve no Ledger (`:8101`) — grep no código por POST ao ledger deve dar vazio
- emite selo — não há chamada a seal/
- presume DID — `did_present` é sempre `false`

```bash
grep -rn "8101\|ledger\|seal\|POST" /opt/windi/vpse/vpse_engine/ || echo "limpo: sem efeitos colaterais"
```

## Pendente para sessão futura (scaffold, não morre)

1. **Ligação ao /farm/claim**: receipt-candidate morto → vivo só quando DID consumido.
2. **Refinamento LLM externo** no Risk/Compliance Scanner (windi-sovereignty-quality:
   tier HIGH justificado só aqui, onde qualidade vale o token). Hoje é 100% léxico local.
3. **Expansão do léxico** de domínios e sinais regulatórios.
4. **Selagem doutrinária** §VPSE-001 no Ledger — só após Human Dragon validar em produção.

## Update obrigatório de memória (Lei II + anti-pattern 6)

No fecho da sessão CCode que fizer o deploy:
- adicionar entrada em `CLAUDE-HISTORY.md`
- registar porta final em `windi-location-matrix` (formato:
  `vpse:<PORTA>:?/prescreen:/opt/windi/vpse/:σ`)
- atualizar `CLAUDE.md` no mesmo turno (selo sem atualização = selo invisível)
```
