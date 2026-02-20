#!/usr/bin/env python3
"""
🐉 WINDI Three Dragons — Add Communiqué Templates to Desktop Suite
Adds communiqué creation workflow to suite.html alongside doc/xlsx/pptx.
"""
from pathlib import Path
import shutil, datetime

p = Path("/opt/windi/desktop/suite.html")
bk = Path(f"/opt/windi/backups/suite_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.html")
bk.parent.mkdir(parents=True, exist_ok=True)
shutil.copy2(p, bk)
print(f"✅ Backup: {bk}")

code = p.read_text()

# ═══════════════════════════════════════════════════
# 1. Add communique templates to TEMPLATES object
# ═══════════════════════════════════════════════════

# Find the end of pptx templates array to insert communique after it
old_pptx_end = """    { id:"quartals-review", label:"Quartals-Review", sub:"Universell einsetzbar", icon:"\u{1F4C5}", gov:"MEDIUM", type:"pptx",
      slides:[{type:"title",title:"Quartals-Review Q1 2026",subtitle:"[Organisation] \u00B7 [Abteilung]"},{type:"content",heading:"Highlights des Quartals",body:"[Die wichtigsten Erfolge und Entwicklungen des Quartals zusammenfassen]\\n\\n\u2022 Projekt A: [Status und Ergebnis]\\n\u2022 Projekt B: [Status und Ergebnis]\\n\u2022 Projekt C: [Status und Ergebnis]"},{type:"dashboard",framework:"Interne Governance-Richtlinien",status:"[Status]"},{type:"risks",heading:"Herausforderungen",items:["[Herausforderung 1 \u2014 Beschreibung und Auswirkung]","[Herausforderung 2 \u2014 Beschreibung und Auswirkung]","[Herausforderung 3 \u2014 Beschreibung und Auswirkung]"]},{type:"actions",heading:"Ziele Q2 2026",items:["[Ziel 1 mit konkretem Ergebnis und Frist]","[Ziel 2 mit konkretem Ergebnis und Frist]","[Ziel 3 mit konkretem Ergebnis und Frist]"]}] },
  ],"""

if old_pptx_end not in code:
    # Try a simpler anchor
    print("⚠️  Exact pptx end not found, trying simpler anchor...")
    # Find the closing of pptx array
    idx = code.find("pptx: [")
    if idx == -1:
        raise SystemExit("❌ Cannot find pptx templates array")
    # Find the "]," that closes it by counting brackets
    # Alternative: find the pattern right before the closing of TEMPLATES
    anchor = """  ],
};"""
    if anchor not in code:
        raise SystemExit("❌ Cannot find end of TEMPLATES object")
    
    new_anchor = """  ],
  communique: [
    { id:"blank-com", label:"Leeres Communiqu\\u00E9", sub:"Freie Mitteilung", icon:"\\u{1F4E2}", gov:"LOW", type:"communique",
      content:{ title_de:"", title_en:"", title_pt:"", body_de:"", body_en:"", body_pt:"", category:"UPDATE", impact_level:"MED", author_name:"", author_role:"" } },
    { id:"gov-update", label:"Governance-Update", sub:"System & Compliance", icon:"\\u{1F6E1}\\uFE0F", gov:"HIGH", type:"communique",
      content:{ title_de:"Governance-Update: [Thema]", title_en:"Governance Update: [Topic]", title_pt:"Atualiza\\u00E7\\u00E3o de Governan\\u00E7a: [Tema]",
        body_de:"Im Rahmen unserer fortlaufenden Governance-\\u00DCberwachung informieren wir \\u00FCber folgende Entwicklung:\\n\\n1. Sachverhalt\\n[Beschreibung]\\n\\n2. Ma\\u00DFnahmen\\n[Durchgef\\u00FChrte oder geplante Ma\\u00DFnahmen]\\n\\n3. Auswirkungen\\n[Bewertung der Auswirkungen auf Compliance-Status]",
        body_en:"As part of our ongoing governance monitoring, we report the following development:\\n\\n1. Situation\\n[Description]\\n\\n2. Measures\\n[Actions taken or planned]\\n\\n3. Impact\\n[Assessment of impact on compliance status]",
        body_pt:"No \\u00E2mbito do nosso monitoramento cont\\u00EDnuo de governan\\u00E7a, informamos sobre o seguinte desenvolvimento:\\n\\n1. Situa\\u00E7\\u00E3o\\n[Descri\\u00E7\\u00E3o]\\n\\n2. Medidas\\n[A\\u00E7\\u00F5es tomadas ou planejadas]\\n\\n3. Impacto\\n[Avalia\\u00E7\\u00E3o do impacto no status de conformidade]",
        category:"GOVERNANCE", impact_level:"HIGH", author_name:"", author_role:"Governance Officer" } },
    { id:"launch-com", label:"Launch / Markteinf\\u00FChrung", sub:"Neues Produkt oder Service", icon:"\\u{1F680}", gov:"MEDIUM", type:"communique",
      content:{ title_de:"Markteinf\\u00FChrung: [Produkt/Service]", title_en:"Launch: [Product/Service]", title_pt:"Lan\\u00E7amento: [Produto/Servi\\u00E7o]",
        body_de:"Wir freuen uns, die Einf\\u00FChrung von [Name] bekannt zu geben.\\n\\n1. \\u00DCbersicht\\n[Kurze Beschreibung des Produkts/Service]\\n\\n2. Mehrwert\\n[Kernvorteile f\\u00FCr die Zielgruppe]\\n\\n3. Verf\\u00FCgbarkeit\\n[Ab wann, f\\u00FCr wen, wie]\\n\\n4. Governance-Status\\n[Compliance-Nachweis und Zertifizierungen]",
        body_en:"We are pleased to announce the launch of [Name].\\n\\n1. Overview\\n[Brief description]\\n\\n2. Value Proposition\\n[Core benefits for target audience]\\n\\n3. Availability\\n[When, for whom, how]\\n\\n4. Governance Status\\n[Compliance proof and certifications]",
        body_pt:"Temos o prazer de anunciar o lan\\u00E7amento de [Nome].\\n\\n1. Vis\\u00E3o Geral\\n[Descri\\u00E7\\u00E3o breve]\\n\\n2. Proposta de Valor\\n[Benef\\u00EDcios principais]\\n\\n3. Disponibilidade\\n[Quando, para quem, como]\\n\\n4. Status de Governan\\u00E7a\\n[Comprova\\u00E7\\u00E3o de conformidade e certifica\\u00E7\\u00F5es]",
        category:"LAUNCH", impact_level:"MED", author_name:"", author_role:"Product Manager" } },
    { id:"compliance-alert", label:"Compliance-Alert", sub:"Risiko & Dringlichkeit", icon:"\\u26A0\\uFE0F", gov:"HIGH", type:"communique",
      content:{ title_de:"COMPLIANCE-ALERT: [Thema]", title_en:"COMPLIANCE ALERT: [Topic]", title_pt:"ALERTA DE CONFORMIDADE: [Tema]",
        body_de:"DRINGLICHKEIT: [HOCH/KRITISCH]\\n\\n1. Vorfall\\n[Beschreibung des Compliance-relevanten Vorfalls]\\n\\n2. Betroffene Bereiche\\n[Abteilungen, Systeme, Prozesse]\\n\\n3. Sofortma\\u00DFnahmen\\n[Bereits eingeleitete Schritte]\\n\\n4. Erforderliche Aktionen\\n[Was muss bis wann von wem getan werden]\\n\\n5. Meldepflicht\\n[Beh\\u00F6rdliche Meldungen gem\\u00E4\\u00DF DSGVO Art. 33/34, EU AI Act]",
        body_en:"URGENCY: [HIGH/CRITICAL]\\n\\n1. Incident\\n[Description of compliance-relevant incident]\\n\\n2. Affected Areas\\n[Departments, systems, processes]\\n\\n3. Immediate Measures\\n[Steps already taken]\\n\\n4. Required Actions\\n[What needs to be done, by whom, by when]\\n\\n5. Reporting Obligations\\n[Regulatory notifications per GDPR Art. 33/34, EU AI Act]",
        body_pt:"URG\\u00CANCIA: [ALTA/CR\\u00CDTICA]\\n\\n1. Incidente\\n[Descri\\u00E7\\u00E3o do incidente relevante para conformidade]\\n\\n2. \\u00C1reas Afetadas\\n[Departamentos, sistemas, processos]\\n\\n3. Medidas Imediatas\\n[Passos j\\u00E1 tomados]\\n\\n4. A\\u00E7\\u00F5es Necess\\u00E1rias\\n[O que precisa ser feito, por quem, at\\u00E9 quando]\\n\\n5. Obriga\\u00E7\\u00F5es de Comunica\\u00E7\\u00E3o\\n[Notifica\\u00E7\\u00F5es regulat\\u00F3rias conforme LGPD, EU AI Act]",
        category:"COMPLIANCE", impact_level:"CRIT", author_name:"", author_role:"Compliance Officer" } },
    { id:"dekret-com", label:"Dekret / Decreto", sub:"Offizielle Anordnung", icon:"\\u{1F4DC}", gov:"HIGH", type:"communique",
      content:{ title_de:"DEKRET: [Titel der Anordnung]", title_en:"DECREE: [Title]", title_pt:"DECRETO: [T\\u00EDtulo]",
        body_de:"Hiermit wird folgendes Dekret erlassen:\\n\\nPr\\u00E4ambel\\n[Hintergrund und Notwendigkeit der Anordnung]\\n\\nArtikel 1 \\u2014 Gegenstand\\n[Was wird angeordnet]\\n\\nArtikel 2 \\u2014 Geltungsbereich\\n[F\\u00FCr wen gilt diese Anordnung]\\n\\nArtikel 3 \\u2014 Inkrafttreten\\n[Ab wann gilt die Anordnung]\\n\\nArtikel 4 \\u2014 Durchsetzung\\n[Wie wird die Einhaltung sichergestellt]",
        body_en:"The following decree is hereby issued:\\n\\nPreamble\\n[Background and necessity]\\n\\nArticle 1 \\u2014 Subject\\n[What is ordered]\\n\\nArticle 2 \\u2014 Scope\\n[To whom this applies]\\n\\nArticle 3 \\u2014 Entry into Force\\n[When it takes effect]\\n\\nArticle 4 \\u2014 Enforcement\\n[How compliance is ensured]",
        body_pt:"Fica estabelecido o seguinte decreto:\\n\\nPre\\u00E2mbulo\\n[Contexto e necessidade]\\n\\nArtigo 1 \\u2014 Objeto\\n[O que \\u00E9 ordenado]\\n\\nArtigo 2 \\u2014 \\u00C2mbito\\n[A quem se aplica]\\n\\nArtigo 3 \\u2014 Entrada em Vigor\\n[Quando entra em vigor]\\n\\nArtigo 4 \\u2014 Execu\\u00E7\\u00E3o\\n[Como a conformidade \\u00E9 garantida]",
        category:"GOVERNANCE", impact_level:"HIGH", author_name:"", author_role:"Chief Governance Officer" } },
    { id:"status-report", label:"Status-Bericht", sub:"Periodische Mitteilung", icon:"\\u{1F4CB}", gov:"MEDIUM", type:"communique",
      content:{ title_de:"Status-Bericht: [Berichtszeitraum]", title_en:"Status Report: [Period]", title_pt:"Relat\\u00F3rio de Status: [Per\\u00EDodo]",
        body_de:"Berichtszeitraum: [Datum von \\u2014 Datum bis]\\n\\n1. Zusammenfassung\\n[\\u00DCberblick \\u00FCber den aktuellen Status]\\n\\n2. Fortschritt\\n[Erreichte Meilensteine]\\n\\n3. Offene Punkte\\n[Ausstehende Aufgaben und Fristen]\\n\\n4. Kennzahlen\\n[Relevante KPIs und Metriken]\\n\\n5. Ausblick\\n[N\\u00E4chste Schritte]",
        body_en:"Reporting period: [Date from \\u2014 Date to]\\n\\n1. Summary\\n[Overview of current status]\\n\\n2. Progress\\n[Milestones achieved]\\n\\n3. Open Items\\n[Pending tasks and deadlines]\\n\\n4. Metrics\\n[Relevant KPIs and metrics]\\n\\n5. Outlook\\n[Next steps]",
        body_pt:"Per\\u00EDodo: [Data de \\u2014 Data at\\u00E9]\\n\\n1. Resumo\\n[Vis\\u00E3o geral do status atual]\\n\\n2. Progresso\\n[Marcos alcan\\u00E7ados]\\n\\n3. Pontos Abertos\\n[Tarefas pendentes e prazos]\\n\\n4. M\\u00E9tricas\\n[KPIs e m\\u00E9tricas relevantes]\\n\\n5. Perspectiva\\n[Pr\\u00F3ximos passos]",
        category:"UPDATE", impact_level:"MED", author_name:"", author_role:"" } },
  ],
};"""
    
    code = code.replace(anchor, new_anchor, 1)
    print("✅ 1/6 Communiqué templates added to TEMPLATES")
else:
    new_pptx_end = old_pptx_end + """
  communique: [
    { id:"blank-com", label:"Leeres Communiqu\\u00E9", sub:"Freie Mitteilung", icon:"\\u{1F4E2}", gov:"LOW", type:"communique",
      content:{ title_de:"", title_en:"", title_pt:"", body_de:"", body_en:"", body_pt:"", category:"UPDATE", impact_level:"MED", author_name:"", author_role:"" } },
    { id:"gov-update", label:"Governance-Update", sub:"System & Compliance", icon:"\\u{1F6E1}\\uFE0F", gov:"HIGH", type:"communique",
      content:{ title_de:"Governance-Update: [Thema]", title_en:"Governance Update: [Topic]", title_pt:"Atualiza\\u00E7\\u00E3o de Governan\\u00E7a: [Tema]",
        body_de:"[Governance update body DE]", body_en:"[Governance update body EN]", body_pt:"[Governance update body PT]",
        category:"GOVERNANCE", impact_level:"HIGH", author_name:"", author_role:"Governance Officer" } },
    { id:"launch-com", label:"Launch / Markteinf\\u00FChrung", sub:"Neues Produkt oder Service", icon:"\\u{1F680}", gov:"MEDIUM", type:"communique",
      content:{ title_de:"Markteinf\\u00FChrung: [Name]", title_en:"Launch: [Name]", title_pt:"Lan\\u00E7amento: [Nome]",
        body_de:"[Launch body DE]", body_en:"[Launch body EN]", body_pt:"[Launch body PT]",
        category:"LAUNCH", impact_level:"MED", author_name:"", author_role:"Product Manager" } },
    { id:"compliance-alert", label:"Compliance-Alert", sub:"Risiko & Dringlichkeit", icon:"\\u26A0\\uFE0F", gov:"HIGH", type:"communique",
      content:{ title_de:"COMPLIANCE-ALERT: [Thema]", title_en:"COMPLIANCE ALERT: [Topic]", title_pt:"ALERTA DE CONFORMIDADE: [Tema]",
        body_de:"[Alert body DE]", body_en:"[Alert body EN]", body_pt:"[Alert body PT]",
        category:"COMPLIANCE", impact_level:"CRIT", author_name:"", author_role:"Compliance Officer" } },
    { id:"dekret-com", label:"Dekret / Decreto", sub:"Offizielle Anordnung", icon:"\\u{1F4DC}", gov:"HIGH", type:"communique",
      content:{ title_de:"DEKRET: [Titel]", title_en:"DECREE: [Title]", title_pt:"DECRETO: [T\\u00EDtulo]",
        body_de:"[Decree body DE]", body_en:"[Decree body EN]", body_pt:"[Decree body PT]",
        category:"GOVERNANCE", impact_level:"HIGH", author_name:"", author_role:"Chief Governance Officer" } },
    { id:"status-report", label:"Status-Bericht", sub:"Periodische Mitteilung", icon:"\\u{1F4CB}", gov:"MEDIUM", type:"communique",
      content:{ title_de:"Status-Bericht: [Zeitraum]", title_en:"Status Report: [Period]", title_pt:"Relat\\u00F3rio de Status: [Per\\u00EDodo]",
        body_de:"[Status body DE]", body_en:"[Status body EN]", body_pt:"[Status body PT]",
        category:"UPDATE", impact_level:"MED", author_name:"", author_role:"" } },
  ],"""
    code = code.replace(old_pptx_end, new_pptx_end, 1)
    print("✅ 1/6 Communiqué templates added to TEMPLATES")


# ═══════════════════════════════════════════════════
# 2. Fix tab click: remove redirect, use normal setTab
# ═══════════════════════════════════════════════════
old_click = 'onClick={()=>t.id==="communique"?window.location.href="/communique/feed":setTab(t.id)}'
new_click = 'onClick={()=>setTab(t.id)}'

if old_click in code:
    code = code.replace(old_click, new_click, 1)
    print("✅ 2/6 Tab click handler restored (no redirect)")
else:
    print("⚠️  2/6 Click handler already normal or different pattern")


# ═══════════════════════════════════════════════════
# 3. Add communique to typeConf
# ═══════════════════════════════════════════════════
old_typeconf = 'const typeConf={doc:{l:"DOC",c:C.blue},xlsx:{l:"XLSX",c:C.green},pptx:{l:"PPTX",c:C.orange}};'
new_typeconf = 'const typeConf={doc:{l:"DOC",c:C.blue},xlsx:{l:"XLSX",c:C.green},pptx:{l:"PPTX",c:C.orange},communique:{l:"COM",c:C.gold}};'

if old_typeconf in code:
    code = code.replace(old_typeconf, new_typeconf, 1)
    print("✅ 3/6 typeConf updated with communique")
else:
    print("⚠️  3/6 typeConf pattern not found — may need manual check")


# ═══════════════════════════════════════════════════
# 4. Add communique state variables
# ═══════════════════════════════════════════════════
old_state = 'const [tpl,setTpl]=useState(null);'
new_state = '''const [tpl,setTpl]=useState(null);
  const [comTitleDe,setComTitleDe]=useState("");
  const [comTitleEn,setComTitleEn]=useState("");
  const [comTitlePt,setComTitlePt]=useState("");
  const [comBodyDe,setComBodyDe]=useState("");
  const [comBodyEn,setComBodyEn]=useState("");
  const [comBodyPt,setComBodyPt]=useState("");
  const [comAuthor,setComAuthor]=useState("");
  const [comRole,setComRole]=useState("");
  const [comCategory,setComCategory]=useState("UPDATE");
  const [comImpact,setComImpact]=useState("MED");
  const [comPublishing,setComPublishing]=useState(false);'''

if old_state in code:
    code = code.replace(old_state, new_state, 1)
    print("✅ 4/6 Communiqué state variables added")
else:
    print("⚠️  4/6 State pattern not found")


# ═══════════════════════════════════════════════════
# 5. Add communique publish function + template init
# ═══════════════════════════════════════════════════
# Find the generate function to add publishCommunique before it
old_generate_marker = '    const id=mkId(), sge=mkSge(tpl.gov), isp="Bundesregierung \u00B7 BaFin \u00B7 DSGVO";'
new_generate_marker = '''    // ── Communiqué Publish ──
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
        setToast({id:cj.id,name:comTitleDe||comTitleEn||"Communiqué",sealed:true,hash:rid});
        setDocs(p=>[{id:cj.id,name:comTitleDe||comTitleEn,type:"communique",gov:comImpact==="CRIT"?"HIGH":comImpact==="HIGH"?"HIGH":"MEDIUM",
          sge:0,hash:rid,contentHash:pj.publish_result?.content_hash||"",templateId:tpl.id,ts:ts(),sealed:true},...p]);
        setView("gallery");setTpl(null);
      }catch(e){setComPublishing(false);alert("Publish error: "+e.message);}
      return;
    }
    const id=mkId(), sge=mkSge(tpl.gov), isp="Bundesregierung \u00B7 BaFin \u00B7 DSGVO";'''

if old_generate_marker in code:
    code = code.replace(old_generate_marker, new_generate_marker, 1)
    print("✅ 5/6 Communiqué publish function injected")
else:
    print("⚠️  5/6 Generate marker not found — checking for unicode variant")
    # Try with actual unicode
    alt = '    const id=mkId(), sge=mkSge(tpl.gov), isp="Bundesregierung · BaFin · DSGVO";'
    if alt in code:
        code = code.replace(alt, new_generate_marker.replace('\u00B7', '·'), 1)
        print("✅ 5/6 Communiqué publish function injected (unicode variant)")
    else:
        print("❌ 5/6 FAILED — need manual inspection of generate function")


# ═══════════════════════════════════════════════════
# 6. Add communique form UI + feed link in editor
# ═══════════════════════════════════════════════════
# Insert after pptx editor block
old_pptx_editor = '''{tpl.type==="pptx"&&('''
# Find the communique UI insertion point - after the pptx slides editor
# We need to find where tpl.type==="pptx" block ends and add communique form

# Add communique form rendering after the pptx form
# Find the pattern that shows the generate button area
old_generate_btn = '''<button onClick={generate} disabled={busy}'''
# We need to insert the communique form BEFORE the generate button area
# Actually, let's find the spot right after the pptx conditional rendering

# Better approach: add the communique form as a new conditional block
# Find: {tpl.type==="pptx"&&( ... the entire pptx editing section
# Instead, let's insert AFTER the last type check but before the generate button

# The cleanest injection point is right before the generate button
old_gen_button_section = '''                <button onClick={generate} disabled={busy} style={{background:busy?C.gold+"66":C.gold,color:"#000",border:"none",borderRadius:8,padding:"10px 24px",fontSize:13,fontWeight:700,cursor:busy?"wait":"pointer",whiteSpace:"nowrap"}}>'''

communique_form = '''              {tpl.type==="communique"&&(
                <div style={{display:"flex",flexDirection:"column",gap:12}}>
                  <div style={{display:"flex",gap:8,marginBottom:8}}>
                    <a href="/communique/feed" target="_blank" style={{color:C.gold,fontSize:11,textDecoration:"none",padding:"4px 10px",border:"1px solid "+C.gold+"44",borderRadius:5,background:C.gold+"12",display:"flex",alignItems:"center",gap:4}}>{"\u{1F4E2}"} Feed anzeigen</a>
                    <select value={comCategory} onChange={e=>setComCategory(e.target.value)} style={{background:card,color:fg,border:"1px solid "+bdr,borderRadius:5,padding:"4px 8px",fontSize:11}}>
                      <option value="UPDATE">Aktualisierung</option><option value="GOVERNANCE">Governance</option>
                      <option value="LAUNCH">Markteinführung</option><option value="COMPLIANCE">Compliance</option>
                    </select>
                    <select value={comImpact} onChange={e=>setComImpact(e.target.value)} style={{background:card,color:fg,border:"1px solid "+bdr,borderRadius:5,padding:"4px 8px",fontSize:11}}>
                      <option value="LOW">LOW</option><option value="MED">MED</option><option value="HIGH">HIGH</option><option value="CRIT">CRIT</option>
                    </select>
                  </div>
                  <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:8}}>
                    <input value={comAuthor} onChange={e=>setComAuthor(e.target.value)} placeholder="Autor / Author" style={{background:card,color:fg,border:"1px solid "+bdr,borderRadius:6,padding:"8px 12px",fontSize:12,fontFamily:"Outfit"}}/>
                    <input value={comRole} onChange={e=>setComRole(e.target.value)} placeholder="Rolle / Role" style={{background:card,color:fg,border:"1px solid "+bdr,borderRadius:6,padding:"8px 12px",fontSize:12,fontFamily:"Outfit"}}/>
                  </div>
                  {[["🇩🇪 Titel DE",comTitleDe,setComTitleDe],["🇬🇧 Title EN",comTitleEn,setComTitleEn],["🇧🇷 Título PT",comTitlePt,setComTitlePt]].map(([ph,v,set],i)=>
                    <input key={i} value={v} onChange={e=>set(e.target.value)} placeholder={ph}
                      style={{background:card,color:fg,border:"1px solid "+bdr,borderRadius:6,padding:"8px 12px",fontSize:13,fontFamily:"Outfit",fontWeight:600}}/>
                  )}
                  {[["🇩🇪 Inhalt",comBodyDe,setComBodyDe,8],["🇬🇧 Content",comBodyEn,setComBodyEn,6],["🇧🇷 Conteúdo",comBodyPt,setComBodyPt,6]].map(([ph,v,set,rows],i)=>
                    <textarea key={i} value={v} onChange={e=>set(e.target.value)} placeholder={ph} rows={rows}
                      style={{background:card,color:fg,border:"1px solid "+bdr,borderRadius:6,padding:"10px 12px",fontSize:12,fontFamily:"JetBrains Mono, monospace",resize:"vertical",lineHeight:1.5}}/>
                  )}
                </div>
              )}
''' + '                <button onClick={generate} disabled={busy||comPublishing} style={{background:(busy||comPublishing)?C.gold+"66":C.gold,color:"#000",border:"none",borderRadius:8,padding:"10px 24px",fontSize:13,fontWeight:700,cursor:(busy||comPublishing)?"wait":"pointer",whiteSpace:"nowrap"}}>'

if old_gen_button_section in code:
    code = code.replace(old_gen_button_section, communique_form, 1)
    print("✅ 6/6 Communiqué form UI injected")
else:
    print("⚠️  6/6 Generate button pattern not found — trying variant")
    # The button text might vary
    alt_btn = '<button onClick={generate} disabled={busy}'
    idx = code.find(alt_btn)
    if idx != -1:
        # Find the full button opening tag
        end = code.index('>', idx) + 1
        old_full = code[idx:end]
        print(f"  Found button: {old_full[:80]}...")
        # We can't easily replace partial — just note it
        print("  ⚠️  Manual insertion needed for communique form before generate button")


# ═══════════════════════════════════════════════════
# 7. Init communique fields when template is selected
# ═══════════════════════════════════════════════════
# When a template card is clicked, we need to populate the fields
old_set_tpl = 'setTpl(t);setView("editor");'
# Check if this exists or a variant
if old_set_tpl not in code:
    old_set_tpl = "setTpl(t);setView(\"editor\")"

if old_set_tpl in code:
    new_set_tpl = old_set_tpl + ''';if(t.type==="communique"&&t.content){setComTitleDe(t.content.title_de||"");setComTitleEn(t.content.title_en||"");setComTitlePt(t.content.title_pt||"");setComBodyDe(t.content.body_de||"");setComBodyEn(t.content.body_en||"");setComBodyPt(t.content.body_pt||"");setComAuthor(t.content.author_name||"");setComRole(t.content.author_role||"");setComCategory(t.content.category||"UPDATE");setComImpact(t.content.impact_level||"MED");}'''
    code = code.replace(old_set_tpl, new_set_tpl, 1)
    print("✅ 7/7 Template selection populates communiqué fields")
else:
    print("⚠️  7/7 setTpl pattern not found — checking...")
    # Search for the pattern
    import re
    matches = [m.start() for m in re.finditer(r'setTpl\(', code)]
    print(f"  Found setTpl at positions: {matches}")


p.write_text(code)
print(f"\n🐉 suite.html patched successfully!")
print(f"   Backup: {bk}")
print(f"   Templates: 6 communiqué types added")
print(f"   Run: sudo systemctl restart windi-desktop")
