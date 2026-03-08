#!/usr/bin/env python3
"""Patch Palette UI to use Guardian Local before LLM calls."""
import shutil
from datetime import datetime

UI_FILE = "/opt/windi/agent-palette/ui/index.html"

# Backup
bak = f"{UI_FILE}.{datetime.now().strftime('%Y%m%d_%H%M')}.bak"
shutil.copy2(UI_FILE, bak)
print(f"✅ Backup: {bak}")

content = open(UI_FILE, "r", encoding="utf-8").read()

OLD = """          // Chat mode \u2192 Dragon API
          const chatHistory = msgs.slice(-10).map(m => ({ role: m.role === "agent" ? "assistant" : "human", text: m.text }));
          const dragon = await window.DragonBrain.chat(msg, {"""

NEW = """          // ── Guardian Local Intercept (FREE tier) ──────────
          try {
            const gResp = await fetch('/guardian/local', {
              method: 'POST',
              headers: {'Content-Type': 'application/json'},
              body: JSON.stringify({ text: msg, session_id: window._windiSessionId || 'anon', tier: tier || 'FREE' })
            });
            const gData = await gResp.json();
            if (gData && !gData.requires_llm) {
              const ats = new Date().toLocaleTimeString("de-DE",{hour:"2-digit",minute:"2-digit",second:"2-digit"});
              setActiveDragon('guardian');
              setLang(gData.language || detectedLang);
              const localResp = applyLayer7(gData.text);
              setMsgs(prev => [...prev, { role:"agent", text:localResp, ts:ats, dragon:"guardian", source:"local",
                governance: { sge:0, risk:"R0", mode:"LOCAL", dragon:"guardian", latencyMs:gData.processing_ms } }]);
              setLoading(false);
              setTypingPhase(null);
              // Track stats
              if (window.dragonRouter?.autoAuditTrail) window.dragonRouter.autoAuditTrail(msg, { dragon:"guardian" }, gData.processing_ms);
              return;
            }
            // requires_llm=true → show escalation message if present, then fall through to DragonBrain
            if (gData && gData.requires_llm && gData.text) {
              const ats = new Date().toLocaleTimeString("de-DE",{hour:"2-digit",minute:"2-digit",second:"2-digit"});
              setMsgs(prev => [...prev, { role:"agent", text:gData.text, ts:ats, dragon:"guardian", source:"local",
                governance: { sge:0, risk:"R0", mode:"ESCALATION", dragon:"guardian" } }]);
              setLoading(false);
              setTypingPhase(null);
              return;
            }
          } catch(e) { console.log('[Guardian Local] Unavailable, falling back to DragonBrain:', e.message); }
          // ── END Guardian Local ─────────────────────────────

          // Dragon API (LLM fallback)
          const chatHistory = msgs.slice(-10).map(m => ({ role: m.role === "agent" ? "assistant" : "human", text: m.text }));
          const dragon = await window.DragonBrain.chat(msg, {"""

if OLD not in content:
    print("❌ Pattern not found! File may have changed.")
    print("   Looking for: '// Chat mode → Dragon API'")
    import sys; sys.exit(1)

content = content.replace(OLD, NEW, 1)
open(UI_FILE, "w", encoding="utf-8").write(content)
print("✅ Guardian Local intercept injected into Palette")
print("   Flow: User msg → Guardian Local → if local OK → respond")
print("                                   → if needs LLM → escalation msg")
print("                                   → if unavailable → DragonBrain fallback")
