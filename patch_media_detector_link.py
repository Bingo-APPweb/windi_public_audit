#!/usr/bin/env python3
"""
Patch: adiciona banner de destaque para media-detector.html
Injector: entre </section> das modes e <section class="philosophy">

Uso (Gêmeo no servidor):
  python3 patch_media_detector_link.py /opt/windi/verify-public/web/index.html
"""
import sys, shutil
from datetime import datetime

BANNER_CSS = """
  /* ── Media Detector Banner ── */
  .media-banner {
    margin: 0 auto 0;
    max-width: 960px;
    padding: 0 20px 32px;
  }
  .media-banner-inner {
    background: var(--text);
    color: var(--bg);
    border-radius: var(--radius);
    padding: 28px 32px;
    display: flex;
    align-items: center;
    gap: 28px;
    position: relative;
    overflow: hidden;
  }
  .media-banner-inner::before {
    content: '';
    position: absolute;
    top: 0; right: 0;
    width: 260px; height: 100%;
    background: linear-gradient(135deg, transparent 40%, rgba(83,74,183,0.18));
    pointer-events: none;
  }
  .media-banner-icon {
    font-size: 36px;
    flex-shrink: 0;
    line-height: 1;
  }
  .media-banner-body { flex: 1; }
  .media-banner-label {
    font-size: 11px; font-weight: 700;
    letter-spacing: 1px; text-transform: uppercase;
    opacity: 0.5; margin-bottom: 4px;
  }
  .media-banner-title {
    font-size: 18px; font-weight: 800;
    letter-spacing: -0.4px; margin-bottom: 6px;
  }
  .media-banner-sub {
    font-size: 13px; opacity: 0.65; line-height: 1.45;
  }
  .media-banner-tags {
    display: flex; gap: 8px; flex-wrap: wrap;
    margin-top: 10px;
  }
  .media-banner-tag {
    font-size: 11px; font-weight: 600;
    background: rgba(255,255,255,0.12);
    border: 1px solid rgba(255,255,255,0.18);
    border-radius: 20px; padding: 3px 10px;
    letter-spacing: 0.2px;
  }
  .media-banner-cta {
    flex-shrink: 0;
    background: var(--purple);
    color: #fff;
    text-decoration: none;
    font-size: 14px; font-weight: 700;
    padding: 12px 22px;
    border-radius: var(--radius-sm);
    display: flex; align-items: center; gap: 8px;
    transition: all 0.18s;
    white-space: nowrap;
    position: relative; z-index: 1;
  }
  .media-banner-cta:hover { opacity: 0.88; transform: translateY(-1px); }
  @media (max-width: 640px) {
    .media-banner-inner { flex-direction: column; align-items: flex-start; gap: 18px; padding: 22px 20px; }
    .media-banner-icon { font-size: 28px; }
    .media-banner-title { font-size: 16px; }
    .media-banner-cta { width: 100%; justify-content: center; }
  }"""

BANNER_HTML = """
<!-- ── Media Detector Banner ── -->
<div class="media-banner">
  <div class="media-banner-inner">
    <div class="media-banner-icon">🎬</div>
    <div class="media-banner-body">
      <div class="media-banner-label" data-i18n="media_label"></div>
      <div class="media-banner-title" data-i18n="media_title"></div>
      <div class="media-banner-sub" data-i18n="media_sub"></div>
      <div class="media-banner-tags">
        <span class="media-banner-tag" data-i18n="media_tag1"></span>
        <span class="media-banner-tag" data-i18n="media_tag2"></span>
        <span class="media-banner-tag" data-i18n="media_tag3"></span>
        <span class="media-banner-tag" data-i18n="media_tag4"></span>
      </div>
    </div>
    <a class="media-banner-cta"
       href="/verify-public/web/media-detector.html"
       data-i18n="media_cta"></a>
  </div>
</div>

"""

# i18n strings to inject
I18N_PT = {
    'media_label': 'Novo',
    'media_title': 'Media Detector — Vídeo · Imagem · Texto',
    'media_sub': 'Classifica qualquer conteúdo: VERIFIED · UNVERIFIABLE · INCONSISTENT. WINDI não declara "fake" — classifica verificabilidade.',
    'media_tag1': 'Vídeo',
    'media_tag2': 'Imagem',
    'media_tag3': 'Texto',
    'media_tag4': 'Heurísticas MVP',
    'media_cta': 'Analisar conteúdo →',
}

I18N_DE = {
    'media_label': 'Neu',
    'media_title': 'Media Detector — Video · Bild · Text',
    'media_sub': 'Klassifiziert beliebige Inhalte: VERIFIED · UNVERIFIABLE · INCONSISTENT. WINDI erklärt kein "Fake" — klassifiziert Verifizierbarkeit.',
    'media_tag1': 'Video',
    'media_tag2': 'Bild',
    'media_tag3': 'Text',
    'media_tag4': 'Heuristiken MVP',
    'media_cta': 'Inhalt analysieren →',
}

I18N_EN = {
    'media_label': 'New',
    'media_title': 'Media Detector — Video · Image · Text',
    'media_sub': 'Classifies any content: VERIFIED · UNVERIFIABLE · INCONSISTENT. WINDI does not declare "fake" — it classifies verifiability.',
    'media_tag1': 'Video',
    'media_tag2': 'Image',
    'media_tag3': 'Text',
    'media_tag4': 'MVP heuristics',
    'media_cta': 'Analyse content →',
}

def patch(path: str):
    with open(path, 'r', encoding='utf-8') as f:
        html = f.read()

    if 'media-banner' in html:
        print("✅ Banner já presente. Nada a fazer.")
        return

    bak = path + '.bak_mediabanner_' + datetime.now().strftime('%Y%m%d_%H%M%S')
    shutil.copy2(path, bak)
    print(f"🔒 Backup: {bak}")

    # 1. Inject CSS before closing </style>
    html = html.replace('</style>', BANNER_CSS + '\n</style>', 1)
    print("   ✓ CSS injectado")

    # 2. Inject i18n keys into the I18N object
    # Find the PT section and add keys
    for lang, keys in [('pt', I18N_PT), ('de', I18N_DE), ('en', I18N_EN)]:
        # Build the i18n string to inject
        i18n_str = ',\n'.join([f"    {k}: '{v}'" for k, v in keys.items()])

        # Find a good injection point - after m3_cta line
        search_pattern = f"m3_cta:"
        if search_pattern in html:
            # Find the line with m3_cta and inject after it
            lines = html.split('\n')
            new_lines = []
            for line in lines:
                new_lines.append(line)
                if 'm3_cta:' in line and ('QR Decoder' in line or 'QR-Decoder' in line):
                    # Add media detector i18n after this line
                    new_lines.append(f"    // Media Detector banner ({lang})")
                    for k, v in keys.items():
                        new_lines.append(f"    {k}: '{v}',")
            html = '\n'.join(new_lines)

    print("   ✓ i18n injectado (PT/DE/EN)")

    # 3. Inject HTML banner between modes </section> and philosophy section
    html = html.replace(
        '</section>\n\n<!-- Philosophy strip -->',
        '</section>\n' + BANNER_HTML + '\n<!-- Philosophy strip -->',
        1
    )
    print("   ✓ Banner HTML injectado (após mode cards)")

    with open(path, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"\n✅ Patch aplicado: {path}")
    print("🔗 Link: /verify-public/web/media-detector.html")
    print("📋 Mudanças:")
    print("   • Banner escuro com CTA purple após mode cards")
    print("   • Tags: Vídeo · Imagem · Texto · Heurísticas MVP")
    print("   • i18n PT/DE/EN")
    print("   • Responsive (mobile: stack vertical)")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Uso: python3 patch_media_detector_link.py <path/to/index.html>")
        sys.exit(1)
    patch(sys.argv[1])
