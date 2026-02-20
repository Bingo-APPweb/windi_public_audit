#!/bin/bash
# ═══════════════════════════════════════════════════
# 🐉 WINDI — Add Communiqué Templates to Desktop Suite
# ═══════════════════════════════════════════════════
set -e

SUITE="/opt/windi/desktop/suite.html"
BK="/opt/windi/backups/suite_$(date +%Y%m%d_%H%M%S).html"
mkdir -p /opt/windi/backups
cp "$SUITE" "$BK"
echo "✅ Backup: $BK"

# ── Step 1: Add communique templates to TEMPLATES ──
python3 -c "
import re
p = '$SUITE'
with open(p) as f: code = f.read()

# Check if already patched
if 'communique:' in code and 'blank-com' in code:
    print('⚠️  1/7 Templates already present — skipping')
else:
    # Find closing of TEMPLATES object: the pattern '  ],' followed by '};'
    # We need to insert before the '};' that closes TEMPLATES
    # Find 'pptx: [' then find its closing '],' then insert communique before '};'
    
    # Strategy: find the last '],' before '};' in TEMPLATES context
    idx_templates = code.find('const TEMPLATES')
    if idx_templates == -1:
        raise SystemExit('❌ TEMPLATES not found')
    
    # Find the closing }; of TEMPLATES
    # It should be: ...],\n};
    idx_close = code.find('};', idx_templates)
    if idx_close == -1:
        raise SystemExit('❌ TEMPLATES closing not found')
    
    # Insert communique array before the };
    communique_block = '''  communique: [
    { id:\"blank-com\", label:\"Leeres Communiqu\u00e9\", sub:\"Freie Mitteilung\", icon:\"\ud83d\udce2\", gov:\"LOW\", type:\"communique\",
      content:{ title_de:\"\", title_en:\"\", title_pt:\"\", body_de:\"\", body_en:\"\", body_pt:\"\", category:\"UPDATE\", impact_level:\"MED\", author_name:\"\", author_role:\"\" } },
    { id:\"gov-update\", label:\"Governance-Update\", sub:\"System & Compliance\", icon:\"\ud83d\udee1\ufe0f\", gov:\"HIGH\", type:\"communique\",
      content:{ title_de:\"Governance-Update: [Thema]\", title_en:\"Governance Update: [Topic]\", title_pt:\"Atualiza\u00e7\u00e3o de Governan\u00e7a: [Tema]\",
        body_de:\"Im Rahmen unserer Governance-\u00dcberwachung informieren wir:\\\\n\\\\n1. Sachverhalt\\\\n[Beschreibung]\\\\n\\\\n2. Ma\u00dfnahmen\\\\n[Durchgef\u00fchrte Ma\u00dfnahmen]\\\\n\\\\n3. Auswirkungen\\\\n[Compliance-Status]\",
        body_en:\"As part of our governance monitoring:\\\\n\\\\n1. Situation\\\\n[Description]\\\\n\\\\n2. Measures\\\\n[Actions taken]\\\\n\\\\n3. Impact\\\\n[Compliance status]\",
        body_pt:\"No \u00e2mbito do monitoramento de governan\u00e7a:\\\\n\\\\n1. Situa\u00e7\u00e3o\\\\n[Descri\u00e7\u00e3o]\\\\n\\\\n2. Medidas\\\\n[A\u00e7\u00f5es tomadas]\\\\n\\\\n3. Impacto\\\\n[Status de conformidade]\",
        category:\"GOVERNANCE\", impact_level:\"HIGH\", author_name:\"\", author_role:\"Governance Officer\" } },
    { id:\"launch-com\", label:\"Launch / Markteinf\u00fchrung\", sub:\"Neues Produkt oder Service\", icon:\"\ud83d\ude80\", gov:\"MEDIUM\", type:\"communique\",
      content:{ title_de:\"Markteinf\u00fchrung: [Name]\", title_en:\"Launch: [Name]\", title_pt:\"Lan\u00e7amento: [Nome]\",
        body_de:\"Wir freuen uns, die Einf\u00fchrung bekannt zu geben.\\\\n\\\\n1. \u00dcbersicht\\\\n[Beschreibung]\\\\n\\\\n2. Mehrwert\\\\n[Vorteile]\\\\n\\\\n3. Verf\u00fcgbarkeit\\\\n[Details]\\\\n\\\\n4. Governance-Status\\\\n[Compliance]\",
        body_en:\"We are pleased to announce the launch.\\\\n\\\\n1. Overview\\\\n[Description]\\\\n\\\\n2. Value\\\\n[Benefits]\\\\n\\\\n3. Availability\\\\n[Details]\\\\n\\\\n4. Governance\\\\n[Compliance]\",
        body_pt:\"Temos o prazer de anunciar.\\\\n\\\\n1. Vis\u00e3o Geral\\\\n[Descri\u00e7\u00e3o]\\\\n\\\\n2. Proposta de Valor\\\\n[Benef\u00edcios]\\\\n\\\\n3. Disponibilidade\\\\n[Detalhes]\\\\n\\\\n4. Governan\u00e7a\\\\n[Conformidade]\",
        category:\"LAUNCH\", impact_level:\"MED\", author_name:\"\", author_role:\"Product Manager\" } },
    { id:\"compliance-alert\", label:\"Compliance-Alert\", sub:\"Risiko & Dringlichkeit\", icon:\"\u26a0\ufe0f\", gov:\"HIGH\", type:\"communique\",
      content:{ title_de:\"COMPLIANCE-ALERT: [Thema]\", title_en:\"COMPLIANCE ALERT: [Topic]\", title_pt:\"ALERTA DE CONFORMIDADE: [Tema]\",
        body_de:\"DRINGLICHKEIT: [HOCH/KRITISCH]\\\\n\\\\n1. Vorfall\\\\n[Beschreibung]\\\\n\\\\n2. Betroffene Bereiche\\\\n[Details]\\\\n\\\\n3. Sofortma\u00dfnahmen\\\\n[Schritte]\\\\n\\\\n4. Erforderliche Aktionen\\\\n[Fristen]\",
        body_en:\"URGENCY: [HIGH/CRITICAL]\\\\n\\\\n1. Incident\\\\n[Description]\\\\n\\\\n2. Affected Areas\\\\n[Details]\\\\n\\\\n3. Immediate Measures\\\\n[Steps]\\\\n\\\\n4. Required Actions\\\\n[Deadlines]\",
        body_pt:\"URG\u00caNCIA: [ALTA/CR\u00cdTICA]\\\\n\\\\n1. Incidente\\\\n[Descri\u00e7\u00e3o]\\\\n\\\\n2. \u00c1reas Afetadas\\\\n[Detalhes]\\\\n\\\\n3. Medidas Imediatas\\\\n[Passos]\\\\n\\\\n4. A\u00e7\u00f5es Necess\u00e1rias\\\\n[Prazos]\",
        category:\"COMPLIANCE\", impact_level:\"CRIT\", author_name:\"\", author_role:\"Compliance Officer\" } },
    { id:\"dekret-com\", label:\"Dekret / Decreto\", sub:\"Offizielle Anordnung\", icon:\"\ud83d\udcdc\", gov:\"HIGH\", type:\"communique\",
      content:{ title_de:\"DEKRET: [Titel]\", title_en:\"DECREE: [Title]\", title_pt:\"DECRETO: [T\u00edtulo]\",
        body_de:\"Hiermit wird folgendes Dekret erlassen:\\\\n\\\\nArtikel 1 \u2014 Gegenstand\\\\n[Anordnung]\\\\n\\\\nArtikel 2 \u2014 Geltungsbereich\\\\n[Bereich]\\\\n\\\\nArtikel 3 \u2014 Inkrafttreten\\\\n[Datum]\",
        body_en:\"The following decree is hereby issued:\\\\n\\\\nArticle 1 \u2014 Subject\\\\n[Order]\\\\n\\\\nArticle 2 \u2014 Scope\\\\n[Scope]\\\\n\\\\nArticle 3 \u2014 Entry into Force\\\\n[Date]\",
        body_pt:\"Fica estabelecido o seguinte decreto:\\\\n\\\\nArtigo 1 \u2014 Objeto\\\\n[Ordem]\\\\n\\\\nArtigo 2 \u2014 \u00c2mbito\\\\n[\u00c2mbito]\\\\n\\\\nArtigo 3 \u2014 Entrada em Vigor\\\\n[Data]\",
        category:\"GOVERNANCE\", impact_level:\"HIGH\", author_name:\"\", author_role:\"Chief Governance Officer\" } },
    { id:\"status-report\", label:\"Status-Bericht\", sub:\"Periodische Mitteilung\", icon:\"\ud83d\udccb\", gov:\"MEDIUM\", type:\"communique\",
      content:{ title_de:\"Status-Bericht: [Zeitraum]\", title_en:\"Status Report: [Period]\", title_pt:\"Relat\u00f3rio de Status: [Per\u00edodo]\",
        body_de:\"Berichtszeitraum: [Datum]\\\\n\\\\n1. Zusammenfassung\\\\n[\u00dcberblick]\\\\n\\\\n2. Fortschritt\\\\n[Meilensteine]\\\\n\\\\n3. Offene Punkte\\\\n[Aufgaben]\\\\n\\\\n4. Ausblick\\\\n[N\u00e4chste Schritte]\",
        body_en:\"Period: [Date]\\\\n\\\\n1. Summary\\\\n[Overview]\\\\n\\\\n2. Progress\\\\n[Milestones]\\\\n\\\\n3. Open Items\\\\n[Tasks]\\\\n\\\\n4. Outlook\\\\n[Next steps]\",
        body_pt:\"Per\u00edodo: [Data]\\\\n\\\\n1. Resumo\\\\n[Vis\u00e3o geral]\\\\n\\\\n2. Progresso\\\\n[Marcos]\\\\n\\\\n3. Pontos Abertos\\\\n[Tarefas]\\\\n\\\\n4. Perspectiva\\\\n[Pr\u00f3ximos passos]\",
        category:\"UPDATE\", impact_level:\"MED\", author_name:\"\", author_role:\"\" } },
  ],
'''
    code = code[:idx_close] + communique_block + code[idx_close:]
    with open(p, 'w') as f: f.write(code)
    print('✅ 1/7 Communiqué templates added')
"
echo ""

# ── Step 2: Fix tab click (remove redirect if present) ──
python3 -c "
p = '$SUITE'
with open(p) as f: code = f.read()
old = 't.id===\"communique\"?window.location.href=\"/communique/feed\":setTab(t.id)'
if old in code:
    code = code.replace(old, 'setTab(t.id)', 1)
    with open(p, 'w') as f: f.write(code)
    print('✅ 2/7 Tab click handler fixed (no redirect)')
else:
    print('⚠️  2/7 Redirect not present or already fixed')
"

# ── Step 3: Add communique to typeConf ──
python3 -c "
p = '$SUITE'
with open(p) as f: code = f.read()
old = 'pptx:{l:\"PPTX\",c:C.orange}}'
new = 'pptx:{l:\"PPTX\",c:C.orange},communique:{l:\"COM\",c:C.gold}}'
if 'communique:{l:\"COM\"' in code:
    print('⚠️  3/7 typeConf already has communique')
elif old in code:
    code = code.replace(old, new, 1)
    with open(p, 'w') as f: f.write(code)
    print('✅ 3/7 typeConf updated')
else:
    print('❌ 3/7 typeConf pattern not found')
"

# ── Step 4: Add state variables ──
python3 -c "
p = '$SUITE'
with open(p) as f: code = f.read()
if 'comTitleDe' in code:
    print('⚠️  4/7 State variables already present')
else:
    old = 'const [tpl,setTpl]=useState(null);'
    new = '''const [tpl,setTpl]=useState(null);
  const [comTitleDe,setComTitleDe]=useState(\"\");
  const [comTitleEn,setComTitleEn]=useState(\"\");
  const [comTitlePt,setComTitlePt]=useState(\"\");
  const [comBodyDe,setComBodyDe]=useState(\"\");
  const [comBodyEn,setComBodyEn]=useState(\"\");
  const [comBodyPt,setComBodyPt]=useState(\"\");
  const [comAuthor,setComAuthor]=useState(\"\");
  const [comRole,setComRole]=useState(\"\");
  const [comCategory,setComCategory]=useState(\"UPDATE\");
  const [comImpact,setComImpact]=useState(\"MED\");
  const [comPublishing,setComPublishing]=useState(false);'''
    if old in code:
        code = code.replace(old, new, 1)
        with open(p, 'w') as f: f.write(code)
        print('✅ 4/7 State variables added')
    else:
        print('❌ 4/7 useState pattern not found')
"

# ── Step 5: Add publish function ──
python3 << 'STEP5'
p = "/opt/windi/desktop/suite.html"
with open(p) as f: code = f.read()

if 'tpl.type==="communique"' in code:
    print("⚠️  5/7 Publish function already present")
else:
    # Find the generate function entry point
    marker = 'const id=mkId(), sge=mkSge(tpl.gov), isp='
    idx = code.find(marker)
    if idx == -1:
        print("❌ 5/7 Generate function marker not found")
    else:
        inject = '''// ── Communiqué Publish ──
    if(tpl.type==="communique"){
      setComPublishing(true);
      try{
        const cr=await fetch("/communique/api/communique/create",{method:"POST",headers:{"Content-Type":"application/json"},
          body:JSON.stringify({title_de:comTitleDe,title_en:comTitleEn,title_pt:comTitlePt,body_de:comBodyDe,body_en:comBodyEn,body_pt:comBodyPt,
            author_name:comAuthor,author_role:comRole,category:comCategory,impact_level:comImpact})});
        const cj=await cr.json();
        if(!cj.id){setComPublishing(false);return alert("Create failed: "+(cj.error||"unknown"));}
        await fetch(`/communique/api/communique/${cj.id}/review`,{method:"POST",headers:{"Content-Type":"application/json"},body:"{}"});
        const pr=await fetch(`/communique/api/communique/${cj.id}/publish`,{method:"POST",headers:{"Content-Type":"application/json"},
          body:JSON.stringify({approved_by:comAuthor||"Suite"})});
        const pj=await pr.json();
        setComPublishing(false);
        const rid=pj.publish_result?.receipt_id||"pending";
        setToast({id:cj.id,name:comTitleDe||comTitleEn||"Communiqu\u00e9",sealed:true,hash:rid});
        setDocs(p=>[{id:cj.id,name:comTitleDe||comTitleEn,type:"communique",gov:comImpact==="CRIT"||comImpact==="HIGH"?"HIGH":"MEDIUM",
          sge:0,hash:rid,contentHash:pj.publish_result?.content_hash||"",templateId:tpl.id,ts:ts(),sealed:true},...p]);
        setView("gallery");setTpl(null);
      }catch(e){setComPublishing(false);alert("Error: "+e.message);}
      return;
    }
    '''
        code = code[:idx] + inject + code[idx:]
        with open(p, 'w') as f: f.write(code)
        print("✅ 5/7 Publish function injected")
STEP5

# ── Step 6: Add communique form UI ──
python3 << 'STEP6'
p = "/opt/windi/desktop/suite.html"
with open(p) as f: code = f.read()

if 'tpl.type==="communique"&&(' in code:
    print("⚠️  6/7 Communiqu\u00e9 form already present")
else:
    # Find the pptx conditional to insert after
    marker = '{tpl.type==="pptx"&&('
    idx = code.find(marker)
    if idx == -1:
        print("❌ 6/7 pptx form marker not found")
    else:
        # Find the matching closing of this block - look for the next {tpl.type or the generate button
        # Better: insert before the generate button section
        btn_marker = '<button onClick={generate} disabled={busy}'
        btn_idx = code.find(btn_marker, idx)
        if btn_idx == -1:
            print("❌ 6/7 Generate button not found")
        else:
            form = '''              {tpl.type==="communique"&&(
                <div style={{display:"flex",flexDirection:"column",gap:12}}>
                  <div style={{display:"flex",gap:8,marginBottom:8,flexWrap:"wrap"}}>
                    <a href="/communique/feed" target="_blank" style={{color:C.gold,fontSize:11,textDecoration:"none",padding:"4px 10px",border:"1px solid "+C.gold+"44",borderRadius:5,background:C.gold+"12",display:"flex",alignItems:"center",gap:4}}>{"\ud83d\udce2"} Feed</a>
                    <select value={comCategory} onChange={e=>setComCategory(e.target.value)} style={{background:card,color:fg,border:"1px solid "+bdr,borderRadius:5,padding:"4px 8px",fontSize:11}}>
                      <option value="UPDATE">Aktualisierung</option><option value="GOVERNANCE">Governance</option>
                      <option value="LAUNCH">Launch</option><option value="COMPLIANCE">Compliance</option>
                    </select>
                    <select value={comImpact} onChange={e=>setComImpact(e.target.value)} style={{background:card,color:fg,border:"1px solid "+bdr,borderRadius:5,padding:"4px 8px",fontSize:11}}>
                      <option value="LOW">LOW</option><option value="MED">MED</option><option value="HIGH">HIGH</option><option value="CRIT">CRIT</option>
                    </select>
                  </div>
                  <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:8}}>
                    <input value={comAuthor} onChange={e=>setComAuthor(e.target.value)} placeholder="Autor / Author" style={{background:card,color:fg,border:"1px solid "+bdr,borderRadius:6,padding:"8px 12px",fontSize:12,fontFamily:"Outfit"}}/>
                    <input value={comRole} onChange={e=>setComRole(e.target.value)} placeholder="Rolle / Role" style={{background:card,color:fg,border:"1px solid "+bdr,borderRadius:6,padding:"8px 12px",fontSize:12,fontFamily:"Outfit"}}/>
                  </div>
                  {[{p:"\ud83c\udde9\ud83c\uddea Titel DE",v:comTitleDe,s:setComTitleDe},{p:"\ud83c\uddec\ud83c\udde7 Title EN",v:comTitleEn,s:setComTitleEn},{p:"\ud83c\udde7\ud83c\uddf7 T\u00edtulo PT",v:comTitlePt,s:setComTitlePt}].map((x,i)=>
                    <input key={i} value={x.v} onChange={e=>x.s(e.target.value)} placeholder={x.p}
                      style={{background:card,color:fg,border:"1px solid "+bdr,borderRadius:6,padding:"8px 12px",fontSize:13,fontFamily:"Outfit",fontWeight:600}}/>
                  )}
                  {[{p:"\ud83c\udde9\ud83c\uddea Inhalt",v:comBodyDe,s:setComBodyDe,r:8},{p:"\ud83c\uddec\ud83c\udde7 Content",v:comBodyEn,s:setComBodyEn,r:6},{p:"\ud83c\udde7\ud83c\uddf7 Conte\u00fado",v:comBodyPt,s:setComBodyPt,r:6}].map((x,i)=>
                    <textarea key={i} value={x.v} onChange={e=>x.s(e.target.value)} placeholder={x.p} rows={x.r}
                      style={{background:card,color:fg,border:"1px solid "+bdr,borderRadius:6,padding:"10px 12px",fontSize:12,fontFamily:"'JetBrains Mono',monospace",resize:"vertical",lineHeight:1.5}}/>
                  )}
                </div>
              )}
'''
            code = code[:btn_idx] + form + code[btn_idx:]
            with open(p, 'w') as f: f.write(code)
            print("\u2705 6/7 Communiqu\u00e9 form UI injected")
STEP6

# ── Step 7: Init fields when template selected ──
python3 << 'STEP7'
p = "/opt/windi/desktop/suite.html"
with open(p) as f: code = f.read()

if 't.type==="communique"&&t.content' in code:
    print("\u26a0\ufe0f  7/7 Template init already present")
else:
    old = 'setTpl(t);setView("editor")'
    if old not in code:
        old = "setTpl(t);setView('editor')"
    if old in code:
        new = old + ';if(t.type==="communique"&&t.content){setComTitleDe(t.content.title_de||"");setComTitleEn(t.content.title_en||"");setComTitlePt(t.content.title_pt||"");setComBodyDe(t.content.body_de||"");setComBodyEn(t.content.body_en||"");setComBodyPt(t.content.body_pt||"");setComAuthor(t.content.author_name||"");setComRole(t.content.author_role||"");setComCategory(t.content.category||"UPDATE");setComImpact(t.content.impact_level||"MED");}'
        code = code.replace(old, new, 1)
        with open(p, 'w') as f: f.write(code)
        print("\u2705 7/7 Template init wired")
    else:
        print("\u274c 7/7 setTpl pattern not found")
STEP7

echo ""
echo "═══════════════════════════════════════════════"
echo "🐉 Patch complete! Restarting desktop..."
echo "═══════════════════════════════════════════════"
sudo systemctl restart windi-desktop
sleep 2
sudo systemctl is-active windi-desktop && echo "✅ Desktop active" || echo "❌ Desktop failed"

# Verify
echo ""
echo "--- Verification ---"
grep -c "communique" /opt/windi/desktop/suite.html
grep -o "blank-com\|gov-update\|launch-com\|compliance-alert\|dekret-com\|status-report" /opt/windi/desktop/suite.html | sort -u
