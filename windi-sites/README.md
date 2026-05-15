# WINDI W-SITES-001 · Sprint 1 — Frontend Mockup

**Sealed:** 03 May 2026
**Status:** Sprint 1 complete · UI navegável sem IA
**Próximo:** Sprint 2 — Identity Gate + Backend integration

---

## O que está aqui

5 páginas HTML estáticas, KLAR/NOIR, sem dependências de build. Pronto para deploy.

```
public/
├── index.html              # /                — Landing pública
├── dashboard.html          # /dashboard       — Lista de sites
├── new-site.html           # /sites/new       — Wizard 6 passos
├── site-workspace.html     # /sites/[id]      — Workspace single site
└── verify.html             # /verify/[receipt]— Prova pública

assets/
└── windi-base.css          # Design system partilhado
```

---

## Decisão arquitectural — Não Next.js

Seguimos o **WINDI Product Blueprint v1.0** (testado em produção pelo W-LAW):

```
✓ HTML único por página                 (não SPA · não hidratação cliente)
✓ FastAPI + Jinja2 backend (Sprint 2)   (mesmo stack do W-LAW)
✓ nginx ONE TREE (windi-domain.com)     (não criar subdomínio separado)
✓ KLAR/NOIR via data-theme              (cartão de visita NUNCA tem só dark mode)
✓ Bricolage Grotesque + JetBrains Mono  (tipografia constitucional)
✓ Forensic strip no rodapé              (governança silenciosa · §57)
```

Razão: introduzir Next.js fragmenta a constelação. 200+ deps em `node_modules`,
build pipeline separado, hidratação cliente que rouba protagonismo do conteúdo
selável. Para um produto cuja promessa é "sites verificáveis", o React esconderia
o conteúdo atrás de JavaScript e dificultaria a própria selagem forense.

---

## Sprint 1 — checklist (entregue)

- [x] Layout NOIR/KLAR (toggle persistente via localStorage)
- [x] Landing pública com tiers LOW/MED/HIGH/GOV
- [x] Dashboard mockado com 3 sites de exemplo + estatísticas
- [x] Wizard com stepper visual de 6 passos (step 1 funcional, restantes preview)
- [x] Workspace com preview do site + compliance panel + receipt history
- [x] Verify público com receipt completo, QR SVG, e Beweiskette
- [x] Forensic footer em todas as páginas (governança silenciosa)
- [x] Botões publish/seal presentes mas mockados (alert no click)
- [x] Responsive mobile (≥320px)
- [x] Zero dependências externas (excepto Google Fonts)

---

## Deploy local — testar agora

```bash
# Opção A — Python simple server
cd public/
python3 -m http.server 8000
# abrir: http://localhost:8000/index.html

# Opção B — abrir directo no browser
open public/index.html
```

---

## Deploy Strato — Sprint 1.5

Após validação visual com o Human Dragon:

```bash
# 1. Copiar para o servidor
ssh windi@87.106.29.233
sudo mkdir -p /opt/windi/windi-sites/static
sudo chown windi:windi /opt/windi/windi-sites/static

# (no localhost)
scp -r public/* assets windi@87.106.29.233:/opt/windi/windi-sites/static/

# 2. nginx ONE TREE — adicionar a /etc/nginx/sites-enabled/windi-domain.com
#    ANTES do bloco 'listen 443 ssl;'
location /sites/ {
    alias /opt/windi/windi-sites/static/;
    index index.html;
    try_files $uri $uri/ =404;
}
location /sites/assets/ {
    alias /opt/windi/windi-sites/static/assets/;
}

# 3. Validar e reload (SEMPRE -t primeiro)
sudo nginx -t && sudo systemctl reload nginx

# 4. Smoke test
curl -s -o /dev/null -w "%{http_code}\n" https://www.windi-domain.com/sites/index.html
# esperado: 200
```

---

## Sprint 2 — próximo (não aqui)

```
Sprint 2 = ligar backend (Identity Gate + FastAPI)

1. cp -r /opt/windi/windi-law/identity-gate /opt/windi/windi-sites/identity-gate
2. Renomear referências law → sites (bash script)
3. Port: 8128 (próximo livre na faixa 8120-8129)
4. Endpoint POST /api/sites · grava em windi_sites_users.db
5. Ligar wizard step 6 a POST /api/sites/{id}/seal → :8101 Forensic Ledger
6. Ligar verify.html a GET https://windi-domain.com/api/receipts/{id}
7. Constitutional Tests 7/7 → cert({sites}): GOLD
```

---

## Invariantes deste produto

```
Protagonista:        SITE verificável (página pública com receipt)
Invariante novo:     I17 — Site Sovereignty
                     "todo conteúdo publicado é selável,
                      todo deploy é verificável,
                      toda revisão preserva chain"
Invariantes herdados: I9 · I11 · I13 · G3
Agent:               W-SITES-001 (domain extension de :8091)
Jurisdições:         DE · EU · PT
Port (Sprint 2):     :8128
```

---

## Liga IA+H · §XX — pendente

Após Sprint 2 + Constitutional Tests 7/7:

```markdown
## §XX — WINDI-SITES-001 v1.0 — CERTIFIED · {data}

Status:    COMPLETE · SEALED · I17 · IRREMEDIÁVEL
Receipt:   WINDI-SITES-CERTIFIED-{timestamp}
Blueprint: windi-product-blueprint v1.0
Live:      windi-domain.com/sites/

Diferencial:
  Sites públicos com receipts forenses por publish.
  Cada página carrega QR · SHA-256 · DID do autor.
  Sem dependência de browser para verificação.

Invariante específico:
  I17 — Site Sovereignty
```

---

**OM SHANTI 🐉**
