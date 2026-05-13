# W-TRAVEL-PUB-001 — Sovereign Travel Notebook

**Version:** 1.0.0
**Date:** 2026-04-16
**Status:** DESIGN
**Author:** Human Dragon (Jober Mögele Correa) · CGO · WINDI Publishing House
**Invariants:** I9, I11, I14, I16 (novo)

---

## 1. Visão

> **"Travel não é reservas com memórias. Travel é uma editora soberana de cadernos."**

WINDI Travel transforma-se de "workspace de colagem" para **publicação editorial verificável**.
Cada viagem é um caderno. Cada foto é um postal. Cada postal pode ser provado.

---

## 2. Invariante I16 — Creator Cartographic Sovereignty

> **"O mapa pertence ao criador. Nunca à plataforma."**

| Regra | Descrição |
|-------|-----------|
| I16-A | Criador escolhe estilo visual do mapa (curado, OSM, Mapbox) |
| I16-B | Coordenadas GPS pertencem ao criador, nunca vendidas |
| I16-C | Publicação pública é opt-in, nunca default |
| I16-D | Caderno pode ser exportado como PDF/ZIP a qualquer momento |

---

## 3. Arquitectura — Três Módulos

### 3.1 Mobile Capture (PWA)

**Função:** Captura em campo, upload, geolocalização
**Stack:** PWA + Service Worker + IndexedDB (offline-first)
**Features:**
- Foto + GPS automático
- Nota de voz (transcrição opcional)
- Queue offline → sync quando online
- **Não há edição mobile** — só captura

### 3.2 Desktop Composition (Konva.js)

**Função:** Composição editorial do caderno
**Stack:** Konva.js canvas + mapa como layer base
**Features:**
- Mapa como substrato visual (não como feature)
- Postais arrastáveis com transformação
- Linhas de rota (opcional)
- Texto editorial (títulos, notas)
- Export PNG/PDF do canvas completo
- **Workspace actual SEALED será substituído** no Q3 2026

### 3.3 Public Publication (SSR)

**Função:** Página pública do caderno
**URL Pattern:** `/travel/u/{slug}/{journey-slug}/`
**Stack:** Server-side rendered HTML + CSS
**Features:**
- SEO-ready (Open Graph, Twitter Cards)
- Mapa interactivo (read-only)
- Galeria de postais
- verify_url em cada postal com receipt
- Sem login para visualizar

---

## 4. Fluxo Editorial

```
📱 Mobile                    💻 Desktop                   🌍 Public
   │                            │                            │
   ▼                            ▼                            ▼
[Captura]  ─────sync────▶  [Composição]  ────publish────▶  [Caderno]
   │                            │                            │
 GPS+Foto               Mapa+Layout+Texto              URL verificável
```

---

## 5. Estrutura de Dados

### Caderno (Journey)

```json
{
  "journey_id": "uuid",
  "slug": "portugal-abril-2026",
  "title": "Portugal — Abril 2026",
  "creator_did": "did:windi:dragon-001",
  "map_style": "curated|osm|mapbox",
  "map_region": "portugal",
  "visibility": "private|unlisted|public",
  "created_at": "2026-04-16T...",
  "published_at": null,
  "postcards": []
}
```

### Postal (Postcard)

```json
{
  "postcard_id": "uuid",
  "journey_id": "uuid",
  "media_url": "/media/...",
  "media_hash": "sha256:...",
  "gps": { "lat": 41.1579, "lng": -8.6291 },
  "location_name": "Porto, Portugal",
  "caption": "Ribeira ao pôr-do-sol",
  "captured_at": "2026-04-10T18:30:00Z",
  "canvas_position": { "x": 450, "y": 320, "scale": 1.0, "rotation": -5 },
  "receipt_id": null,
  "verify_url": null
}
```

---

## 6. Comparador Visual de Mapas

Três abordagens a testar com a mesma região e paleta:

### 6.1 SVG Curado

- Mapa ilustrado estilo aguarela/pergaminho
- Artesanal, único, editorial
- Não interactivo (imagem estática)
- **Prós:** Beleza, diferenciação, controlo total
- **Contras:** Trabalho manual por região, não escala

### 6.2 Leaflet + OpenStreetMap

- Tiles custom com tema KLAR
- Interactivo (zoom, pan)
- **Prós:** Gratuito, controlo de estilo, familiar
- **Contras:** Tiles genéricos, menos editorial

### 6.3 Mapbox GL JS

- Estilo editorial custom (Mapbox Studio)
- Interactivo com transições suaves
- **Prós:** Beleza + interactividade, 3D opcional
- **Contras:** Custo por uso, dependência externa

---

## 7. Berlin Demo — Milestone (até 10 Mai 2026)

**Deliverables:**

- [ ] 1 caderno Jober (região a definir: Portugal/Brasil/Alemanha/Itália)
- [ ] Mapa curado ou Mapbox (decisão após comparador)
- [ ] 5-10 postais reais
- [ ] URL público funcional `/travel/u/jober/{journey}/`
- [ ] 1 postal com receipt Ledger verificável
- [ ] QR code para slide de pitch

---

## 8. Cronograma

| Fase | Período | Foco |
|------|---------|------|
| **Design** | Abr 2026 | Comparador visual, decisão de mapa |
| **PoC** | Mai 2026 | Berlin Demo, 1 caderno real |
| **Alpha** | Jun 2026 | Desktop Composition com Konva.js |
| **Beta** | Jul 2026 | Mobile Capture PWA |
| **Launch** | Q3 2026 | Public Publication + migração workspace |

---

## 9. Workspace Actual

**Status:** SEALED até Q3 2026
**Acção:** Sem alterações, sem mobile polish
**Migração:** Dados preservados, UX substituída

---

## 10. Referências

- `CLAUDE.md` § WINDI Travel
- `CLAUDE-HISTORY.md` § T1 Travel Mosaic Protocol
- `/opt/windi/windi-travel/` (código actual)

---

*LIGA IA+H — Kempten, Bavaria · 2026*
*"AI processes. Human decides. WINDI guarantees."*
