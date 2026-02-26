# 🐉 BIG PROMPT — "O RESPIRADOURO" Phase 1 Implementation
# WINDI Agent Palette v0.9.0-R (Respiradouro Edition)
# Target: Strato Server 87.106.29.233 — Port :8108

---

## CONTEXT — Read This First

You are working on the WINDI Agent Palette — a constitutional document intelligence terminal running at `admin.windia4desk.tech/palette/` (port 8108). The Palette currently has a Dragon Server with chat, generate, and render APIs. It uses the Three Dragons Protocol (Guardian/Architect/Witness) and dual themes KLAR/NOIR.

Tonight we designed **"O Respiradouro"** — three ambient, organic UI components that transform the Palette from a "chat tool" into a "living organism." The system's intelligence becomes visible through breathing, flowing, pulsing elements. This is Phase 1: implementation.

**Core Philosophy — MEMORIZE THIS:**
> "Inteligência que grita parece frágil. Inteligência que respira parece inevitável."

**Dual Reading Principle:**
- Normal users see: beautiful, living decoration → creates trust
- WINDI insiders see: the entire system presenting itself in real-time
- Same object. Two readings. Governança silenciosa.

---

## ARCHITECTURE — What Exists

### Server & Files
```
Server: windi@87.106.29.233
Base:   /opt/windi/agent-palette/
UI:     /opt/windi/agent-palette/ui/index.html  ← THIS IS THE FILE TO EDIT
Server: agent_palette_server.py (Python3, reads ui/index.html per request, NO restart needed)
nginx:  admin.windia4desk.tech/palette/ → proxy_pass http://127.0.0.1:8108/
```

### APIs Already Working (on the same server)
| Endpoint | Returns | Use For |
|----------|---------|---------|
| `/api/dragon/cognitive/score` | JSON: `{score, grade, components, decisions, timestamp}` | LivingOrb — CogScore feeds breath depth |
| `/api/pulse/report.md` | Markdown: 20 services, 17 wires, health status | NerveStrand — parse service status for particles |
| `/api/dragon/health` | JSON: `{version, dragons, model, budget}` | General health context |
| `/api/dragon/outlook/report.md` | Markdown: 15 features, 6 sprints, wiring | Future Phase 2 |

### Theme System (BOTH themes must be supported)
| Property | KLAR (Default) | NOIR |
|----------|---------------|------|
| bg | `#F5F0E0` | `#0E0E14` |
| card | `#FDFBF5` | `#16161F` |
| gold | `#8B6914` | `#D4A843` |
| text | `#2C2924` | `#E2E2EA` |
| dim | `#6B6560` | `#7A7A96` |
| border | `#DDD6C2` | `#26263A` |

### Brand Rules — ABSOLUTE
- ❌ NEVER mention: Claude, GPT, Gemini, OpenAI, Anthropic, Google
- ✅ Use only: Guardian, Architect, Witness
- Fonts: Bricolage Grotesque (headings) + JetBrains Mono (code/data)

---

## THE THREE COMPONENTS TO BUILD

### 1. 🔮 LivingOrb — "The System Breathes"

**What the user sees:** A softly glowing orb, pulsing gently like something alive.
**What WINDI insiders see:** The Cognitive Score (currently 89/100). Breath depth = system health.

**Technical Spec:**
- HTML5 `<canvas>` element, 60fps animation loop
- Position: floating element, suggest top-right or bottom-right of the Palette interface
- Size: ~80px diameter, with soft glow extending ~120px
- **Breathing animation:** sinusoidal scale/opacity cycle
  - Healthy (score > 85): slow, deep breath (~4 second cycle)
  - Normal (score 70-85): moderate breath (~3 second cycle)  
  - Stressed (score < 70): faster breath (~2 second cycle), slightly warmer color
  - Excellence (score > 92): deepest, calmest glow, micro-stability — almost serene
- **Inner pupil:** a brighter point at center, slightly offset, reacts to confidence
- **Color scheme:**
  - KLAR: warm gold glow (`#8B6914` → `#D4A843` gradient), pupil brighter gold
  - NOIR: cool blue-gold glow (`#D4A843` → `#4A9BD9` gradient), pupil electric
- **Glow:** CSS `box-shadow` or canvas `shadowBlur` radiating outward, breathing with the orb
- **First Visit Welcome:** first 3 seconds → deeper initial breath, then stabilize to normal rhythm
- **Data source:** Fetch `/api/dragon/cognitive/score` every 60 seconds
  - Extract `score` field from JSON response
  - If API unavailable: default to score=75, show slightly amber glow (graceful degradation)

### 2. 🧬 NerveStrand — "The Neural Network Flows"

**What the user sees:** Flowing dots along invisible fiber-optic paths, like bioluminescence.
**What WINDI insiders see:** Each particle = 1 WINDI service. Flowing = healthy. Stopped = service down.

**Technical Spec:**
- Same `<canvas>` or a second canvas layered behind/below the Orb
- Position: a horizontal or gently curved strip, suggest bottom of chat area or side rail
- **20 particles** (one per WINDI service), each as a small glowing dot (~3-5px)
- **Flow animation:** particles travel along a path (bezier curve or sine wave)
  - Healthy: smooth continuous flow, moderate speed
  - Service down: that particle stops, dims, maybe pulses red briefly
- **Neural connections:** faint lines between particles when close, like synaptic connections
  - Lines opacity based on distance — closer = more visible
  - Creates a living mesh/web effect
- **Color scheme:**
  - KLAR: warm amber/gold particles on subtle translucent track
  - NOIR: cyan/blue-white particles on dark translucent track
- **Data source:** Parse `/api/pulse/report.md` every 60 seconds
  - Count services with ✅ (healthy) vs ❌ (down)
  - Map each service to a particle: healthy=flowing, down=stopped
  - If API unavailable: show all 20 particles flowing (optimistic default)
- **Failure behaviour:** when services < 70% healthy:
  - Fibres lose fluidity (jittery motion)
  - Some particles slow/stop
  - Visual degradation should be subtle but noticeable to trained eye

### 3. 📊 SovereigntyGauge — "The Independence Bar"

**What the user sees:** An elegant thin bar, mostly green with a small amber segment.
**What WINDI insiders see:** Architecture ratio — 93% local sovereign vs 7% LLM-dependent (42 local / 3 LLM out of 45 total functions).

**Technical Spec:**
- CSS-based (no canvas needed), thin horizontal bar (~4px height, full width or section width)
- Position: very bottom of the Respiradouro area, or as a subtle accent line
- **Two segments:**
  - Green segment: `93.3%` width — represents local/sovereign functions (42/45)
  - Amber segment: `6.7%` width — represents LLM-dependent functions (3/45)
- **Color scheme:**
  - KLAR: green = `#4A8C3F`, amber = `#C4922A`, track bg = `#EDE8D8`
  - NOIR: green = `#5DAE50`, amber = `#D4A843`, track bg = `#1C1C28`
- **Subtle animation:** very slow pulse on the green segment (breathing glow, not movement)
- **Data source:** Currently STATIC values (42 local, 3 LLM, 45 total)
  - Hardcode for Phase 1: `const sovereignty = { local: 42, llm: 3, total: 45 };`
  - Future Phase 3: will come from API endpoint

---

## PROGRESSIVE DISCLOSURE

**Default state (ambient):** All three components visible but showing NO text, NO numbers. Pure visual.

**On click (expanded):** Clicking any component reveals a small panel with data:
- **LivingOrb click → CogPanel:** Shows "Cognitive Score: 89/100 — Grade: A" + component breakdown
- **NerveStrand click → PulsePanel:** Shows "Services: 18/20 Healthy" + list of service names and status
- **SovereigntyGauge click → SovPanel:** Shows "Sovereignty: 93.3% Local — 42 functions local, 3 LLM-assisted"

**Click outside → collapse** back to ambient. No text, no numbers.

**Panel styling:**
- Small floating card, matches theme (KLAR card bg / NOIR card bg)
- Subtle slide-in animation (200-300ms ease-out)
- Font: JetBrains Mono for data, Bricolage Grotesque for labels
- Border: 1px theme border color
- Close on click outside or click same component again

---

## INTEGRATION INTO EXISTING UI

### Placement Strategy
The Respiradouro components should integrate into the existing Palette layout WITHOUT breaking existing functionality. Suggested placement:

```
┌─────────────────────────────────────────┐
│  Palette Header (existing)              │
├─────────────────────────────────────────┤
│                                    [🔮] │  ← LivingOrb (top-right, floating)
│  Chat Area (existing)                   │
│  ...                                    │
│  ...                                    │
│  🧬 ○ ○ ○ ○ ○ ○ ○ ○ ○ ○ ○ ○ ○ ○ ○ ○  │  ← NerveStrand (bottom of chat)
│  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓░░░  │  ← SovereigntyGauge (thin bar)
├─────────────────────────────────────────┤
│  Input Area (existing)                  │
└─────────────────────────────────────────┘
```

The components should feel like they were ALWAYS there — ambient, organic, part of the living system.

---

## IMPLEMENTATION PROCEDURE

### Step 0: Reconnaissance
```bash
# ALWAYS check environment first (WINDI Debug Rule)
ss -tlnp | grep 8108
ps aux | grep palette | grep -v grep

# Read current UI to understand structure
cat /opt/windi/agent-palette/ui/index.html | head -100

# Test APIs are alive
curl -s http://localhost:8108/api/dragon/cognitive/score | python3 -m json.tool
curl -s http://localhost:8108/api/pulse/report.md | head -30
curl -s http://localhost:8108/api/dragon/health | python3 -m json.tool
```

### Step 1: Backup
```bash
cp /opt/windi/agent-palette/ui/index.html \
   /opt/windi/agent-palette/ui/index.html.$(date +%Y%m%d_%H%M).bak
```

### Step 2: Implement
Edit `/opt/windi/agent-palette/ui/index.html` directly. Everything is in a single HTML file (inline CSS + JS). Add:

1. **Canvas elements** for LivingOrb and NerveStrand
2. **CSS** for SovereigntyGauge bar + panel styling + animations
3. **JavaScript** for:
   - Canvas 60fps animation loops (requestAnimationFrame)
   - API polling (fetch every 60s with error handling)
   - Pulse report markdown parsing (extract service statuses)
   - Click handlers for progressive disclosure
   - Theme-aware colors (read current theme state from existing code)
   - First-visit welcome breath

### Step 3: Verify (no restart needed — server reads per request)
```bash
# Local check
curl -s http://localhost:8108/ | grep -o 'v[0-9]\.[0-9]\.[0-9]-[A-Z]'

# Brand safety check
curl -s http://localhost:8108/ | grep -c "Claude\|GPT\|Gemini\|OpenAI\|Anthropic"
# Must return 0

# HTTPS check
curl -s https://admin.windia4desk.tech/palette/ | grep "Respiradouro\|LivingOrb\|livingOrb"
```

---

## CODE QUALITY REQUIREMENTS

1. **No external dependencies.** Everything vanilla JS + Canvas + CSS. No libraries.
2. **60fps or bust.** Use `requestAnimationFrame`, not `setInterval` for animations.
3. **Theme-aware.** All colors must switch correctly between KLAR and NOIR.
4. **Graceful degradation.** If APIs fail, components show default/healthy state. Never crash.
5. **No brand names.** Zero mentions of Claude, GPT, Gemini, OpenAI, Anthropic, Google.
6. **Mobile-friendly.** Canvas should resize. Touch events for click/expand.
7. **Performance.** Animations must not block the main thread. Use offscreen calculations.
8. **Clean code.** Comment sections clearly. Group Respiradouro code in clearly marked blocks:
   ```javascript
   // ═══════════════════════════════════════
   // O RESPIRADOURO — Living Pulse System
   // v0.9.0-R — 24 Feb 2026
   // ═══════════════════════════════════════
   ```

---

## VERSION BUMP

Update the version string in the HTML from current version to: **v0.9.0-R**
(R = Respiradouro Edition)

---

## SMOKE TEST AFTER DEPLOY

```bash
# 1. Service alive
ss -tlnp | grep 8108

# 2. Version correct
curl -s http://localhost:8108/ | grep -o 'v0\.9\.0-R'

# 3. Respiradouro elements present
curl -s http://localhost:8108/ | grep -c "livingOrb\|nerveStrand\|sovereigntyGauge"

# 4. No brand leaks
curl -s http://localhost:8108/ | grep -c "Claude\|GPT\|Gemini\|OpenAI\|Anthropic"
# → must be 0

# 5. APIs feeding
curl -s http://localhost:8108/api/dragon/cognitive/score | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'CogScore: {d[\"score\"]}')"

# 6. HTTPS works
curl -s -o /dev/null -w "%{http_code}" https://admin.windia4desk.tech/palette/
# → must be 200

# 7. Theme toggle works (visual check via browser)
echo "Open https://admin.windia4desk.tech/palette/ and toggle KLAR ↔ NOIR"
echo "Verify: Orb glow changes color, particles change color, gauge bar adapts"
```

---

## WHAT SUCCESS LOOKS LIKE

When you open the Palette in a browser, you should see:
1. A softly breathing orb in the corner — alive, warm, calming
2. Tiny particles flowing along invisible paths — like bioluminescence in deep water
3. A thin bar at the bottom, mostly green — sovereignty made visible
4. Click any element → clean data panel slides in
5. Click away → back to ambient beauty
6. Switch KLAR ↔ NOIR → all elements adapt seamlessly
7. Everything feels like it was always there. Natural. Organic. Inevitable.

**"O sistema não sente. Observa. E agora, mostra-se."** 🐉

---

## IMPORTANT NOTES

- The Palette UI is a SINGLE HTML file. All CSS and JS are inline.
- No server restart needed. Edit the file, refresh browser, see changes.
- The existing UI has chat functionality, Three Dragons routing, Dragon Server integration — DO NOT break any of this. ADD the Respiradouro components alongside.
- If you need to understand the existing code structure, read the full index.html first.
- The Dragon Server on :8108 handles API routes AND serves the UI. The APIs are relative paths.
- WINDI AGENT image assets (favicon, apple-touch-icon) are available in `/opt/windi/agent-palette/ui/assets/` — integrate as favicon/PWA icons if not already present.

---

*Prompt crafted by Human Dragon + Architect Dragon*
*24 February 2026 — "Inteligência que respira parece inevitável."*
