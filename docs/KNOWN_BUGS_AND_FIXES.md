
## BUG-001: Distribution Engine — Receipt ID Mismatch (Fixed 2026-03-07)

### Sintoma
- Email de distribuição mostra `receipt_id` (ex: COM-2026-1437)
- Verificação retorna "DOCUMENT NOT FOUND"
- Ledger contém apenas `dist_id` (ex: DIST-20260307...)

### Causa Raiz
O `seal_in_ledger()` usava sempre `dist_id` ao invés do `receipt_id` fornecido pelo Communiqué Engine.

### Fix
**Arquivo:** `/opt/windi/distribution-engine/distribution_server.py`
**Linha:** ~617

```python
# ANTES (BUG):
ledger_result = seal_in_ledger(dist_id=dist_id, ...)

# DEPOIS (FIX):
seal_id = receipt_id if receipt_id else dist_id
ledger_result = seal_in_ledger(dist_id=seal_id, ...)
```

### Diagnóstico Rápido
```bash
# Ver últimas distribuições
sqlite3 /opt/windi/data/distribution.db "SELECT dist_id, receipt_id FROM distribution_ledger ORDER BY id DESC LIMIT 3;"

# Verificar se receipt_id existe no Ledger
curl -s "http://127.0.0.1:8101/api/receipts/COM-2026-XXXX"
```

### Status
✅ Corrigido em 2026-03-07 15:43 UTC
