#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════
# WINDI Agent Palette — Frontend Patch v0.7.0-D (Dragon Edition)
# Applies surgical modifications to ui/index.html for brain integration
#
# Run AFTER deploying agent_dragon_server.py
# Usage: bash patch_frontend_v070.sh
# ═══════════════════════════════════════════════════════════════════════

set -e

UI_FILE="/opt/windi/agent-palette/ui/index.html"
BACKUP="${UI_FILE}.$(date +%Y%m%d_%H%M).bak"

echo "🐉 WINDI Frontend Patch v0.7.0-D"
echo "================================="

# Backup
echo "[1/6] Backing up current UI..."
cp "$UI_FILE" "$BACKUP"
echo "  → Backup: $BACKUP"

# ── PATCH 1: Version bump ──────────────────────────────────────────
echo "[2/6] Patching version..."
sed -i 's/const V = "0.6.0-K";/const V = "0.7.0-D";/' "$UI_FILE"
echo "  → Version: 0.6.0-K → 0.7.0-D"

# ── PATCH 2: Add isLoading + activeDragon state ───────────────────
echo "[3/6] Adding Dragon state variables..."
sed -i 's/const \[themeName, setThemeName\] = useState("KLAR");/const [themeName, setThemeName] = useState("KLAR");\n  const [isLoading, setIsLoading] = useState(false);\n  const [activeDragon, setActiveDragon] = useState(null);/' "$UI_FILE"
echo "  → Added: isLoading, activeDragon state"

# ── PATCH 3: Replace synchronous send with async Dragon-powered send ─
echo "[4/6] Upgrading send handler to async Dragon brain..."
# This is the big one — we replace the entire send callback
python3 - "$UI_FILE" << 'PYTHON_PATCH'
import sys

filepath = sys.argv[1]

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Old send function (synchronous, local-only)
OLD_SEND = '''const send = useCallback((text) => {
    const msg = (text || input).trim();
    if (!msg) return;
    const ts = new Date().toLocaleTimeString("de-DE",{hour:"2-digit",minute:"2-digit",second:"2-digit"});
    setMsgs(prev => [...prev, { role:"human", text:msg, ts }]);
    setInput("");
    setTimeout(() => {
      const result = agentThink(msg, tier, intentHistory, stats);
      const ats = new Date().toLocaleTimeString("de-DE",{hour:"2-digit",minute:"2-digit",second:"2-digit"});
      if (result.intent) { setLang(result.intent.language); setIntentHistory(prev => [...prev, result.intent].slice(-10)); }
      setMsgs(prev => [...prev, { role:"agent", text:result.message, result, ts:ats }]);
      if (result.type === "success") setStats(prev => ({ docs:prev.docs+1, sealed:prev.sealed+(result.receipt?1:0), avgMs:Math.round((prev.avgMs*prev.docs+result.ms)/(prev.docs+1)) }));
    }, 100 + Math.random() * 200);
  }, [input, tier, intentHistory]);'''

# New send function (async, Dragon-powered with local fallback)
NEW_SEND = '''const send = useCallback(async (text) => {
    const msg = (text || input).trim();
    if (!msg || isLoading) return;
    const ts = new Date().toLocaleTimeString("de-DE",{hour:"2-digit",minute:"2-digit",second:"2-digit"});
    setMsgs(prev => [...prev, { role:"human", text:msg, ts }]);
    setInput("");
    setIsLoading(true);
    setActiveDragon(null);

    try {
      // Try Dragon Brain (async LLM) first
      if (window.DragonBrain?.ready) {
        const classification = classifyInput(msg, intentHistory);
        const detectedLang = detectLang(msg) || "de";

        if (classification.mode === "chat") {
          // Chat mode → Dragon API
          const chatHistory = msgs.slice(-10).map(m => ({ role: m.role === "agent" ? "assistant" : "human", text: m.text }));
          const dragon = await window.DragonBrain.chat(msg, {
            tier, chatType: classification.chatType, intentMode: "chat",
            language: detectedLang, history: chatHistory,
          });

          if (dragon?.message) {
            const ats = new Date().toLocaleTimeString("de-DE",{hour:"2-digit",minute:"2-digit",second:"2-digit"});
            setActiveDragon(dragon.dragon);
            setLang(detectedLang);
            setMsgs(prev => [...prev, { role:"agent", text:dragon.message, ts:ats, dragon:dragon.dragon, source:dragon.source,
              result: { type:"chat", chatType:classification.chatType, message:dragon.message, dragon:dragon.dragon,
                intent:{language:detectedLang}, sge:null, receipt:null, template:null,
                constitutional:{active:true, invariants:9, layers:8}, ms:0 }
            }]);
            setIsLoading(false);
            return;
          }
        }

        if (classification.mode === "document") {
          // Document mode → try Dragon Generate + local governance
          const intent = parseIntent(msg, intentHistory);
          const tierCfg = TIERS[tier];
          if (tierCfg.llm) {
            const { template, alternatives } = resolveTemplate(intent);
            const dragon = await window.DragonBrain.generate(msg, {
              tier, intent, templateId: template?.id, language: detectedLang,
            });
            if (dragon?.message) {
              const sge = runSGE(dragon.message, tier, intent, template?.id);
              const format = resolveFormat(intent, tierCfg);
              const validation = validateInvariants(dragon.message);
              let receipt = null;
              if (tierCfg.ledger) receipt = genReceipt(intent, template?.id, sge, tier, validation);
              const ats = new Date().toLocaleTimeString("de-DE",{hour:"2-digit",minute:"2-digit",second:"2-digit"});
              setActiveDragon("architect");
              setLang(detectedLang);
              setIntentHistory(prev => [...prev, intent].slice(-10));
              const result = {
                type: validation.hasFatal ? "blocked_constitutional" : "success",
                intent, sge, receipt, template, alternatives, format,
                method:"hybrid", message:dragon.message, dragon:"architect",
                needsConfirm: sge.humanRequired && !sge.blocked,
                constitutional:{validation, invariants:9, layers:8}, ms:0
              };
              setMsgs(prev => [...prev, { role:"agent", text:dragon.message, result, ts:ats, dragon:"architect", source:dragon.source }]);
              if (result.type === "success") setStats(prev => ({ docs:prev.docs+1, sealed:prev.sealed+(receipt?1:0), avgMs:prev.avgMs }));
              setIsLoading(false);
              return;
            }
          }
        }
      }

      // Fallback: local agentThink (original behavior)
      const result = agentThink(msg, tier, intentHistory, stats);
      const ats = new Date().toLocaleTimeString("de-DE",{hour:"2-digit",minute:"2-digit",second:"2-digit"});
      if (result.intent) { setLang(result.intent.language); setIntentHistory(prev => [...prev, result.intent].slice(-10)); }
      setMsgs(prev => [...prev, { role:"agent", text:result.message, result, ts:ats }]);
      if (result.type === "success") setStats(prev => ({ docs:prev.docs+1, sealed:prev.sealed+(result.receipt?1:0), avgMs:Math.round((prev.avgMs*prev.docs+result.ms)/(prev.docs+1)) }));
    } catch (err) {
      console.error("[DragonBrain] Send error:", err);
      // Emergency fallback
      const result = agentThink(msg, tier, intentHistory, stats);
      const ats = new Date().toLocaleTimeString("de-DE",{hour:"2-digit",minute:"2-digit",second:"2-digit"});
      setMsgs(prev => [...prev, { role:"agent", text:result.message, result, ts:ats }]);
    }
    setIsLoading(false);
  }, [input, tier, intentHistory, isLoading, msgs]);'''

if OLD_SEND in content:
    content = content.replace(OLD_SEND, NEW_SEND)
    print("  → Send handler patched successfully (sync → async Dragon)")
else:
    print("  ⚠️  Could not find exact send handler match. Manual patching may be needed.")
    print("     Look for 'const send = useCallback((text)' and replace with async version.")

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
PYTHON_PATCH

# ── PATCH 4: Update Msg component to show Dragon identity ─────────
echo "[5/6] Patching Msg component for Dragon identity..."
python3 - "$UI_FILE" << 'PYTHON_PATCH2'
import sys

filepath = sys.argv[1]

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace the agent label in Msg component
OLD_LABEL = '''{a && <div style={{ fontSize:10, color:T.muted, marginBottom:3, marginLeft:2, fontFamily:T.mono }}>🐉 WINDI Agent</div>}'''

NEW_LABEL = '''{a && <div style={{ fontSize:10, color:T.muted, marginBottom:3, marginLeft:2, fontFamily:T.mono }}>
        {dragon ? (
          <span>{dragon === "guardian" ? "🛡️" : dragon === "architect" ? "🏗️" : dragon === "witness" ? "👁️" : "🐉"}{" "}
          <span style={{color:T.gold}}>{dragon === "guardian" ? "Guardian" : dragon === "architect" ? "Architect" : dragon === "witness" ? "Witness" : "Agent"}</span>
          {source === "llm" && <span style={{color:T.green, marginLeft:4, fontSize:8}}>● LIVE</span>}
          {source === "local_fallback" && <span style={{color:T.orange, marginLeft:4, fontSize:8}}>○ LOCAL</span>}
          </span>
        ) : "🐉 WINDI Agent"}
      </div>}'''

if OLD_LABEL in content:
    content = content.replace(OLD_LABEL, NEW_LABEL)
    print("  → Msg label patched for Dragon identity display")
else:
    print("  ⚠️  Could not find exact Msg label. Manual patching may be needed.")

# Also update the Msg function signature to receive dragon + source props
OLD_MSG_SIG = '''function Msg({ role, text, result, ts, T }) {'''
NEW_MSG_SIG = '''function Msg({ role, text, result, ts, T, dragon, source }) {'''

if OLD_MSG_SIG in content:
    content = content.replace(OLD_MSG_SIG, NEW_MSG_SIG)
    print("  → Msg signature updated with dragon + source props")

# Update Msg rendering to pass dragon prop
OLD_MSG_RENDER = '''{msgs.map((m,i) => <Msg key={i} {...m} T={T} />)}'''
NEW_MSG_RENDER = '''{msgs.map((m,i) => <Msg key={i} {...m} T={T} dragon={m.dragon} source={m.source} />)}'''

if OLD_MSG_RENDER in content:
    content = content.replace(OLD_MSG_RENDER, NEW_MSG_RENDER)
    print("  → Msg rendering updated with dragon prop passthrough")

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
PYTHON_PATCH2

# ── PATCH 5: Add loading indicator ────────────────────────────────
echo "[6/6] Adding loading indicator..."
python3 - "$UI_FILE" << 'PYTHON_PATCH3'
import sys

filepath = sys.argv[1]

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Add loading indicator after messages list
OLD_MSGS_END = '''{msgs.map((m,i) => <Msg key={i} {...m} T={T} dragon={m.dragon} source={m.source} />)}'''

NEW_MSGS_END = '''{msgs.map((m,i) => <Msg key={i} {...m} T={T} dragon={m.dragon} source={m.source} />)}
            {isLoading && (
              <div style={{ display:"flex", alignItems:"flex-start", marginBottom:14, animation:"msgIn 0.35s" }}>
                <div style={{ fontSize:10, color:T.muted, marginBottom:3, marginLeft:2, fontFamily:T.mono }}>
                  {activeDragon ? (activeDragon === "guardian" ? "🛡️ Guardian" : activeDragon === "architect" ? "🏗️ Architect" : "👁️ Witness") : "🐉 Agent"}
                  <span style={{ color:T.gold, marginLeft:4, fontSize:9 }}>thinking...</span>
                </div>
              </div>
            )}'''

if OLD_MSGS_END in content:
    content = content.replace(OLD_MSGS_END, NEW_MSGS_END, 1)
    print("  → Loading indicator added")
else:
    print("  ⚠️  Could not add loading indicator. Add manually after msgs.map().")

# Disable send button during loading
OLD_SEND_BTN = '''disabled={!input.trim()}'''
NEW_SEND_BTN = '''disabled={!input.trim() || isLoading}'''

content = content.replace(OLD_SEND_BTN, NEW_SEND_BTN)
print("  → Send button disabled during loading")

# Update title
OLD_TITLE = '''<title>WINDI Agent Suite v0.6.0-K</title>'''
NEW_TITLE = '''<title>WINDI Agent Suite v0.7.0-D — Three Dragons</title>'''
content = content.replace(OLD_TITLE, NEW_TITLE)
print("  → Title updated")

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
PYTHON_PATCH3

echo ""
echo "═══════════════════════════════════════════════════════════════════"
echo "🐉 Frontend patched to v0.7.0-D!"
echo "   Backup saved: $BACKUP"
echo ""
echo "   Changes applied:"
echo "   ✓ Version 0.6.0-K → 0.7.0-D"
echo "   ✓ Dragon state (isLoading, activeDragon)"
echo "   ✓ Async send with Dragon Brain API"
echo "   ✓ Msg component shows Guardian/Architect/Witness identity"
echo "   ✓ Loading indicator"
echo "   ✓ Send button disabled during API calls"
echo ""
echo "   No server restart needed (UI served fresh per request)"
echo "═══════════════════════════════════════════════════════════════════"
