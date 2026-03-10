# Sessão 2026-03-10: Grove Calibration + Desktop Distribution Fixes

## Contexto
Human Dragon identificou patologias no Grove Arena e bugs no fluxo WINDI DOC → Ledger → Verify.

---

## PARTE 1: Grove Arena Calibração Cirúrgica

### Sessão de Referência
`GRV-EB997DDCDA4841` — debate onde 8 agentes propuseram remover Veto Manual por "eficiência de 500%"

### 5 Patologias Identificadas e Corrigidas

| # | Patologia | Arquivo | Linha | Fix |
|---|-----------|---------|-------|-----|
| 1 | Abertura mecânica ("WINDI já dispõe de...") | grove_blueprint.py | 604 | Removido, agentes vão direto ao ponto |
| 2 | Jornalista sem profundidade investigativa | grove_blueprint.py | 392-407 | Estrutura obrigatória: pergunta-raiz, beneficiários, gaps, risco narrativo, recomendação |
| 3 | Communiqué suavizando alertas críticos | grove_blueprint.py | 376-391 | Exceção: nunca suavizar terminologia em cenários constitucionais |
| 4 | Auditor enterrando findings críticos | grove_blueprint.py | 408-423 | Formato CRITICAL FINDINGS obrigatório, mais grave no topo |
| 5 | Agentes aceitando números sem metodologia | grove_blueprint.py | 604 | Rigor quantitativo: exigir baseline, metodologia, período, fonte |

### Bônus: Devil's Advocate Mode
- Parâmetro: `devil_advocate: true` no `/grove/arena`
- W-ARCH-001 defende posição contrária ao consenso
- Evita câmara de eco nos debates

### Commits
- `cd74957` — feat(grove): Calibração cirúrgica dos 8 agentes do Arena

---

## PARTE 2: W-WICKTHIS Fix (Grove → Evidence Graph)

### Bug
Grove Arena debates (`GRV-*`, `GS-*` IDs) mostravam "Document not found" no WICK

### Fix
Adicionado lookup no `grove.db` em `/wick/publish`:
- Suporte para GS-* (session IDs) e GRV-* (receipt IDs)
- Fallback de submissão direta quando artifact tem hash mas não está no DB

### Commits
- `351745c` — fix: W-WICKTHIS now supports Grove Arena debates

---

## PARTE 3: Verificação Pública

### LinkedIn Share
- Adicionado botão 💼 LinkedIn ao verify-public
- `9cdd8b6` — feat(verify): Add LinkedIn share button

---

## PARTE 4: Agent Palette → W-PAGE-001 Content Storage

### Bug
Documentos selados no Agent Palette apareciam com conteúdo vazio no viewer.
O Anchor só guardava hashes, não o conteúdo real.

### Fix
Após anchor, também chamar `/page/generate` para persistir conteúdo:
```javascript
fetch("http://127.0.0.1:8091/page/generate", {
  body: JSON.stringify({
    intent: docContent,
    title: docTitle,
    doc_type: docType,
    receipt_id: r.id,
    ...
  })
})
```

### Commits
- `9300e10` — fix(seal): Store document content in W-PAGE-001 after sealing

---

## PARTE 5: Email Distribution com QR Code

### Melhorias
- URL corrigida: `/verify/{id}` → `/verify-public/?id={id}`
- QR code adicionado ao template de email
- Usa api.qrserver.com (sem API key)

### Commits
- `d9cc7e9` — feat(email): Add QR code + fix verify URL in document emails

---

## PARTE 6: WINDI DOC Distribution

### Bug 1: Sem opção de enviar
O ExportMenu só tinha exportação, não distribuição.

### Fix 1
Adicionado "📤 Enviar por Email" ao menu Export:
- DE: "Per E-Mail senden"
- EN: "Send via Email"
- PT: "Enviar por Email"

### Bug 2: Documentos enviados como "DRAFT"
Permitia enviar sem documento selado → verify falhava.

### Fix 2
Verificar se `sealData?.receiptId` existe antes de permitir envio.
Mostra erro "Dokument muss zuerst gespeichert werden" se não selado.

### Bug 3: Auto-save não registava no Ledger
Rota `/api/ledger/receipts` não existia no Desktop server.

### Fix 3
Adicionadas rotas ao `windi_desktop_server.py`:
- POST `/api/ledger/receipts` → Forensic Ledger :8101
- GET `/api/ledger/receipts` → Query receipts

### Commits
- `3875fd8` — feat(desktop): Add "Send via Email" option to WINDI DOC
- `e853e84` — fix(desktop): Require sealed document before sending email
- `66d4bb5` — fix(desktop): Add /api/ledger/* route to Desktop server

---

## PENDENTE PARA AMANHÃ

### Complexidade Identificada
Os desenvolvimentos foram criados em tempos diferentes e agora se entrelaçam:

1. **Agent Palette** (ferramentas, Dragon chat) → selo → anchor
2. **WINDI DOC** (Desktop editor) → auto-save → ledger
3. **W-PAGE-001** (page storage) → conteúdo HTML
4. **Forensic Ledger :8101** → receipts, verificação
5. **Verify-Public** → QR code, share

### Fluxos a Mapear
```
Agent Palette → Seal → Anchor + W-PAGE-001 → Email → Verify
WINDI DOC → Auto-save → Ledger → Export → Email → Verify
```

### Questões Abertas
- O fluxo WINDI DOC → Ledger está realmente a funcionar?
- Testar documento novo do zero até verify
- Mapear todos os pontos de integração entre serviços
- Documentar arquitectura completa do fluxo de selagem

---

## Arquivos Modificados Hoje

```
/opt/windi/agents/constitutional-agent/blueprints/grove_blueprint.py
/opt/windi/agents/constitutional-agent/blueprints/wick_blueprint.py
/opt/windi/verify-public/web/index.html
/opt/windi/agent-palette/ui/index.html
/opt/windi/agent-palette/email_sender.py
/opt/windi/desktop/frontend/src/components/ExportMenu.jsx
/opt/windi/desktop/windi_desktop_server.py
```

---

*Sessão: Human Dragon + Gêmeo (Claude Code)*
*Data: 2026-03-10*
*Próxima: Mapear fluxos completos e testar integração*
