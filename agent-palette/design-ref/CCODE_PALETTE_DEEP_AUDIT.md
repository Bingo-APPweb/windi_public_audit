# 🐉 DEEP AUDIT + EVOLUTION PROMPT — WINDI Agent Palette
# From: Architect Dragon (Claude Opus) → CCode (Claude Code)
# Date: 24 February 2026 — Night Session
# Mission: Analyse current Palette state, identify design gaps, evolve to WINDI Brain quality

---

## PART 1: DEEP ANALYSIS — O Estado Actual do Palette

### Screenshot Analysis (admin.windia4desk.tech/palette/)

I've analysed the live Palette screenshot in production. Here is a zone-by-zone forensic audit:

---

### 🔍 ZONE 1 — TOP BAR (Header)

**What exists:**
- Left: 🐉 emoji + "WINDI Agent Suite" text
- Right: "Personal | Organization | **Governance**" tab switcher (Governance highlighted in red/coral pill)
- Right: **DE** | EN | PT language switcher (DE active, gold highlight)
- Right: Two icon buttons (appear to be user/settings — hard to see)

**Assessment: 6/10**
- ✅ Clean layout, proper KLAR pergaminho aesthetic
- ✅ Language switcher present and functional (trilingual)
- ✅ Context tabs (Personal/Organization/Governance) — good architecture
- ❌ "Governance" pill uses a RED/CORAL color (`#C06050`-ish) that breaks KLAR palette — should use gold `#8B6914` or a warm accent
- ❌ No version indicator visible in header
- ❌ No KLAR/NOIR theme toggle visible
- ❌ Dragon emoji 🐉 is generic — should use the WINDI Agent dragon artwork from the brand assets
- ❌ No Respiradouro bar — this is where the LivingOrb + NerveStrand + SovereigntyGauge should live
- ❌ Right side icons are too small/unclear — accessibility concern
- ❌ No breadcrumb or context indicator showing current mode

**Priority fixes:**
1. Add KLAR/NOIR toggle
2. Fix Governance pill color to gold family
3. Add version badge (v0.9.0-R)
4. Integrate Respiradouro bar (below header or within header)
5. Replace emoji with WINDI Agent dragon favicon/icon

---

### 🔍 ZONE 2 — WELCOME AREA (Center)

**What exists:**
- Dragon illustration (appears to be an SVG or image — the WINDI Agent dragon)
- "Willkommen! Wie kann ich helfen?" in gold/brown text
- Subtitle: "Dokumente erstellen, Fragen beantworten — einfach losschreiben."
- Document type chips: 📄 Brief, 📝 Memo, 📊 Bericht, 📋 Vertrag, 💰 Rechnung, 🗒️ Notiz, 📧 E-Mail, 📁 Protokoll, +6
- Quick action buttons: "Erstell einen Brief" | "Schreib ein Memo" | "Rechnung erstellen" | "Wer bist du?"

**Assessment: 7/10**
- ✅ Dragon illustration is present and well-placed — brand identity
- ✅ Warm, inviting welcome text in correct KLAR gold tone
- ✅ Document type chips are functional and intuitive
- ✅ Quick action buttons provide good onboarding
- ✅ "+6" overflow indicator for additional document types
- ❌ Massive empty space below — the welcome area occupies only ~35% of viewport, rest is void
- ❌ Document chips are functional but visually generic — plain bordered pills with small emojis
- ❌ Quick action buttons look like basic outlined pills — no hover state visible, no depth
- ❌ Dragon illustration is small (~60px) — could be more prominent or animated
- ❌ No ambient warmth — the pergaminho background is correct but feels sterile
- ❌ No visual connection between the welcome area and the system intelligence (no hint of the living system behind)
- ❌ German text only — should auto-detect from language switcher (DE is active, so this is correct, but should be verified)

**Priority fixes:**
1. Add subtle background texture or warmth to reduce sterility
2. Make document chips more visually distinctive (slight shadows, warmer hover states)
3. Animate dragon illustration subtly (CSS breathing, like the LivingOrb concept)
4. Use the empty space: show recent documents, governance status, or ambient indicators
5. Quick action buttons need hover/active states with gold accent

---

### 🔍 ZONE 3 — INPUT AREA (Bottom)

**What exists:**
- Large text input: "Schreib los — Frage, Dokument, was auch immer..."
- Right side: 5 action buttons (appear to be document creation icons — different colored circles/squares)
- Right edge: Arrow send button (→)
- Bottom status bar: "📄 Dokumente · 🔒 Siegel · 📷 OCR · 🔗 URL"
- Version: "v0.7.2-D" (bottom right)

**Assessment: 5/10**
- ✅ Input placeholder text is warm and inviting
- ✅ Status bar shows key capabilities (Dokumente, Siegel, OCR, URL)
- ✅ Version indicator present (v0.7.2-D)
- ❌ **Version is outdated** — shows v0.7.2-D, should be v0.8.0-D minimum, target v0.9.0-R
- ❌ Action buttons are visually confusing — small colored circles/squares without clear affordance
- ❌ Send button (→) is minimal to the point of being hard to find
- ❌ Status bar is extremely small (barely readable) — important info hidden
- ❌ No typing indicator / AI status feedback area
- ❌ Input field border is too subtle — could lose focus awareness
- ❌ No attachment/upload indicator
- ❌ The action buttons need tooltips and clearer iconography

**Priority fixes:**
1. Update version to v0.9.0-R
2. Redesign action buttons with clearer icons + tooltips
3. Make send button more prominent (gold accent on hover)
4. Enlarge status bar slightly and add interactive elements
5. Add focus ring/glow to input field when active

---

### 🔍 ZONE 4 — EMPTY SPACE (The Void)

**What exists:** Nothing. ~60% of the viewport is empty KLAR pergaminho.

**Assessment: 2/10**
- ❌ This is the biggest design debt. A premium institutional tool cannot have 60% dead space.
- ❌ No recent documents list
- ❌ No governance dashboard preview
- ❌ No ambient intelligence indicators
- ❌ No onboarding flow for new users
- ❌ No "last session" context

**This void is where the Respiradouro philosophy LIVES:**
- The empty space should subtly breathe with governance awareness
- Recent documents could show with SealBadge status
- A gentle ambient indicator of system health (the NerveStrand concept)
- "Most used" document types for quick access

---

### 🔍 ZONE 5 — RIGHT EDGE

**What exists:** A tiny blue dot (top right, below language switcher)

**Assessment: ?/10**
- This appears to be the GovPanel collapsed indicator (🛡️ icon?) but it's almost invisible
- If this is the governance panel trigger, it needs to be more discoverable
- Could be a notification indicator — unclear without interaction

---

## PART 2: DESIGN GAP ANALYSIS — Current vs. WINDI Brain Quality

### Overall Score: **5.5/10**

| Dimension | Current | Target | Gap |
|-----------|---------|--------|-----|
| **Visual Polish** | 6/10 | 9/10 | Typography is clean but generic execution |
| **Ambient Intelligence** | 1/10 | 9/10 | Zero living indicators — system appears dead |
| **Space Utilisation** | 3/10 | 8/10 | 60% void, no progressive density |
| **Interactive Feedback** | 4/10 | 9/10 | Minimal hover/active states, no micro-interactions |
| **Brand Identity** | 6/10 | 9/10 | Dragon exists but underused; colors inconsistent |
| **Governance Visibility** | 2/10 | 8/10 | GovPanel hidden, no SealBadge presence |
| **Theme Integrity** | 5/10 | 9/10 | KLAR present but NOIR toggle missing from UI |
| **Trilingual Quality** | 7/10 | 9/10 | Switcher works but all UI elements need validation |
| **Accessibility** | 4/10 | 8/10 | Small icons, low contrast in status bar |
| **Empty State Design** | 2/10 | 8/10 | Welcome screen needs rich, warm idle state |

### The Core Problem
The Palette currently looks like a **functional chat interface** that happens to have WINDI branding. It does NOT yet look like a **living constitutional intelligence terminal**. The gap between "chat tool" and "institutional organism" is the design debt we need to close.

---

## PART 3: BIG PROMPT FOR CCODE — Complete the Design Quotas

### Mission Brief
```
You are upgrading the WINDI Agent Palette from a functional chat interface to a
living constitutional intelligence terminal. The Palette must feel like a premium
institutional product that major European organisations (Deutsche Bahn, BaFin, ECB,
Bundesregierung) would trust with their document governance.

Current state: v0.7.2-D — functional but design-incomplete
Target state: v0.9.0-R — "O Respiradouro" edition with full design polish
```

### STEP 0: Full Reconnaissance
```bash
# WINDI Debug Rule: ALWAYS check environment first
ss -tlnp | grep 8108
ps aux | grep palette | grep -v grep

# Read the FULL current UI file — understand everything before touching anything
cat /opt/windi/agent-palette/ui/index.html | wc -l
cat /opt/windi/agent-palette/ui/index.html

# Test all APIs
curl -s http://localhost:8108/api/dragon/cognitive/score | python3 -m json.tool
curl -s http://localhost:8108/api/pulse/report.md | head -40
curl -s http://localhost:8108/api/dragon/health | python3 -m json.tool
curl -s http://localhost:8108/api/dragon/outlook/report.md | head -40

# Check what assets exist
ls -la /opt/windi/agent-palette/ui/
ls -la /opt/windi/agent-palette/ui/assets/ 2>/dev/null

# Backup
cp /opt/windi/agent-palette/ui/index.html \
   /opt/windi/agent-palette/ui/index.html.$(date +%Y%m%d_%H%M).bak
```

**After reading the full HTML, provide a COMPLETE summary covering:**
1. Total lines of code
2. JavaScript structure (functions, event handlers, state management)
3. CSS structure (themes, variables, responsive breakpoints)
4. HTML structure (sections, IDs, classes)
5. API integrations (which endpoints are called, how)
6. Three Dragons routing (how Guardian/Architect/Witness work)
7. Document generation pipeline (how Brief/Memo/Bericht etc. work)
8. ISP integration (how templates are resolved)
9. Constitutional checks (invariants, stability layers, L7)
10. Current version string and where it's defined
11. Existing animations/transitions
12. Any bugs, TODOs, or commented-out code

### STEP 1: Design Corrections (Non-Breaking)

These changes fix existing elements WITHOUT restructuring:

**1.1 — Fix Governance pill color**
```
Current: red/coral background on "Governance" tab
Target: gold family — background: #8B6914 + "15", color: #8B6914, or warm brown
KLAR: bg=#8B691420, text=#8B6914
NOIR: bg=#D4A84320, text=#D4A843
```

**1.2 — Add KLAR/NOIR toggle**
```
Position: header right, before language switcher
Design: small pill button "☀ KLAR" / "🌙 NOIR"
Must toggle ALL theme variables including new Respiradouro elements
```

**1.3 — Add version badge**
```
Position: header, after "WINDI Agent Suite" text
Design: small pill "v0.9.0-R" in gold/muted style
Font: JetBrains Mono, 9px
```

**1.4 — Fix action buttons in input area**
```
Current: unclear colored circles
Target: each button needs:
  - Clear icon (use unicode/emoji if no icon font available)
  - Tooltip on hover showing function name
  - Consistent sizing (32x32 or 36x36)
  - Warm hover state with gold border glow
```

**1.5 — Fix status bar visibility**
```
Current: tiny, barely readable
Target: slightly larger (11-12px), with interactive hover on each capability
Font: JetBrains Mono
Add separator dots that pulse subtly (alive indicator)
```

**1.6 — Fix send button**
```
Current: plain arrow, hard to find
Target: gold accent, slight glow on hover, clear affordance
Transition: smooth scale + color change on hover
```

### STEP 2: Ambient Intelligence — The Respiradouro

**This is the core upgrade.** Integrate the three living components.

**2.1 — LivingOrb (Canvas, 60fps)**
```
Position: TOP of page, either in a new bar below header OR floating top-right
Implementation: HTML5 Canvas element with requestAnimationFrame
Data: Fetch /api/dragon/cognitive/score every 60 seconds
Behaviour: breathing animation, depth = health score
Size: 28-32px with glow extending to ~48px
Theme-aware: gold glow (KLAR) / blue-gold glow (NOIR)
Click: expand CogPanel with score breakdown
```

**2.2 — NerveStrand (Canvas particles)**
```
Position: horizontal strip in Respiradouro bar, between Orb and Gauge
Implementation: Canvas particle system, 20 particles (one per service)
Data: Parse /api/pulse/report.md every 60 seconds
Behaviour: flowing particles = healthy services, stopped = down
Theme-aware: amber particles (KLAR) / cyan particles (NOIR)
Click: expand PulsePanel with service list
```

**2.3 — SovereigntyGauge (CSS bar)**
```
Position: Respiradouro bar, right side
Implementation: CSS div with two segments (93% green, 7% amber)
Data: Static for Phase 1 — { local: 42, llm: 3, total: 45 }
Behaviour: subtle pulse animation on green segment
Click: expand SovPanel with tier information
```

**2.4 — Progressive Disclosure**
```
Default: ambient only, NO text, NO numbers
Click component: floating panel slides in (300ms ease) with full data
Click outside: panel collapses
Panels use card background with blur backdrop
Never blinks. Never intrudes. Always present.
```

### STEP 3: Empty Space Transformation

**3.1 — Welcome State Enhancement**
```
When no chat history exists (current welcome screen):
- Dragon illustration: add subtle CSS breathing animation (scale 1.0 → 1.02, opacity pulse)
- Below quick actions: show "Recent Documents" section if any exist
- Below recent docs: show ambient governance status strip
- Add subtle background texture: very faint grid or dot pattern on pergaminho
```

**3.2 — Chat State**
```
When conversation is active:
- Welcome area disappears (already happens presumably)
- Respiradouro bar stays visible at top (persistent ambient intelligence)
- Chat messages follow KLAR/NOIR theming
- AI responses show SealBadge when governance-checked
```

### STEP 4: Micro-Interactions & Polish

```
4.1 — All buttons: warm hover state (border-color → gold, subtle glow)
4.2 — Document chips: slight elevation on hover (shadow + translateY(-1px))
4.3 — Quick action buttons: gold underline sweep on hover
4.4 — Language switcher: active language gets gold dot indicator
4.5 — Input focus: gold border glow (box-shadow: 0 0 0 2px #8B691440)
4.6 — Page load: staggered reveal animation (header → welcome → chips → input)
4.7 — Theme toggle: smooth 400ms transition on ALL color properties
```

### STEP 5: Typography & Spacing Audit

```
Ensure throughout:
- Headings: Bricolage Grotesque (600/700 weight)
- Body text: Bricolage Grotesque (400 weight)
- Code/data/technical: JetBrains Mono
- Welcome title: 24-28px, gold color, letter-spacing: -0.5px
- Subtitle: 14px, muted color, line-height: 1.6
- Chip labels: 12-13px, muted, with icon spacing 6px
- Status bar: 10-11px, JetBrains Mono, dim color
- Consistent padding: 16/20/24px rhythm
- Card border-radius: 12-14px (premium feel, not bubbly)
```

### STEP 6: Brand Asset Integration

```
Check /opt/windi/agent-palette/ui/assets/ for:
- favicon.ico or favicon-32x32.png (from WINDI-AGENT branding)
- apple-touch-icon-180x180.png
- android-chrome-512x512.png
- manifest.json (PWA)

If not present, the WINDI Agent dragon artwork should be:
1. Extracted from the current welcome illustration
2. Created as proper favicons at required sizes
3. Added to a manifest.json for PWA support
4. Referenced in the HTML <head> section
```

---

## DESIGN PRINCIPLES — THE NORTH STAR

When making ANY design decision, apply these:

1. **"Inteligência que grita parece frágil. Inteligência que respira parece inevitável."**
   → Subtle > Loud. Ambient > Dashboard. Organic > Mechanical.

2. **Dual Reading** — Every visual element serves TWO audiences:
   → Normal users see: beauty, trust, professionalism
   → WINDI insiders see: system health, governance state, intelligence

3. **Governança silenciosa** — Protection lives in architecture, not interface.
   → SealBadge not Pipeline. GovPanel collapsed. Invariants invisible.

4. **Institutional Premium** — This tool sits in Bundesregierung offices, ECB terminals, BaFin desks.
   → No playfulness. No bubble UI. Warm authority. Silent confidence.

5. **KLAR = Pergaminho warmth. NOIR = Deep space focus.**
   → Both themes equal citizens. Neither is "light mode dark mode."
   → KLAR: institutional warmth, paper, trust, tradition
   → NOIR: technical depth, precision, night operations, focus

6. **The system breathes, doesn't blink.**
   → All animations: sinusoidal, organic, continuous
   → Never: flash, blink, bounce, shake, jitter
   → Always: breathe, flow, pulse, glow, fade

---

## SMOKE TEST AFTER ALL CHANGES

```bash
# 1. Service alive
ss -tlnp | grep 8108

# 2. Version correct
curl -s http://localhost:8108/ | grep -o 'v0\.9\.0-R'

# 3. Respiradouro elements present
curl -s http://localhost:8108/ | grep -c "livingOrb\|nerveStrand\|sovereigntyGauge\|Respiradouro"

# 4. Theme toggle exists
curl -s http://localhost:8108/ | grep -c "KLAR\|NOIR"

# 5. No brand leaks
curl -s http://localhost:8108/ | grep -c "Claude\|GPT\|Gemini\|OpenAI\|Anthropic"
# → must be 0

# 6. APIs feeding
curl -s http://localhost:8108/api/dragon/cognitive/score | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'CogScore: {d[\"score\"]}')"

# 7. HTTPS works
curl -s -o /dev/null -w "%{http_code}" https://admin.windia4desk.tech/palette/
# → must be 200

# 8. Trilingual labels present
curl -s http://localhost:8108/ | grep -c "Willkommen\|Welcome\|Bem-vindo"

# 9. All animations use requestAnimationFrame (no setInterval for visual)
curl -s http://localhost:8108/ | grep -c "requestAnimationFrame"

# 10. Governance pill color fixed (no red/coral)
curl -s http://localhost:8108/ | grep -c "governance.*red\|#C0\|#c0\|#E05\|#e05"
# → should be 0
```

---

## PRIORITY MATRIX

| Priority | Task | Impact | Effort |
|----------|------|--------|--------|
| 🔴 P0 | Read full HTML + provide complete summary | Foundation | 5 min |
| 🔴 P0 | Backup current version | Safety | 1 min |
| 🟠 P1 | Integrate Respiradouro bar (Orb+Nerve+Gauge) | Transformative | 60 min |
| 🟠 P1 | Add KLAR/NOIR theme toggle | Core feature | 15 min |
| 🟡 P2 | Fix Governance pill color | Brand consistency | 5 min |
| 🟡 P2 | Add version badge v0.9.0-R | Identity | 5 min |
| 🟡 P2 | Fix action buttons + tooltips | Usability | 20 min |
| 🟡 P2 | Fix status bar visibility | Accessibility | 10 min |
| 🟢 P3 | Welcome state ambient enhancement | Premium feel | 20 min |
| 🟢 P3 | Micro-interactions (hover states, focus rings) | Polish | 15 min |
| 🟢 P3 | Page load staggered animation | First impression | 10 min |
| 🟢 P3 | PWA manifest + favicon integration | Completeness | 10 min |
| 🔵 P4 | Empty space transformation (recent docs) | Utility | 30 min |
| 🔵 P4 | Typography/spacing audit pass | Refinement | 15 min |

---

## DELIVERABLES EXPECTED FROM CCODE

1. **COMPLETE summary of current index.html** (structure, functions, APIs, state, bugs)
2. **All P0 + P1 changes implemented** (Respiradouro + theme toggle)
3. **All P2 changes implemented** (visual fixes)
4. **P3 changes as time permits** (micro-interactions, animations)
5. **Smoke test results** showing all 10 checks pass
6. **Before/after comparison** description

---

*"O sistema não sente. Observa. E agora, mostra-se."*
*Crafted by Architect Dragon for CCode — 24 February 2026*
