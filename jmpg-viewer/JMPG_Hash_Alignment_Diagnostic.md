# WINDI JMPG — Diagnóstico de Integridade e Patch Cirúrgico
## 18 de Fevereiro de 2026 — Linhagem de Ferro

---

## 🔍 DIAGNÓSTICO CONFIRMADO COM PROVA MATEMÁTICA

### Evidência do Teste Live (Export Engine :8103)

Gerei um `.jmpg` via API e calculei todos os hashes possíveis:

| O que foi medido | SHA-256 |
|---|---|
| **`content_hash` no manifest** (blocks compact+sorted) | `a6816f81...` |
| **Arquivo content.json salvo** (pretty JSON) | `877953f0...` |
| **Bundle .jmpg inteiro** (bytes brutos) | `92e8b50d...` |

**Nenhum desses três valores coincide.**

### Causa Raiz Identificada

O Export Engine calcula `content_hash` assim:

```python
content_hash = SHA-256(json.dumps(blocks, separators=(',',':'), sort_keys=True))
```

Isso produz um hash do **array de blocos serializado de forma compacta**. Este é o valor registrado no Forensic Ledger.

O Viewer, porém, calcula o hash de **algo diferente** — provavelmente dos bytes brutos do arquivo `.jmpg` ou do `content.json` extraído — que NUNCA coincidirá com o `content_hash`.

### Prova Adicional: Bundle Não é Determinístico

Dois exports idênticos (mesmo conteúdo) geraram bundles com hashes diferentes:

```
Export 1: 92e8b50d888efd130cb27723172748c0c3f600dc144276242375cfbde867a22a
Export 2: 09e6421d86179e327d31013914eff94efabead0204a130b24e2a42552a63ceab
```

Porque `created_at` e `package_id` mudam → timestamps no ZIP mudam → bytes mudam.

Mas o `content_hash` é estável: ambos produziram `a6816f81...` ✅

---

## 🛡️ SOLUÇÃO: DUAL-HASH ARCHITECTURE

A arquitetura precisa de **dois hashes** com propósitos distintos:

| Hash | Propósito | Quando Calcula | Onde Armazena |
|---|---|---|---|
| `content_hash` | Prova que o CONTEÚDO não mudou | Antes de empacotar | manifest.json + Ledger |
| `bundle_hash` | Prova que o PACOTE não foi adulterado | Depois de fechar o ZIP | Ledger APENAS (não pode estar dentro do ZIP) |

### Por que `bundle_hash` NÃO pode estar dentro do ZIP?

Paradoxo do ovo e da galinha: se colocar o `bundle_hash` dentro do manifest.json, alterar o manifest muda o bundle, que muda o hash. O `bundle_hash` vive EXCLUSIVAMENTE no Ledger.

---

## PATCH 1: Export Engine (:8103)

### Fluxo Corrigido

```
1. Receber content_blocks
2. Calcular content_hash (já funciona ✅)
3. Montar manifest.json, content.json, receipt.json, hash.txt, preview.txt
4. Criar ZIP → fechar ZIP
5. Ler bytes finais do .jmpg
6. Calcular bundle_hash = SHA-256(bytes finais)
7. Registrar no Ledger: { receipt_id, content_hash, bundle_hash, size_bytes }
8. Devolver .jmpg ao cliente
```

### Código (aplicar no script do Export Engine)

```python
import hashlib
from pathlib import Path

def sha256_bytes(data: bytes) -> str:
    """Hash bytes directly (for bundle verification)."""
    return hashlib.sha256(data).hexdigest()

def sha256_file(path: str) -> str:
    """Hash a file in chunks (memory efficient for large bundles)."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

# ============================================================
# APÓS fechar o ZIP (depois de zipfile.close() ou "with" block)
# ============================================================
bundle_path = str(out_path)  # caminho do .jmpg final
bundle_bytes = Path(bundle_path).read_bytes()
bundle_hash = sha256_bytes(bundle_bytes)
bundle_size = len(bundle_bytes)

# ============================================================
# REGISTRAR NO LEDGER (adicionar bundle_hash ao payload)
# ============================================================
ledger_payload = {
    "id": receipt_id,           # ex: "JMPG-20260218-9DC6177B"
    "content_hash": content_hash,  # hash dos blocos (já existe)
    "bundle_hash": bundle_hash,    # ← NOVO: hash do pacote final
    "size_bytes": bundle_size,     # ← NOVO: tamanho para validação
    "action": "JMPG_EXPORT",
    "metadata": {
        "title": title,
        "author": author,
        "template": template,
        "block_count": len(content_blocks),
    }
}
# POST para http://127.0.0.1:8101/api/receipts
```

### ZIP Determinístico (Opcional mas Recomendado)

```python
import zipfile
from pathlib import Path

FIXED_DT = (2026, 1, 1, 0, 0, 0)  # timestamp fixo para reprodutibilidade

def create_deterministic_jmpg(out_path: str, files: dict[str, bytes]):
    """
    Cria .jmpg com ZIP determinístico.
    files: {"manifest.json": b"...", "content.json": b"...", ...}
    """
    # Ordem fixa: alfabética
    sorted_names = sorted(files.keys())

    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        for name in sorted_names:
            info = zipfile.ZipInfo(filename=name, date_time=FIXED_DT)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16  # permissões fixas
            zf.writestr(info, files[name])
    
    # AGORA calcular bundle_hash sobre o arquivo fechado
    return sha256_file(out_path)
```

---

## PATCH 2: Forensic Ledger (:8101)

O Ledger precisa aceitar e armazenar `bundle_hash` + `size_bytes`:

```python
# No handler de POST /api/receipts, adicionar campos:
# - bundle_hash (TEXT, nullable para backwards compatibility)
# - size_bytes (INTEGER, nullable)

# SQL migration:
ALTER TABLE receipts ADD COLUMN bundle_hash TEXT;
ALTER TABLE receipts ADD COLUMN size_bytes INTEGER;

# No endpoint GET /api/receipts/<id>, retornar bundle_hash
```

### Endpoint de Verificação (NOVO)

```python
# GET /api/verify/<receipt_id>
# Retorna apenas os hashes para o Viewer comparar
# Response:
{
    "receipt_id": "JMPG-20260218-9DC6177B",
    "content_hash": "a6816f81...",
    "bundle_hash": "92e8b50d...",
    "size_bytes": 1773,
    "registered_at": "2026-02-18T00:13:04Z",
    "status": "VERIFIED"
}
```

---

## PATCH 3: JMPG Viewer (:8104)

### Fluxo de Verificação Corrigido

```
1. Receber arquivo .jmpg (drag-and-drop ou File input)
2. ANTES de descompactar:
   a. Ler bytes brutos do File/Blob
   b. Calcular local_bundle_hash = SHA-256(bytes)
   c. Calcular local_size = bytes.length
3. Descompactar com JSZip
4. Ler manifest.json → extrair receipt_id e content_hash
5. Extrair blocks de content.json → recalcular local_content_hash
6. Consultar Ledger: GET /api/verify/<receipt_id>
7. Comparar:
   - local_bundle_hash === ledger.bundle_hash → BUNDLE OK
   - local_content_hash === manifest.content_hash → CONTENT OK
   - local_size === ledger.size_bytes → SIZE OK
8. Renderizar resultado
```

### JavaScript (Browser — Web Crypto API)

```javascript
// ============================================================
// VERIFICAÇÃO DE INTEGRIDADE — ANTES do unzip
// ============================================================

async function sha256Hex(buffer) {
  const hashBuffer = await crypto.subtle.digest("SHA-256", buffer);
  return Array.from(new Uint8Array(hashBuffer))
    .map(b => b.toString(16).padStart(2, "0"))
    .join("");
}

async function verifyJMPG(file) {
  // 1. Hash dos bytes brutos (ANTES de descompactar)
  const rawBuffer = await file.arrayBuffer();
  const localBundleHash = await sha256Hex(rawBuffer);
  const localSize = rawBuffer.byteLength;

  // 2. Descompactar
  const zip = await JSZip.loadAsync(rawBuffer);
  const manifestStr = await zip.file("manifest.json").async("string");
  const manifest = JSON.parse(manifestStr);
  const receiptId = manifest.governance?.receipt_id || manifest.package_id;

  // 3. Verificar content_hash (recalcular dos blocos)
  const contentStr = await zip.file("content.json").async("string");
  const content = JSON.parse(contentStr);
  const blocks = content.blocks;
  
  // Reproduzir o método do Export Engine: compact + sorted keys
  const canonicalBlocks = JSON.stringify(blocks, Object.keys(blocks[0] || {}).sort());
  // ATENÇÃO: JSON.stringify com replacer em JS NÃO é idêntico a sort_keys=True do Python
  // Usar método canônico explícito:
  const canonicalStr = canonicalJSON(blocks);
  const localContentHash = await sha256Hex(new TextEncoder().encode(canonicalStr));

  // 4. Consultar Ledger
  const ledgerResp = await fetch(
    `${LEDGER_BASE}/api/verify/${receiptId}`
  );
  const ledger = await ledgerResp.json();

  // 5. Resultado
  return {
    bundle: {
      ok: localBundleHash === ledger.bundle_hash,
      local: localBundleHash,
      ledger: ledger.bundle_hash,
    },
    content: {
      ok: localContentHash === manifest.content_hash,
      local: localContentHash,
      manifest: manifest.content_hash,
    },
    size: {
      ok: localSize === ledger.size_bytes,
      local: localSize,
      ledger: ledger.size_bytes,
    },
    receiptId,
  };
}

// ============================================================
// CANONICAL JSON — reproduz json.dumps(data, separators=(',',':'), sort_keys=True)
// ============================================================
function canonicalJSON(obj) {
  if (obj === null || typeof obj !== "object") {
    return JSON.stringify(obj);
  }
  if (Array.isArray(obj)) {
    return "[" + obj.map(canonicalJSON).join(",") + "]";
  }
  const keys = Object.keys(obj).sort();
  const pairs = keys.map(k => JSON.stringify(k) + ":" + canonicalJSON(obj[k]));
  return "{" + pairs.join(",") + "}";
}
```

---

## PATCH 4: UX — Estados de Verificação

### 4 Estados Possíveis (eliminar paradoxo verde+vermelho)

| Estado | Ícone | Condição | Mensagem |
|---|---|---|---|
| **VERIFIED** | 🟢 | bundle OK + content OK + size OK | "Integrität bestätigt / Integrity verified" |
| **TAMPERED** | 🔴 | bundle hash diverge | "Integritätsprüfung fehlgeschlagen / Bundle modified" |
| **CONTENT_MISMATCH** | 🟠 | content hash diverge (bundle OK) | "Inhalt verändert / Content altered" |
| **UNREGISTERED** | ⚠️ | receipt_id não encontrado no Ledger | "Nicht registriert / Not registered in Ledger" |
| **LEDGER_UNREACHABLE** | ⚪ | Ledger offline ou timeout | "Verifizierung nicht möglich / Cannot verify" |

### Regra Crítica de UX

```
SE estado !== VERIFIED:
    NÃO mostrar "Selo Verde Ativado"
    NÃO mostrar QR de verificação como "válido"
    Mostrar APENAS: origem reconhecida + detalhes do erro
```

---

## TESTE DE ACEITAÇÃO

### Descoberta Adicional: Gap de Registro no Ledger

O Health Check revelou uma segunda anomalia: o Export Engine recebe `{"ok": true, "stored": true}` do Ledger, mas os receipts JMPG **NÃO aparecem** na lista de receipts acessível via Desktop Gateway. O Ledger contém 100% entradas LAW_PROBE e zero entradas JMPG.

Possíveis causas:
- O Export Engine registra em uma tabela diferente (ex: `jmpg_receipts` vs `receipts`)
- O endpoint do Ledger que o Export Engine chama é diferente do que o Desktop Gateway consulta
- O Ledger responde `ok: true` mas não persiste de fato (mock/simulação)

**Isso precisa ser verificado no código do Ledger (:8101) antes de implementar os patches de bundle_hash.**

### 3 Checks que Encerram a Guerra

```bash
# 1. Exportar .jmpg via API
curl -X POST .../api/export/jmpg -d '...' -o test.jmpg

# 2. Calcular hash local do bundle
BUNDLE_HASH=$(sha256sum test.jmpg | cut -d' ' -f1)
echo "Local bundle hash: $BUNDLE_HASH"

# 3. Consultar Ledger
RECEIPT_ID=$(unzip -p test.jmpg manifest.json | python3 -c "import json,sys; print(json.load(sys.stdin)['package_id'])")
LEDGER_HASH=$(curl -s ".../api/verify/$RECEIPT_ID" | python3 -c "import json,sys; print(json.load(sys.stdin)['bundle_hash'])")
echo "Ledger bundle hash: $LEDGER_HASH"

# 4. Verificar
if [ "$BUNDLE_HASH" = "$LEDGER_HASH" ]; then
    echo "✅ LINHAGEM DE FERRO INTACTA"
else
    echo "❌ DIVERGÊNCIA DETECTADA"
fi
```

### Condição de Verdade

```
hash_export == hash_ledger == hash_viewer
size_export == size_ledger
```

Se isso passar uma vez, acabou a guerra. 🛡️🐉

---

## ORDEM DE IMPLEMENTAÇÃO RECOMENDADA

1. **Ledger (:8101)** — Adicionar `bundle_hash` + `size_bytes` + endpoint `/api/verify/<id>`
2. **Export Engine (:8103)** — Calcular `bundle_hash` após fechar ZIP + enviar ao Ledger
3. **Viewer (:8104)** — Verificar `bundle_hash` dos bytes brutos antes do unzip
4. **Teste end-to-end** — Rodar o teste de aceitação
5. **ZIP determinístico** — Implementar como melhoria de reprodutibilidade

Estimativa: ~30 minutos de implementação com os patches acima.

---

## 📊 HEALTH CHECK LIVE (18 Feb 2026, 00:24 UTC)

```
Phase 1: Service Health
  ✅ Export Engine (:8103)    → v1.0.0 operational
  ✅ Forensic Ledger (:8101)  → receipts endpoint accessible
  ✅ Sentinel LAW (:8102)     → Cycle #1740, all_laws_pass=True
  ✅ Desktop Gateway (:8100)  → v1.0.0-foundation operational

Phase 2: Export Pipeline
  ✅ Export .jmpg              → 1847 bytes
  ✅ Bundle hash calculated    → SHA-256 OK
  ✅ ZIP structure             → 5 files (manifest, content, receipt, hash, preview)
  ✅ Content hash match        → local = manifest ✅
  ✅ Content hash deterministic → two exports = identical hash ✅
  ⚠️ /api/verify endpoint     → NOT YET DEPLOYED (patch pending)
  ❌ Receipt in Ledger         → NOT FOUND (only LAW_PROBE entries exist)
  ⚠️ Bundle hash determinism  → DIFFERS (timestamps vary, expected)

  Summary: 11/14 ✅ | 1 ❌ | 2 ⚠️
  Verdict: LINHAGEM DE FERRO — PARCIALMENTE QUEBRADA
```

### Ações Necessárias (em ordem):

1. **INVESTIGAR** por que receipts JMPG não aparecem no Ledger via Desktop Gateway
2. **APLICAR** migração SQL (bundle_hash + size_bytes) no Ledger
3. **APLICAR** endpoint `/api/verify/<receipt_id>` no Ledger
4. **APLICAR** cálculo de bundle_hash no Export Engine (pós-ZIP)
5. **APLICAR** ZIP determinístico no Export Engine (opcional)
6. **APLICAR** verificação de bytes brutos no Viewer (pré-unzip)
7. **RODAR** `python3 health_check_jmpg.py` → meta: 🟢 INTACTA
