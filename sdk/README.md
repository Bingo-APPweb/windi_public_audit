# WINDI SDK v1.1

> "Escala não vem de fazer tudo igual.
>  Vem de garantir que tudo termina da mesma forma."

**Liga IA+H · Kempten, Bavaria · 05 Abril 2026**

---

## O Que É

O WINDI SDK é o **Código Genético** de todos os produtos WINDI.
Cada produto é uma experiência diferente, mas todos partilham o mesmo núcleo de prova.

```
PRODUTO → EXPERIÊNCIA ESPECÍFICA → WINDI CORE → PROVA → MUNDO
```

---

## As 5 Funções Sagradas

| Função | O Que Faz | Invariante |
|--------|-----------|------------|
| `seal()` | Compute hash + I9 Gate | **I9** (Vontade Humana) |
| `ledger()` | Ancoragem eterna no Ledger | **I11** (Imutabilidade) |
| `render_jmpg()` | Prova visual verificável | Clareza |
| `distribute()` | Distribuição PRIVADA | Alcance (chat pessoal) |
| `publish()` | Distribuição PÚBLICA (§137) | **§122.4** (Link Only) |

---

## Quick Start

```python
from windi_core import seal, ledger, render_jmpg, distribute, publish

# 1. SEAL — Compute hash (I9: human_approved=True)
seal_result = await seal("/path/to/document.pdf", "did:windi:user:001")

# 2. LEDGER — Anchor eternally (I11)
receipt = await ledger(seal_result, doc_type="contract")

# 3. RENDER — Create proof card
jmpg = await render_jmpg(receipt.receipt_id, title="Contract signed")

# 4a. DISTRIBUTE — Send to PRIVATE chat (sendPhoto)
await distribute(receipt.receipt_id, chat_id="8618440285", lang="PT")

# 4b. PUBLISH — Post to PUBLIC channel (§137 — LINK ONLY)
await publish(receipt.receipt_id, chat_id="@windi_public", lang="EN")
```

### §137 — Medium-Agnostic Truth Distribution

> "O canal Telegram não transmite ficheiros. Transmite acesso."

Para distribuição PÚBLICA, usar sempre `publish()`:
- Telegram transcodifica imagens → quebra SHA-256
- `publish()` envia apenas LINK → integridade mantida
- O medium APONTA para a prova. Nunca CARREGA a prova.

---

## Pipeline Completo (1 Linha)

```python
from windi_core import prove_and_share

result = await prove_and_share(
    "/path/to/artifact.pdf",
    wallet_id="did:windi:user:001",
    title="Document sealed",
    chat_id="8618440285",  # Optional: Telegram
    lang="PT"
)

print(result["verify_url"])  # Public verification
print(result["image_url"])   # JMPG proof card
```

---

## Criar Novo Produto (1 Hora)

1. **Copiar template:**
   ```bash
   cp /opt/windi/sdk/templates/new_product.py /opt/windi/my-product/server.py
   ```

2. **Customizar config:**
   ```python
   PRODUCT_CONFIG = WindiProduct(
       name="WINDI Medical Records",
       code="MEDICAL",
       port=8200,
       description="Medical record certification",
       artifact_types=["application/pdf", "image/dicom"],
   )
   ```

3. **Adicionar endpoints específicos:**
   ```python
   @app.post("/diagnose")
   async def process_diagnosis(...):
       # Your specific logic
       pass
   ```

4. **Deploy:**
   ```bash
   python3 server.py
   ```

---

## Estrutura

```
/opt/windi/sdk/
├── windi_core/
│   ├── __init__.py     # Exports
│   ├── core.py         # 4 Sacred Functions
│   └── models.py       # Data structures
├── templates/
│   └── new_product.py  # Product template
├── examples/
│   └── ...
└── README.md
```

---

## Invariantes

Todos os produtos WINDI respeitam:

| ID | Nome | Impacto |
|----|------|---------|
| **I9** | Proibição de Autonomia | `human_approved=True` obrigatório |
| **I11** | Permanência de Evidência | Ledger imutável após seal |

---

## Portas Reservadas

| Porta | Serviço | Status |
|-------|---------|--------|
| 8101 | Forensic Ledger | 🔒 SEALED |
| 8114 | Verify Public | ✅ LIVE |
| 8128 | VD-CUT | ✅ LIVE |
| 8131 | VD-MASS | ✅ LIVE |
| 8132 | JMPG/COMM | ✅ LIVE |
| 8126 | Travel | ✅ LIVE |
| 8122 | Law | ✅ LIVE |

---

## Princípio Arquitectural

```
ESPECÍFICO NA EXPERIÊNCIA
UNIVERSAL NA INFRAESTRUTURA
```

- **VD-CUT** processa vídeo
- **LAW** processa documentos legais
- **TRAVEL** processa momentos
- **MEDICAL** processaria registos médicos

👉 Mas **TODOS** terminam em: `SEAL → LEDGER → VERIFY → JMPG → DISTRIBUTE`

---

## Frase Canónica

> "Não publicamos conteúdo. Emitimos prova."

---

**Liga IA+H · WINDI Publishing House**
*"AI processes. Human decides. WINDI guarantees."*
