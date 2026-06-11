# G-SURF-3 — Measurement Run Protocol
**Target:** Safari iOS + Chrome Android reais
**Artifact:** `windi-seal-v2.html` v2.5 · Hash: `6777b4017799ac13`
**URL:** `https://windi-domain.com/artifacts/windi-seal-v2.html`
**Estado:** PENDENTE (aguarda Human Dragon com dispositivos físicos)

---

## Pré-requisitos

- [ ] iPhone com Safari (iOS 15+)
- [ ] Android com Chrome (v90+)
- [ ] Receipt válido no Ledger para teste: `DBED5A85` (KEYGEN-001)
- [ ] Conexão à internet (HTTPS obrigatório para câmara)

---

## Checklist Safari iOS

### 1. Carregamento Inicial
- [ ] Página carrega sem erros de consola
- [ ] UI renderiza correctamente (NOIR/KLAR toggle)
- [ ] Trilíngue funciona (DE/EN/PT)

### 2. Modo CAPTURA — Foto
- [ ] Botão 📷 activa viewfinder
- [ ] Câmara frontal/traseira (flip) funciona
- [ ] Captura foto → hash aparece
- [ ] Botão SELAR MOMENTO → hash viaja para API

### 3. Modo CAPTURA — Vídeo (Safari iOS fix)
- [ ] Botão 🎬 activa gravação
- [ ] Indicador REC aparece com timer
- [ ] Gravação pára correctamente
- [ ] **CRÍTICO:** Vídeo grava em mp4 (não webm)
- [ ] Hash calculado sem erro
- [ ] Se erro no MediaRecorder → reportar mensagem exacta

### 4. Modo CAPTURA — Áudio
- [ ] Botão 🎙️ activa gravação áudio
- [ ] Timer funciona
- [ ] Paragem gera ficheiro áudio
- [ ] Hash calculado

### 5. Modo VERIFICAR — 3 Estados
- [ ] Inserir `DBED5A85` → **MOMENTO PRESERVADO** (verde)
- [ ] Inserir `DEMO` ou `demo` → **DEMONSTRAÇÃO** (azul)
- [ ] Inserir hash inexistente → **NÃO ENCONTRADO** (âmbar) + disclaimer

### 6. Modo EDITOR
- [ ] Carregar background funciona
- [ ] PiP vídeo posiciona-se
- [ ] Texto overlay aparece
- [ ] Exportar gera hash

---

## Checklist Chrome Android

### 1. Carregamento Inicial
- [ ] Página carrega sem erros
- [ ] UI NOIR/KLAR + trilíngue OK

### 2. Modo CAPTURA — Foto
- [ ] Câmara activa
- [ ] Flip funciona
- [ ] Captura + hash OK

### 3. Modo CAPTURA — Vídeo (webm)
- [ ] Gravação inicia
- [ ] Timer REC funciona
- [ ] Vídeo grava em webm (codec vp9)
- [ ] Hash calculado

### 4. Modo CAPTURA — Áudio
- [ ] Gravação OK
- [ ] Hash OK

### 5. Modo VERIFICAR — 3 Estados
- [ ] `DBED5A85` → MOMENTO PRESERVADO ✓
- [ ] `demo` → DEMONSTRAÇÃO ✓
- [ ] inexistente → NÃO ENCONTRADO ✓

### 6. Modo EDITOR
- [ ] Background + PiP + texto OK

---

## Erros a Capturar

Se qualquer teste falhar, registar:
1. **Dispositivo:** modelo exacto (ex: iPhone 14 Pro, Pixel 7)
2. **OS Version:** (ex: iOS 17.4, Android 14)
3. **Browser Version:** (ex: Safari 17, Chrome 125)
4. **Erro:** mensagem de consola ou comportamento
5. **Screenshot/Gravação:** se possível

---

## Resultado Esperado

Após testes bem-sucedidos em ambos os dispositivos:

```
G-SURF-3: ✅ VERIFIED
- Safari iOS: PASS (foto/vídeo/áudio + 3 estados)
- Chrome Android: PASS (foto/vídeo/áudio + 3 estados)
- Tester: [Human Dragon]
- Data: [YYYY-MM-DD]
- V2.5 Hash: 6777b4017799ac13
```

---

## Após Verificação

1. Actualizar GUARDIAN-REVIEW com resultados
2. Selar G-SURF-3 no Ledger
3. Publicar V2.5 como versão de produção

---

*AI processes. Human decides. WINDI guarantees.*
