#!/usr/bin/env python3
"""
WINDI Verify — Gerador de ícones PWA
Gera todos os tamanhos necessários a partir de um SVG base
usando cairosvg (se disponível) ou cria SVGs placeholders.

Instalar: pip install cairosvg --break-system-packages

Deploy:
  python3 generate-icons.py
  cp icons/ /opt/windi/verify-public/web/icons/
"""

import os
import sys

ICONS_DIR = "icons"
SIZES = [72, 96, 128, 192, 512]

# SVG base do ícone WINDI Verify
# Fundo escuro #2C2C2A + W teal + escudo
ICON_SVG = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512">
  <!-- Background -->
  <rect width="512" height="512" rx="96" fill="#2C2C2A"/>

  <!-- Shield shape -->
  <path d="M256 80 L380 130 L380 270 Q380 360 256 430 Q132 360 132 270 L132 130 Z"
        fill="#0F6E56" opacity="0.9"/>

  <!-- W letterform -->
  <text x="256" y="310"
        font-family="Arial, sans-serif"
        font-size="180" font-weight="700"
        text-anchor="middle"
        fill="#F5F0E0"
        letter-spacing="-8">W</text>

  <!-- Verify checkmark -->
  <circle cx="360" cy="360" r="64" fill="#2C2C2A"/>
  <circle cx="360" cy="360" r="56" fill="#5DCAA5"/>
  <path d="M330 360 L350 380 L395 335"
        stroke="#2C2C2A" stroke-width="10"
        stroke-linecap="round" stroke-linejoin="round"
        fill="none"/>
</svg>'''

# SVG maskable — safe zone 80% (mais padding para lojas)
ICON_MASKABLE_SVG = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512">
  <!-- Background full bleed -->
  <rect width="512" height="512" fill="#2C2C2A"/>

  <!-- Safe zone content (80% = 204px margin each side) -->
  <!-- Shield — menor para caber na safe zone -->
  <path d="M256 110 L350 148 L350 258 Q350 330 256 390 Q162 330 162 258 L162 148 Z"
        fill="#0F6E56" opacity="0.9"/>

  <!-- W letterform — escalado para safe zone -->
  <text x="256" y="290"
        font-family="Arial, sans-serif"
        font-size="150" font-weight="700"
        text-anchor="middle"
        fill="#F5F0E0"
        letter-spacing="-6">W</text>

  <!-- Check badge -->
  <circle cx="340" cy="340" r="52" fill="#2C2C2A"/>
  <circle cx="340" cy="340" r="46" fill="#5DCAA5"/>
  <path d="M316 340 L333 357 L368 320"
        stroke="#2C2C2A" stroke-width="8"
        stroke-linecap="round" stroke-linejoin="round"
        fill="none"/>
</svg>'''

def generate_icons():
    os.makedirs(ICONS_DIR, exist_ok=True)

    # Tenta usar cairosvg para PNG real
    try:
        import cairosvg
        has_cairo = True
        print("✅ cairosvg disponível — gerando PNGs reais")
    except ImportError:
        has_cairo = False
        print("⚠️  cairosvg não disponível — guardando SVGs (renomear para .png ou instalar cairosvg)")

    # Ícones normais
    for size in SIZES:
        if has_cairo:
            out = os.path.join(ICONS_DIR, f"icon-{size}.png")
            cairosvg.svg2png(
                bytestring=ICON_SVG.encode(),
                write_to=out,
                output_width=size,
                output_height=size,
            )
        else:
            out = os.path.join(ICONS_DIR, f"icon-{size}.svg")
            with open(out, 'w') as f:
                f.write(ICON_SVG)
        print(f"  ✓ icon-{size}: {out}")

    # Maskable (192 + 512)
    for size in [192, 512]:
        if has_cairo:
            out = os.path.join(ICONS_DIR, f"icon-maskable-{size}.png")
            cairosvg.svg2png(
                bytestring=ICON_MASKABLE_SVG.encode(),
                write_to=out,
                output_width=size,
                output_height=size,
            )
        else:
            out = os.path.join(ICONS_DIR, f"icon-maskable-{size}.svg")
            with open(out, 'w') as f:
                f.write(ICON_MASKABLE_SVG)
        print(f"  ✓ icon-maskable-{size}: {out}")

    print(f"\n✅ {len(SIZES) + 2} ícones gerados em ./{ICONS_DIR}/")
    print("\nDeploy:")
    print(f"  cp -r {ICONS_DIR}/ /opt/windi/verify-public/web/icons/")

    if not has_cairo:
        print("\nPara gerar PNGs reais:")
        print("  pip install cairosvg --break-system-packages")
        print("  python3 generate-icons.py")

if __name__ == '__main__':
    generate_icons()
