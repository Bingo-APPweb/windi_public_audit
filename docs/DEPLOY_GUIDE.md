# WINDI Evidence Package — Deployment Guide
## Integração com Communiqué Engine (:8105)

**Data:** 2026-02-19
**Status:** READY FOR DEPLOY

---

## Deliverables Prontos

| Arquivo | Função |
|---------|--------|
| `EVIDENCE_PACKAGE_SCHEMA_v1.1.md` | Schema oficial — padrão de referência |
| `evidence_live.py` | Builder CLI — scan, hash, bundle, verify |
| `communique-multimedia.jsx` | Paper Sheet React — protótipo visual |
| `EV-20260219-0001.jmpg` | Primeiro bundle de teste (4 files, verified) |
| `EV-20260219-0001_manifest.json` | Manifest gerado automaticamente |

---

## Deploy no Strato (SSH)

### Step 1: Upload dos arquivos

```bash
# Do PC local:
scp evidence_live.py windi@87.106.29.233:/opt/windi/communique/
scp EVIDENCE_PACKAGE_SCHEMA_v1.1.md windi@87.106.29.233:/opt/windi/docs/
```

### Step 2: Criar diretório de evidence

```bash
ssh windi@87.106.29.233
mkdir -p /opt/windi/communique/evidence/
mkdir -p /opt/windi/communique/packages/
```

### Step 3: Testar o builder

```bash
cd /opt/windi/communique/
python3 evidence_live.py --help

# Build com evidência real:
python3 evidence_live.py build \
  --com COM-20260219-0001 \
  --dir ./evidence/ \
  --title "MULTIMEDIA COMMUNIQUÉ — First Prototype" \
  --category INCIDENT \
  --impact HIGH \
  --output ./packages/EV-20260219-0001.jmpg

# Verify:
python3 evidence_live.py verify --package ./packages/EV-20260219-0001.jmpg
```

### Step 4: Integrar com Communiqué Engine

O Communiqué Engine (:8105) precisa de um novo endpoint:

```python
# Adicionar ao communique_engine.py:

# POST /api/communique/multimedia — criar communiqué multimídia
# GET  /communique/{id}/evidence/verify — verificar evidence package
# GET  /communique/{id}/evidence/manifest — retornar manifest.json
```

### Step 5: Registrar no Ledger

```bash
# Após build, enviar hashes para o Ledger (:8101):
curl -X POST http://localhost:8101/api/receipts -H "Content-Type: application/json" -d '{
  "doc_type": "COMMUNIQUE_MULTIMEDIA",
  "content_hash": "<content_hash_from_manifest>",
  "bundle_hash": "<bundle_hash_from_build>",
  "impact_level": "HIGH",
  "category": "INCIDENT"
}'
```

---

## Workflow Completo

```
1. Operador captura evidência (screenshots, logs, vídeos)
   ↓
2. evidence_live.py scan + hash + bundle
   ↓
3. .jmpg criado com manifest.json + metadata/
   ↓
4. Communiqué Engine recebe bundle + texto trilíngue
   ↓
5. Engine registra no Ledger (content_hash + bundle_hash)
   ↓
6. Communiqué publicado com Paper Sheet Multimedia
   ↓
7. Verificação pública via /verify + /evidence/verify
```

---

## Próximos Passos

1. **Deploy evidence_live.py** no Strato
2. **Capturar evidência real** (screenshots do sistema)
3. **Gerar primeiro .jmpg real** com hashes genuínos
4. **Estender Communiqué Engine** para tipo MULTIMEDIA
5. **Publicar COM-20260219-0001** — primeiro Communiqué Multimedia da história WINDI

---

*WINDI Publishing House · Kempten, Bavaria*
*"AI processes. Human decides. WINDI guarantees."*
