#!/bin/bash
# 1. VARREDURA E EXTERMÍNIO FÍSICO (O Pente Fino)
echo "[SENTINEL] Iniciando varredura de impurezas..."
find /workspace/windi -name "*.so" | grep -iE "cuda|vllm|flash_attn|llvmlite" | xargs rm -f
rm -rf /root/.cache/pip/*

# 2. AUDITORIA E PUBLICAÇÃO (A Verdade na Embaixada)
echo "[SENTINEL] Atualizando registros na Embaixada..."
python3 /workspace/windi_public_audit/embassy_publisher.py

echo "[SENTINEL] Ciclo de Virtude concluído."
