#!/usr/bin/env python3
"""
WINDI Pioneer Toolkit — Sector Turismo Florianópolis
Atomiza fotos de passeios turísticos com selo forense.

Uso: python3 atomize_turismo.py foto_escuna.jpg
"""

import requests
import sys
import json
import os

# ══════════════════════════════════════════════════════════════════════════════
# CONFIGURAÇÃO — Edite apenas esta secção
# ══════════════════════════════════════════════════════════════════════════════

API_KEY = os.environ.get("WINDI_API_KEY", "wnd_live_SEU_KEY_AQUI")
BASE    = "https://windi-domain.com"

# ══════════════════════════════════════════════════════════════════════════════


def atomize_foto_turismo(caminho_foto: str) -> dict:
    """
    Atomiza uma foto de passeio turístico.

    Args:
        caminho_foto: Caminho para o ficheiro de imagem (jpg, png, etc.)

    Returns:
        dict com seed_id, forensic_hash, verify_url
    """
    if not os.path.exists(caminho_foto):
        print(f"ERRO: Ficheiro não encontrado: {caminho_foto}")
        sys.exit(1)

    print(f"Atomizando: {caminho_foto}")
    print("Enviando para WINDI Forensic Ledger...")
    print()

    with open(caminho_foto, 'rb') as f:
        response = requests.post(
            f"{BASE}/par/atomize",
            headers={"X-WINDI-API-Key": API_KEY},
            files={"frame": f},
            data={
                "schema_type":      "TOURISM",
                "activation_tier":  "SEED",
                "title":            f"Condições do passeio — {os.path.basename(caminho_foto)}",
                "description":      "Foto verificada pelo operador turístico",
                "operator_did":     "did:windi:turismo-floripa-pioneer"
            },
            timeout=30
        )

    if response.status_code != 200:
        print(f"ERRO: API retornou {response.status_code}")
        print(response.text)
        sys.exit(1)

    result = response.json()

    print("=" * 55)
    print("SEMENTE CRIADA")
    print(f"   Seed ID:    {result.get('seed_id', 'N/A')}")
    print(f"   Hash:       {result.get('forensic_hash','N/A')[:32]}...")
    print(f"   Verify URL: {result.get('verify_url', 'N/A')}")
    print("=" * 55)
    print()
    print("Envie este link ao seu cliente via WhatsApp:")
    print(f"   {result.get('verify_url', 'N/A')}")
    print()
    print("Ou imprima o QR Code e cole no seu material de divulgação.")

    return result


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python3 atomize_turismo.py <foto.jpg>")
        print()
        print("Exemplo:")
        print("  python3 atomize_turismo.py foto_escuna.jpg")
        print()
        print("Variável de ambiente:")
        print("  export WINDI_API_KEY=wnd_live_xxx")
        sys.exit(1)

    foto = sys.argv[1]
    atomize_foto_turismo(foto)
