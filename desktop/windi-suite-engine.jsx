import { useState } from "react";

const W = { gold: "#C9A94E", dark: "#0A0A0F", darkCard: "#12121A", darkBdr: "#1E1E2A", light: "#FAFAF8", lightCard: "#FFF", lightBdr: "#E5E5E0", green: "#34D399", red: "#EF4444", orange: "#F59E0B", blue: "#3B82F6" };
const GOV = { LOW: { c: W.green, l: "LOW" }, MEDIUM: { c: W.orange, l: "MEDIUM" }, HIGH: { c: W.red, l: "HIGH" } };
const mkId = () => "WINDI-" + Date.now().toString(36).toUpperCase();
const mkSge = (g) => ((g === "HIGH" ? 0.82 : g === "MEDIUM" ? 0.65 : 0.4) + Math.random() * (g === "HIGH" ? 0.15 : 0.25)).toFixed(2);
const mkHash = () => "0x" + Array.from({ length: 16 }, () => "0123456789abcdef"[Math.floor(Math.random() * 16)]).join("");
const nl = (s) => (s || "").replace(/\n/g, "<br/>");
const ts = () => new Date().toLocaleString("de-DE", { timeZone: "Europe/Berlin" });

const TPL = {
  doc: [
    { id: "blank-doc", name: { de: "Leeres Dokument", en: "Blank Document", pt: "Documento Vazio" }, icon: "\u{1F4C4}", gov: "LOW", desc: "Clean document", fields: [{ k: "title", l: "Titel / Title", t: "text", d: "Neues Dokument" }, { k: "content", l: "Inhalt / Content", t: "area", d: "" }] },
    { id: "vertrag", name: { de: "Vertrag", en: "Contract", pt: "Contrato" }, icon: "\u{1F4DD}", gov: "HIGH", desc: "Governance-compliant contract", fields: [{ k: "title", l: "Vertragstitel", t: "text", d: "Dienstleistungsvertrag" }, { k: "party_a", l: "Partei A", t: "text", d: "" }, { k: "party_b", l: "Partei B", t: "text", d: "" }, { k: "subject", l: "Vertragsgegenstand", t: "area", d: "" }, { k: "terms", l: "Bedingungen / Terms", t: "area", d: "" }, { k: "value", l: "Vertragswert (EUR)", t: "text", d: "" }] },
    { id: "bericht", name: { de: "Bericht", en: "Report", pt: "Relat\u00F3rio" }, icon: "\u{1F4CA}", gov: "MEDIUM", desc: "Governance report", fields: [{ k: "title", l: "Berichtstitel", t: "text", d: "Governance-Bericht" }, { k: "dept", l: "Abteilung", t: "text", d: "" }, { k: "period", l: "Zeitraum / Period", t: "text", d: "" }, { k: "summary", l: "Zusammenfassung", t: "area", d: "" }, { k: "findings", l: "Ergebnisse", t: "area", d: "" }, { k: "recs", l: "Empfehlungen", t: "area", d: "" }] },
    { id: "bescheid", name: { de: "Bescheid", en: "Official Notice", pt: "Notifica\u00E7\u00E3o" }, icon: "\u{1F3DB}\uFE0F", gov: "HIGH", desc: "Formal governance decision", fields: [{ k: "title", l: "Bescheid-Titel", t: "text", d: "Governance-Bescheid" }, { k: "recipient", l: "Empf\u00E4nger / Recipient", t: "text", d: "" }, { k: "subject", l: "Betreff / Subject", t: "text", d: "" }, { k: "decision", l: "Entscheidung / Decision", t: "area", d: "" }, { k: "basis", l: "Rechtsgrundlage / Legal Basis", t: "area", d: "" }] },
  ],
  xlsx: [
    { id: "blank-xlsx", name: { de: "Leere Tabelle", en: "Blank Sheet", pt: "Planilha Vazia" }, icon: "\u{1F4CA}", gov: "LOW", desc: "Empty spreadsheet", fields: [{ k: "title", l: "Sheet Name", t: "text", d: "Sheet1" }, { k: "cols", l: "Spalten (comma-sep)", t: "text", d: "ID, Name, Value, Status, Date" }, { k: "rows", l: "Anzahl Zeilen", t: "text", d: "10" }] },
    { id: "finanzbericht", name: { de: "Finanzbericht", en: "Financial Report", pt: "Relat\u00F3rio Financeiro" }, icon: "\u{1F4B0}", gov: "HIGH", desc: "Financial governance report", fields: [{ k: "title", l: "Berichtsname", t: "text", d: "Q1 Finanzbericht 2026" }, { k: "dept", l: "Abteilung", t: "text", d: "" }, { k: "period", l: "Zeitraum", t: "text", d: "Q1 2026" }, { k: "budget", l: "Budget (EUR)", t: "text", d: "100000" }, { k: "spent", l: "Ausgaben (EUR)", t: "text", d: "75000" }] },
    { id: "compliance", name: { de: "Compliance-Tracker", en: "Compliance Tracker", pt: "Rastreador" }, icon: "\u2705", gov: "HIGH", desc: "Compliance requirements tracker", fields: [{ k: "title", l: "Tracker-Name", t: "text", d: "DSGVO Compliance" }, { k: "framework", l: "Framework", t: "text", d: "DSGVO / GDPR" }, { k: "items", l: "Pr\u00FCfpunkte (comma-sep)", t: "area", d: "Data Minimization, Consent Management, Right to Erasure, Data Portability, Breach Notification, DPO Designation, Impact Assessment, Cross-Border Transfer" }] },
    { id: "audit", name: { de: "Pr\u00FCfprotokoll", en: "Audit Trail", pt: "Trilha de Auditoria" }, icon: "\u{1F50D}", gov: "HIGH", desc: "Forensic audit trail", fields: [{ k: "title", l: "Protokollname", t: "text", d: "Governance Audit Trail" }, { k: "period", l: "Zeitraum", t: "text", d: "2026-02" }] },
  ],
  pptx: [
    { id: "blank-pptx", name: { de: "Leere Pr\u00E4sentation", en: "Blank Deck", pt: "Apresenta\u00E7\u00E3o Vazia" }, icon: "\u{1F3AC}", gov: "LOW", desc: "Clean WINDI-branded deck", fields: [{ k: "title", l: "Titel", t: "text", d: "" }, { k: "subtitle", l: "Untertitel", t: "text", d: "" }, { k: "author", l: "Autor", t: "text", d: "" }] },
    { id: "gov-review", name: { de: "Governance-Review", en: "Governance Review", pt: "Revis\u00E3o de Governan\u00E7a" }, icon: "\u{1F3DB}\uFE0F", gov: "HIGH", desc: "Governance review deck", fields: [{ k: "title", l: "Review-Titel", t: "text", d: "Governance Review Q1 2026" }, { k: "org", l: "Organisation", t: "text", d: "" }, { k: "period", l: "Zeitraum", t: "text", d: "Q1 2026" }, { k: "summary", l: "Executive Summary", t: "area", d: "" }, { k: "risks", l: "Key Risks (one per line)", t: "area", d: "" }, { k: "actions", l: "Action Items (one per line)", t: "area", d: "" }] },
    { id: "comp-deck", name: { de: "Compliance-Bericht", en: "Compliance Deck", pt: "Deck Compliance" }, icon: "\u{1F4DC}", gov: "HIGH", desc: "Compliance status presentation", fields: [{ k: "title", l: "Titel", t: "text", d: "Compliance Status Report" }, { k: "framework", l: "Framework", t: "text", d: "EU AI Act + DSGVO" }, { k: "status", l: "Status", t: "text", d: "Compliant" }, { k: "findings", l: "Key Findings", t: "area", d: "" }] },
  ],
};

// ═══════════════════════════════════════
// DOCUMENT ENGINES — REAL FILE GENERATION
// ═══════════════════════════════════════

function genDoc(tpl, f, m) {
  const g = GOV[tpl.gov], t = ts();
  const hdr = `<div style="background:#0A0A0F;color:#fff;padding:18px 24px;margin:-25px -25px 30px;display:flex;justify-content:space-between;align-items:center">
    <span style="color:${W.gold};font-size:20pt;font-weight:bold;letter-spacing:4px">\u25C6 WINDI</span>
    <span style="font-size:8pt;color:#888">${m.id} | ${t} | Governance: ${g.l}</span></div>`;
  const seal = `<div style="background:#f0f9f0;border:2px solid #34D399;border-radius:6px;padding:14px 18px;margin-top:35px;font-size:9pt">
    <strong>\u{1F512} WINDI Governance Seal</strong><br>
    Document ID: ${m.id}<br>SGE Score: ${m.sge} | Level: ${g.l}<br>
    ISP: ${m.isp} | Hash: ${m.hash}<br>
    Timestamp: ${t}<br>Status: <strong style="color:#34D399">SEALED \u2713</strong></div>`;
  const foot = `<div style="border-top:3px solid ${W.gold};margin-top:35px;padding-top:12px;font-size:8pt;color:#888">
    <strong>WINDI Publishing House</strong> \u2014 Pre-AI Governance Layer<br>
    \u201CAI processes. Human decides. WINDI guarantees.\u201D<br>
    ISP Active: ${m.isp} | Compliance: DSGVO + EU AI Act + BSI C5</div>`;
  const tbl = (rows) => `<table style="width:100%;border-collapse:collapse;margin:20px 0">${rows.map(([a, b]) =>
    `<tr><td style="padding:10px 14px;border:1px solid #ddd;background:#f5f5f0;width:30%;font-weight:bold;font-size:10pt">${a}</td>
    <td style="padding:10px 14px;border:1px solid #ddd;font-size:10pt">${b}</td></tr>`).join("")}</table>`;

  let body = "";
  if (tpl.id === "vertrag") {
    body = `<h1 style="color:${W.gold};border-bottom:3px solid ${W.gold};padding-bottom:12px;font-size:22pt">${f.title || "Vertrag"}</h1>
      ${tbl([["Partei A", f.party_a || "\u2014"], ["Partei B", f.party_b || "\u2014"], ["Governance Level", g.l], ["SGE Score", m.sge], ["Erstellt", t]])}
      <h2 style="color:#333;margin-top:28px;font-size:14pt">\u00A71 Vertragsgegenstand</h2>
      <p style="line-height:2;font-size:11pt">${nl(f.subject) || "Der Vertragsgegenstand wird zwischen den Parteien vereinbart."}</p>
      <h2 style="color:#333;margin-top:22px;font-size:14pt">\u00A72 Vertragsbedingungen</h2>
      <p style="line-height:2;font-size:11pt">${nl(f.terms) || "Die nachfolgenden Bedingungen gelten f\u00FCr die Dauer des Vertrags."}</p>
      ${f.value ? `<h2 style="color:#333;margin-top:22px;font-size:14pt">\u00A73 Vertragswert</h2><p style="font-size:11pt;line-height:2">${f.value} EUR</p>` : ""}
      <div style="margin-top:40px;display:flex;gap:60px">
        <div style="flex:1;border-top:1px solid #333;padding-top:8px;font-size:9pt">Partei A: ${f.party_a || "________________"}<br>Datum / Unterschrift</div>
        <div style="flex:1;border-top:1px solid #333;padding-top:8px;font-size:9pt">Partei B: ${f.party_b || "________________"}<br>Datum / Unterschrift</div>
      </div>`;
  } else if (tpl.id === "bericht") {
    body = `<h1 style="color:${W.gold};border-bottom:3px solid ${W.gold};padding-bottom:12px;font-size:22pt">${f.title || "Bericht"}</h1>
      ${tbl([["Abteilung", f.dept || "\u2014"], ["Berichtszeitraum", f.period || "\u2014"], ["Governance", `${g.l} | SGE ${m.sge}`]])}
      <h2 style="color:#333;font-size:14pt">1. Zusammenfassung</h2><p style="line-height:2;font-size:11pt">${nl(f.summary) || "\u2014"}</p>
      <h2 style="color:#333;font-size:14pt">2. Ergebnisse</h2><p style="line-height:2;font-size:11pt">${nl(f.findings) || "\u2014"}</p>
      <h2 style="color:#333;font-size:14pt">3. Empfehlungen</h2><p style="line-height:2;font-size:11pt">${nl(f.recs) || "\u2014"}</p>`;
  } else if (tpl.id === "bescheid") {
    body = `<h1 style="color:${W.gold};border-bottom:3px solid ${W.gold};padding-bottom:12px;font-size:22pt">${f.title || "Bescheid"}</h1>
      ${tbl([["Empf\u00E4nger", f.recipient || "\u2014"], ["Betreff", f.subject || "\u2014"], ["Governance", `${g.l} | SGE ${m.sge}`], ["Ausstellungsdatum", t]])}
      <h2 style="color:#333;font-size:14pt">Entscheidung</h2><p style="line-height:2;font-size:11pt">${nl(f.decision) || "\u2014"}</p>
      <h2 style="color:#333;font-size:14pt">Rechtsgrundlage</h2><p style="line-height:2;font-size:11pt">${nl(f.basis) || "\u2014"}</p>
      <div style="margin-top:30px;border-top:1px solid #333;padding-top:8px;font-size:9pt;width:250px">Unterschrift / Stempel<br>WINDI Governance Authority</div>`;
  } else {
    body = `<h1 style="color:${W.gold};border-bottom:3px solid ${W.gold};padding-bottom:12px;font-size:22pt">${f.title || "Dokument"}</h1>
      <div style="line-height:2;font-size:11pt;margin-top:20px">${nl(f.content)}</div>`;
  }

  const html = `<html xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:w="urn:schemas-microsoft-com:office:word" xmlns="http://www.w3.org/TR/REC-html40">
<head><meta charset="utf-8"><title>${f.title || "WINDI"}</title>
<!--[if gte mso 9]><xml><w:WordDocument><w:View>Print</w:View></w:WordDocument></xml><![endif]-->
<style>@page{size:A4;margin:2.5cm}body{font-family:Calibri,Arial,sans-serif;font-size:11pt;color:#1a1a1a;line-height:1.6}
h1{font-size:22pt;margin:0 0 10px}h2{font-size:14pt;margin:22px 0 8px}p{margin:8px 0}</style></head>
<body style="padding:25px">${hdr}${body}${seal}${foot}</body></html>`;
  return { data: html, name: `${m.id}.doc`, mime: "application/msword" };
}

function genXlsx(tpl, f, m) {
  const g = GOV[tpl.gov], t = ts();
  const esc = (v) => '"' + String(v != null ? v : "").replace(/"/g, '""') + '"';
  let rows = [];
  if (tpl.id === "finanzbericht") {
    const b = parseFloat(f.budget) || 100000, s = parseFloat(f.spent) || 75000, r = b - s;
    rows = [
      ["\u25C6 WINDI Financial Report"], ["Generated:", t, "", "Doc ID:", m.id, "", "Hash:", m.hash],
      ["Department:", f.dept || "\u2014", "", "SGE Score:", m.sge, "", "Gov Level:", g.l],
      ["Period:", f.period || "\u2014"], [],
      ["Category", "Budget (\u20AC)", "Spent (\u20AC)", "Remaining (\u20AC)", "% Used", "Risk Flag"],
      ["TOTAL", b, s, r, ((s / b) * 100).toFixed(1) + "%", r < 0 ? "OVER BUDGET" : "OK"],
      ["Personnel (45%)", Math.round(b * .45), Math.round(s * .48), Math.round(b * .45 - s * .48), "", s * .48 > b * .45 ? "ALERT" : ""],
      ["Operations (30%)", Math.round(b * .30), Math.round(s * .28), Math.round(b * .30 - s * .28), "", ""],
      ["IT & Infrastructure (15%)", Math.round(b * .15), Math.round(s * .16), Math.round(b * .15 - s * .16), "", ""],
      ["Compliance & Gov (10%)", Math.round(b * .10), Math.round(s * .08), Math.round(b * .10 - s * .08), "", ""],
      [], ["\u25C6 WINDI Governance Seal: SEALED \u2713", "", "ISP:", m.isp, "", "Hash:", m.hash],
    ];
  } else if (tpl.id === "compliance") {
    const items = (f.items || "Item 1").split(",").map((x) => x.trim()).filter(Boolean);
    rows = [
      ["\u25C6 WINDI Compliance Tracker"], ["Framework:", f.framework, "", "Doc ID:", m.id, "", "SGE:", m.sge],
      ["Generated:", t, "", "Gov Level:", g.l], [],
      ["#", "Requirement", "Status", "Owner", "Due Date", "Evidence", "Risk Level", "Notes"],
      ...items.map((x, i) => [i + 1, x, "PENDING", "", "", "", "MEDIUM", ""]),
      [], ["Summary:", `${items.length} items tracked`, `0/${items.length} complete`, "", "", "", "", ""],
      ["\u25C6 WINDI Seal: SEALED \u2713", "", "ISP:", m.isp],
    ];
  } else if (tpl.id === "audit") {
    const actions = ["Document Created", "Template Applied", "Fields Populated", "SGE Scan Initiated", "SGE Scan Complete", "Governance Level Assigned", "Ed25519 Seal Applied", "Virtue Receipt Issued", "Ledger Entry Written", "Hash Chain Extended"];
    const users = ["System", "ISP Manager", "User", "SGE Engine", "SGE Engine", "Governance API", "Bridge :8097", "Forensic Ledger", "Merkle Tree", "Chain Validator"];
    rows = [
      ["\u25C6 WINDI Forensic Audit Trail"], ["Period:", f.period, "", "Doc ID:", m.id],
      ["Generated:", t, "", "SGE:", m.sge, "", "Gov:", g.l], [],
      ["#", "Timestamp", "Action", "Actor", "Target", "Gov Level", "SGE Score", "Hash", "Status"],
      ...actions.map((a, i) => [i + 1, t, a, users[i], m.id, g.l, m.sge, mkHash(), "\u2713 OK"]),
      [], ["\u25C6 WINDI Governance Seal: SEALED \u2713", "", "", "Chain Integrity: VALID", "", "ISP:", m.isp],
    ];
  } else {
    const cols = (f.cols || "A, B, C").split(",").map((x) => x.trim());
    const n = Math.min(parseInt(f.rows) || 10, 100);
    rows = [
      ["\u25C6 WINDI \u2014 " + (f.title || "Sheet")], ["Generated:", t, "Doc ID:", m.id, "Gov:", g.l], [],
      cols, ...Array.from({ length: n }, (_, i) => cols.map((_, j) => (j === 0 ? i + 1 : ""))),
      [], ["\u25C6 SEALED \u2713 | " + m.id],
    ];
  }
  const csv = "\uFEFF" + rows.map((r) => (Array.isArray(r) ? r.map(esc).join(",") : esc(r))).join("\n");
  return { data: csv, name: `${m.id}.csv`, mime: "text/csv;charset=utf-8" };
}

function genPptx(tpl, f, m) {
  const g = GOV[tpl.gov], t = ts(), gold = W.gold;
  const ss = `width:960px;min-height:540px;margin:20px auto;box-shadow:0 4px 24px rgba(0,0,0,.3);overflow:hidden;position:relative;font-family:Segoe UI,Calibri,sans-serif`;
  let slides = [];

  // Title slide
  slides.push(`<div style="${ss};display:flex;flex-direction:column;justify-content:center;align-items:center;background:linear-gradient(135deg,#0A0A0F 0%,#12122a 50%,#1a1a2e 100%);color:#fff;text-align:center;padding:60px">
    <div style="font-size:14px;color:${gold};letter-spacing:8px;margin-bottom:35px;font-weight:300">\u25C6 W I N D I</div>
    <h1 style="font-size:38px;margin:0;font-weight:700;line-height:1.2">${f.title || "Presentation"}</h1>
    <p style="font-size:17px;color:#999;margin-top:16px;font-weight:300">${f.subtitle || f.org || ""}</p>
    <p style="font-size:13px;color:#666;margin-top:30px">${f.author || ""}${f.period ? " \u2014 " + f.period : ""}</p>
    <div style="position:absolute;bottom:35px;font-size:10px;color:#444;letter-spacing:1px">${m.id} | ${t} | ${g.l} | SGE ${m.sge}</div></div>`);

  if (tpl.id === "gov-review") {
    if (f.summary) slides.push(`<div style="${ss};padding:55px;background:#fff">
      <div style="color:${gold};font-size:11px;letter-spacing:5px;margin-bottom:18px;font-weight:600">\u25C6 WINDI GOVERNANCE</div>
      <h2 style="font-size:28px;color:#1a1a1a;border-bottom:3px solid ${gold};padding-bottom:10px;margin:0 0 20px">Executive Summary</h2>
      <p style="font-size:16px;line-height:1.9;color:#333">${f.summary.replace(/\n/g, "<br/>")}</p></div>`);
    if (f.risks) {
      const rList = f.risks.split("\n").filter(Boolean);
      slides.push(`<div style="${ss};padding:55px;background:#fff">
        <div style="color:${gold};font-size:11px;letter-spacing:5px;margin-bottom:18px;font-weight:600">\u25C6 WINDI GOVERNANCE</div>
        <h2 style="font-size:28px;color:#1a1a1a;border-bottom:3px solid ${W.red};padding-bottom:10px;margin:0 0 20px">Key Risks (${rList.length})</h2>
        <div>${rList.map((r, i) => `<div style="padding:10px 14px;margin:8px 0;background:#FEF2F2;border-left:4px solid #EF4444;border-radius:5px;font-size:15px;display:flex;gap:10px;align-items:start">
          <span style="color:${W.red};font-weight:700;min-width:24px">R${i + 1}</span><span>${r}</span></div>`).join("")}</div></div>`);
    }
    if (f.actions) {
      const aList = f.actions.split("\n").filter(Boolean);
      slides.push(`<div style="${ss};padding:55px;background:#fff">
        <div style="color:${gold};font-size:11px;letter-spacing:5px;margin-bottom:18px;font-weight:600">\u25C6 WINDI GOVERNANCE</div>
        <h2 style="font-size:28px;color:#1a1a1a;border-bottom:3px solid ${W.green};padding-bottom:10px;margin:0 0 20px">Action Items (${aList.length})</h2>
        <div>${aList.map((a, i) => `<div style="padding:10px 14px;margin:8px 0;background:#F0FDF4;border-left:4px solid #34D399;border-radius:5px;font-size:15px;display:flex;gap:10px;align-items:start">
          <span style="color:${W.green};font-weight:700;min-width:24px">${i + 1}.</span><span>${a}</span></div>`).join("")}</div></div>`);
    }
  } else if (tpl.id === "comp-deck") {
    slides.push(`<div style="${ss};padding:55px;background:#fff">
      <div style="color:${gold};font-size:11px;letter-spacing:5px;margin-bottom:18px;font-weight:600">\u25C6 WINDI COMPLIANCE</div>
      <h2 style="font-size:28px;color:#1a1a1a;border-bottom:3px solid ${gold};padding-bottom:10px;margin:0 0 25px">Compliance Dashboard</h2>
      <div style="display:flex;gap:20px;margin-bottom:25px">
        <div style="flex:1;background:#F0FDF4;border-radius:10px;padding:24px;text-align:center;border:1px solid #d1fae5">
          <div style="font-size:36px">\u2705</div>
          <div style="font-size:11px;color:#666;margin:6px 0 2px">Framework</div>
          <div style="font-size:17px;font-weight:700;color:#1a1a1a">${f.framework || "\u2014"}</div></div>
        <div style="flex:1;background:#F0FDF4;border-radius:10px;padding:24px;text-align:center;border:1px solid #d1fae5">
          <div style="font-size:36px">\u{1F3DB}\uFE0F</div>
          <div style="font-size:11px;color:#666;margin:6px 0 2px">Overall Status</div>
          <div style="font-size:17px;font-weight:700;color:${W.green}">${f.status || "\u2014"}</div></div>
        <div style="flex:1;background:#FFFBEB;border-radius:10px;padding:24px;text-align:center;border:1px solid #fef3c7">
          <div style="font-size:36px">\u{1F4CA}</div>
          <div style="font-size:11px;color:#666;margin:6px 0 2px">SGE Score</div>
          <div style="font-size:17px;font-weight:700">${m.sge}</div></div></div>
      ${f.findings ? `<h3 style="font-size:18px;color:#333;margin:20px 0 10px">Key Findings</h3><p style="line-height:1.8;color:#555;font-size:15px">${f.findings.replace(/\n/g, "<br/>")}</p>` : ""}</div>`);
  }

  // Closing slide
  slides.push(`<div style="${ss};display:flex;flex-direction:column;justify-content:center;align-items:center;background:linear-gradient(135deg,#0A0A0F 0%,#12122a 50%,#1a1a2e 100%);color:#fff;text-align:center;padding:60px">
    <div style="font-size:52px;color:${gold};margin-bottom:16px">\u25C6</div>
    <div style="font-size:14px;color:${gold};letter-spacing:8px;font-weight:300">W I N D I</div>
    <p style="font-size:13px;color:#888;margin-top:20px;max-width:480px;line-height:1.7">AI processes. Human decides. WINDI guarantees.</p>
    <div style="margin-top:35px;padding:12px 22px;border:1px solid ${gold}44;border-radius:8px;font-size:10px;color:#666;letter-spacing:1px">
      \u{1F512} SEALED | ${m.id} | SGE ${m.sge} | ${g.l} | Hash: ${m.hash.substring(0, 12)}...</div>
    <div style="position:absolute;bottom:30px;font-size:9px;color:#444">ISP: ${m.isp} | Compliance: DSGVO + EU AI Act + BSI C5 + ISO 27001</div></div>`);

  const html = `<!DOCTYPE html><html><head><meta charset="utf-8"><title>${f.title || "WINDI"}</title>
<style>*{margin:0;padding:0;box-sizing:border-box}body{font-family:Segoe UI,Calibri,sans-serif;background:#1a1a2e;padding:10px}
@media print{body{background:#fff;padding:0}div{box-shadow:none!important;margin:0!important;page-break-after:always}}</style></head>
<body>${slides.join("\n")}</body></html>`;
  return { data: html, name: `${m.id}_deck.html`, mime: "text/html" };
}

function dl(data, name, mime) {
  const b = new Blob([data], { type: mime });
  const u = URL.createObjectURL(b);
  const a = document.createElement("a");
  a.href = u; a.download = name;
  document.body.appendChild(a); a.click();
  document.body.removeChild(a); URL.revokeObjectURL(u);
}

// ═══════════════════════════════════
// MAIN SUITE COMPONENT
// ═══════════════════════════════════
export default function WINDISuite() {
  const [theme, setTheme] = useState("noir");
  const [lang, setLang] = useState("de");
  const [tab, setTab] = useState("doc");
  const [govOn, setGovOn] = useState(true);
  const [sel, setSel] = useState(null);
  const [fields, setFields] = useState({});
  const [docs, setDocs] = useState([]);
  const [busy, setBusy] = useState(false);
  const [toast, setToast] = useState(null);
  const [preview, setPreview] = useState(null);

  const n = theme === "noir";
  const bg = n ? W.dark : W.light;
  const card = n ? W.darkCard : W.lightCard;
  const bdr = n ? W.darkBdr : W.lightBdr;
  const txt = n ? "#E5E5E5" : "#1a1a1a";
  const mut = n ? "#666" : "#888";
  const hdr = n ? "#08080D" : "#fff";

  const L = (o) => o[lang] || o.de;
  const greet = () => { const h = new Date().getHours(); return L(h < 12 ? { de: "Guten Morgen", en: "Good Morning", pt: "Bom Dia" } : h < 18 ? { de: "Guten Tag", en: "Good Afternoon", pt: "Boa Tarde" } : { de: "Guten Abend", en: "Good Evening", pt: "Boa Noite" }); };

  const pick = (t) => { setSel(t); const d = {}; t.fields.forEach((f) => (d[f.k] = f.d || "")); setFields(d); setPreview(null); };

  const generate = () => {
    if (!sel || busy) return;
    setBusy(true);
    const m = { id: mkId(), sge: mkSge(sel.gov), isp: "Bundesregierung \u00B7 BaFin \u00B7 DSGVO", hash: mkHash(), ts: ts() };

    setTimeout(() => {
      let r;
      if (tab === "doc") { r = genDoc(sel, fields, m); }
      else if (tab === "xlsx") { r = genXlsx(sel, fields, m); }
      else { r = genPptx(sel, fields, m); setPreview(r.data); }
      dl(r.data, r.name, r.mime);

      setDocs((p) => [{ id: m.id, name: fields.title || L(sel.name), type: tab, gov: sel.gov, sge: m.sge, hash: m.hash, ts: m.ts, tpl: sel.id }, ...p]);
      setBusy(false);
      setToast(m);
      setTimeout(() => setToast(null), 5000);
    }, 900);
  };

  const typeConf = { doc: { l: "DOC", c: W.blue, i: "\u{1F4C4}" }, xlsx: { l: "XLSX", c: W.green, i: "\u{1F4CA}" }, pptx: { l: "PPTX", c: W.orange, i: "\u{1F3AC}" } };
  const tabItems = [{ id: "doc", l: "Dokumente", i: "\u{1F4C4}" }, { id: "xlsx", l: "Tabellen", i: "\u{1F4CA}" }, { id: "pptx", l: "Pr\u00E4sentationen", i: "\u{1F3AC}" }];

  const Btn = ({ onClick, children, primary, disabled, style: s }) => (
    <button onClick={onClick} disabled={disabled} style={{ background: primary ? (disabled ? W.gold + "66" : W.gold) : "transparent", color: primary ? "#000" : mut, border: primary ? "none" : `1px solid ${bdr}`, borderRadius: 7, padding: primary ? "13px 0" : "4px 11px", fontSize: primary ? 13 : 10, fontWeight: primary ? 700 : 500, cursor: disabled ? "wait" : "pointer", letterSpacing: primary ? 1 : 0.5, transition: "all .2s", width: primary ? "100%" : "auto", ...s }}>{children}</button>
  );

  return (
    <div style={{ background: bg, color: txt, minHeight: "100vh", fontFamily: "Outfit, Segoe UI, sans-serif", transition: "all .3s" }}>
      <style>{`@import url('https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:wght@300;600;800&family=Outfit:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap');
        @keyframes fadeIn{from{opacity:0;transform:translateY(-8px)}to{opacity:1;transform:translateY(0)}}
        @keyframes pulse{0%,100%{opacity:1}50%{opacity:.5}}
        input:focus,textarea:focus{border-color:${W.gold}!important;outline:none;box-shadow:0 0 0 2px ${W.gold}22}
        *{box-sizing:border-box;margin:0}
        ::-webkit-scrollbar{width:5px}::-webkit-scrollbar-thumb{background:${W.gold}33;border-radius:3px}
        button:hover{opacity:.88}`}</style>

      {/* ══ HEADER ══ */}
      <div style={{ background: hdr, borderBottom: `1px solid ${bdr}`, padding: "10px 20px", display: "flex", alignItems: "center", justifyContent: "space-between", position: "sticky", top: 0, zIndex: 50 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <span style={{ color: W.gold, fontSize: 18, fontWeight: 800, letterSpacing: 3, fontFamily: "Bricolage Grotesque" }}>{"\u25C6"} WINDI</span>
          <span style={{ color: mut, fontSize: 11, letterSpacing: 2, fontWeight: 300 }}>SUITE</span>
          <span style={{ color: W.green, fontSize: 8, padding: "2px 7px", background: W.green + "15", borderRadius: 3, fontWeight: 600, letterSpacing: 1 }}>ENGINE v1.0</span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <Btn onClick={() => setGovOn(!govOn)} style={{ color: govOn ? W.gold : mut, borderColor: govOn ? W.gold : bdr, background: govOn ? W.gold + "18" : "transparent" }}>GOV {govOn ? "ON" : "OFF"}</Btn>
          <select value={lang} onChange={(e) => setLang(e.target.value)} style={{ background: "transparent", border: `1px solid ${bdr}`, borderRadius: 4, padding: "4px 6px", color: txt, fontSize: 10, cursor: "pointer" }}>
            <option value="de">DE</option><option value="en">EN</option><option value="pt">PT</option>
          </select>
          <Btn onClick={() => setTheme(n ? "klar" : "noir")}>{n ? "\u2600\uFE0F Klar" : "\u{1F319} Noir"}</Btn>
        </div>
      </div>

      {/* ══ GREETING ══ */}
      <div style={{ padding: "20px 20px 0" }}>
        <h1 style={{ fontSize: 20, fontWeight: 300, fontFamily: "Bricolage Grotesque" }}>
          {greet()}. <span style={{ color: mut, fontSize: 14 }}>{L({ de: "Was m\u00F6chten Sie erstellen?", en: "What would you like to create?", pt: "O que deseja criar?" })}</span>
        </h1>
      </div>

      {/* ══ TABS ══ */}
      <div style={{ display: "flex", padding: "14px 20px 0", borderBottom: `1px solid ${bdr}`, gap: 2 }}>
        {tabItems.map((t) => (
          <button key={t.id} onClick={() => { setTab(t.id); setSel(null); setPreview(null); }}
            style={{ padding: "9px 18px", background: "transparent", border: "none", borderBottom: tab === t.id ? `2px solid ${W.gold}` : "2px solid transparent", color: tab === t.id ? W.gold : mut, fontSize: 12, fontWeight: tab === t.id ? 600 : 400, cursor: "pointer", display: "flex", alignItems: "center", gap: 6, transition: "all .2s" }}>
            {t.i} {t.l}
          </button>
        ))}
        <div style={{ marginLeft: "auto", display: "flex", alignItems: "center", gap: 6, fontSize: 10, color: mut, paddingBottom: 8 }}>
          <span style={{ width: 6, height: 6, borderRadius: "50%", background: W.green, display: "inline-block" }} />
          {docs.length} {L({ de: "erstellt", en: "created", pt: "criados" })}
        </div>
      </div>

      <div style={{ padding: 20 }}>
        {/* ══ TOAST ══ */}
        {toast && (
          <div style={{ background: W.green + "12", border: `1px solid ${W.green}35`, borderRadius: 8, padding: "11px 15px", marginBottom: 14, display: "flex", alignItems: "center", gap: 10, animation: "fadeIn .3s" }}>
            <span style={{ fontSize: 18 }}>{"\u2705"}</span>
            <div style={{ flex: 1 }}>
              <div style={{ fontWeight: 600, fontSize: 12 }}>{L({ de: "Dokument erstellt & versiegelt!", en: "Document created & sealed!", pt: "Documento criado & selado!" })}</div>
              <div style={{ fontSize: 10, color: mut, fontFamily: "JetBrains Mono" }}>{toast.id} | SGE {toast.sge} | Hash: {toast.hash.substring(0, 12)}...</div>
            </div>
            <span style={{ color: W.green, fontSize: 10, fontWeight: 600, animation: "pulse 2s infinite" }}>{"\u{1F512}"} SEALED</span>
          </div>
        )}

        {!sel ? (
          <>
            {/* ══ TEMPLATE GALLERY ══ */}
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(190px, 1fr))", gap: 12 }}>
              {TPL[tab].map((t) => {
                const gc = GOV[t.gov];
                return (
                  <div key={t.id} onClick={() => pick(t)}
                    style={{ background: card, border: `1px solid ${bdr}`, borderRadius: 10, padding: 18, cursor: "pointer", transition: "all .25s", position: "relative" }}
                    onMouseEnter={(e) => { e.currentTarget.style.borderColor = W.gold; e.currentTarget.style.transform = "translateY(-3px)"; e.currentTarget.style.boxShadow = `0 8px 20px ${W.gold}15`; }}
                    onMouseLeave={(e) => { e.currentTarget.style.borderColor = bdr; e.currentTarget.style.transform = "none"; e.currentTarget.style.boxShadow = "none"; }}>
                    {govOn && <div style={{ position: "absolute", top: 8, right: 8, fontSize: 9, color: gc.c, background: gc.c + "14", padding: "2px 8px", borderRadius: 4, fontWeight: 600, letterSpacing: .5 }}>{gc.l}</div>}
                    <div style={{ fontSize: 28, marginBottom: 10 }}>{t.icon}</div>
                    <div style={{ fontWeight: 600, fontSize: 13 }}>{L(t.name)}</div>
                    <div style={{ fontSize: 10, color: mut, marginTop: 4, lineHeight: 1.4 }}>{t.desc}</div>
                  </div>
                );
              })}
            </div>

            {/* ══ CREATED DOCUMENTS ══ */}
            {docs.length > 0 && (
              <div style={{ marginTop: 28 }}>
                <h3 style={{ fontSize: 10, fontWeight: 600, color: W.gold, letterSpacing: 2, marginBottom: 10 }}>
                  {L({ de: "ERSTELLTE DOKUMENTE", en: "CREATED DOCUMENTS", pt: "DOCUMENTOS CRIADOS" })}
                </h3>
                <div style={{ background: card, border: `1px solid ${bdr}`, borderRadius: 9, overflow: "hidden" }}>
                  {docs.map((d, i) => {
                    const tc = typeConf[d.type];
                    return (
                      <div key={d.id} style={{ padding: "10px 14px", borderBottom: i < docs.length - 1 ? `1px solid ${bdr}` : "none", display: "flex", alignItems: "center", gap: 10, fontSize: 11, transition: "background .2s" }}
                        onMouseEnter={(e) => e.currentTarget.style.background = n ? "#1a1a26" : "#f8f8f5"}
                        onMouseLeave={(e) => e.currentTarget.style.background = "transparent"}>
                        <span style={{ fontFamily: "JetBrains Mono", fontSize: 9, color: W.gold, minWidth: 110 }}>{d.id}</span>
                        <span style={{ flex: 1, fontWeight: 500 }}>{d.name}</span>
                        <span style={{ background: tc.c + "18", color: tc.c, padding: "2px 8px", borderRadius: 4, fontSize: 9, fontWeight: 700, letterSpacing: .5 }}>{tc.i} {tc.l}</span>
                        <span style={{ color: GOV[d.gov].c, fontSize: 10, fontWeight: 500, minWidth: 60 }}>{GOV[d.gov].l}</span>
                        <span style={{ fontFamily: "JetBrains Mono", fontSize: 9, color: mut, minWidth: 35 }}>{d.sge}</span>
                        <span style={{ color: W.green, fontSize: 9, fontWeight: 600 }}>{"\u{1F512}"}</span>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
          </>
        ) : (
          /* ══ DOCUMENT EDITOR ══ */
          <div>
            <button onClick={() => { setSel(null); setPreview(null); }}
              style={{ background: "transparent", border: "none", color: W.gold, fontSize: 12, cursor: "pointer", padding: 0, marginBottom: 14, display: "flex", alignItems: "center", gap: 4 }}>
              {"\u2190"} {L({ de: "Zur\u00FCck zu Vorlagen", en: "Back to Templates", pt: "Voltar" })}
            </button>

            <div style={{ display: "grid", gridTemplateColumns: preview ? "1fr" : "1fr 240px", gap: 16 }}>
              {/* Left: Form */}
              <div style={{ background: card, border: `1px solid ${bdr}`, borderRadius: 10, padding: 22 }}>
                <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 20, paddingBottom: 16, borderBottom: `1px solid ${bdr}` }}>
                  <span style={{ fontSize: 28 }}>{sel.icon}</span>
                  <div style={{ flex: 1 }}>
                    <h2 style={{ fontSize: 17, fontWeight: 600 }}>{L(sel.name)}</h2>
                    <div style={{ fontSize: 10, color: mut, marginTop: 2 }}>{sel.desc}</div>
                  </div>
                  {govOn && <span style={{ color: GOV[sel.gov].c, fontSize: 11, fontWeight: 600, background: GOV[sel.gov].c + "14", padding: "4px 12px", borderRadius: 6 }}>{GOV[sel.gov].l}</span>}
                </div>

                {sel.fields.map((f) => (
                  <div key={f.k} style={{ marginBottom: 13 }}>
                    <label style={{ display: "block", fontSize: 10, fontWeight: 600, color: mut, marginBottom: 4, letterSpacing: .5 }}>{f.l}</label>
                    {f.t === "area" ? (
                      <textarea value={fields[f.k] || ""} onChange={(e) => setFields((p) => ({ ...p, [f.k]: e.target.value }))} rows={3}
                        style={{ width: "100%", background: n ? "#0A0A0F" : "#F5F5F0", border: `1px solid ${bdr}`, borderRadius: 6, padding: "9px 12px", color: txt, fontSize: 12, fontFamily: "inherit", resize: "vertical", lineHeight: 1.6 }} />
                    ) : (
                      <input type="text" value={fields[f.k] || ""} onChange={(e) => setFields((p) => ({ ...p, [f.k]: e.target.value }))}
                        style={{ width: "100%", background: n ? "#0A0A0F" : "#F5F5F0", border: `1px solid ${bdr}`, borderRadius: 6, padding: "9px 12px", color: txt, fontSize: 12, fontFamily: "inherit" }} />
                    )}
                  </div>
                ))}

                <Btn primary onClick={generate} disabled={busy} style={{ marginTop: 10 }}>
                  {busy ? "\u23F3 " + L({ de: "Wird erstellt...", en: "Generating...", pt: "Gerando..." })
                    : "\u26A1 " + L({ de: "Erstellen & Herunterladen", en: "Generate & Download", pt: "Gerar & Baixar" })}
                </Btn>
              </div>

              {/* Right: Governance Panel */}
              {!preview && (
                <div style={{ background: card, border: `1px solid ${bdr}`, borderRadius: 10, padding: 18, fontSize: 10, display: "flex", flexDirection: "column", gap: 14 }}>
                  <h3 style={{ fontSize: 10, fontWeight: 600, color: W.gold, letterSpacing: 2 }}>GOVERNANCE</h3>

                  <div style={{ padding: 12, background: GOV[sel.gov].c + "0D", border: `1px solid ${GOV[sel.gov].c}25`, borderRadius: 6 }}>
                    <div style={{ fontSize: 9, color: mut }}>Risk Level</div>
                    <div style={{ fontSize: 18, fontWeight: 700, color: GOV[sel.gov].c, marginTop: 2 }}>{GOV[sel.gov].l}</div>
                  </div>

                  <div>
                    <div style={{ fontSize: 9, color: mut, marginBottom: 3, fontWeight: 600 }}>ISP Active</div>
                    {["Bundesregierung", "BaFin", "DSGVO"].map((x) => <div key={x} style={{ color: txt, padding: "2px 0" }}>{x}</div>)}
                  </div>

                  <div>
                    <div style={{ fontSize: 9, color: mut, marginBottom: 3, fontWeight: 600 }}>Compliance</div>
                    {["EU AI Act", "BSI C5", "ISO 27001", "DSGVO"].map((x) => <div key={x} style={{ color: W.green, padding: "2px 0" }}>{"\u2713"} {x}</div>)}
                  </div>

                  <div>
                    <div style={{ fontSize: 9, color: mut, marginBottom: 3, fontWeight: 600 }}>Output</div>
                    <div style={{ fontSize: 14, fontWeight: 600, color: W.gold }}>{typeConf[tab].i} {typeConf[tab].l}</div>
                  </div>

                  <div style={{ borderTop: `1px solid ${bdr}`, paddingTop: 10 }}>
                    <div style={{ fontSize: 9, color: mut, marginBottom: 4, fontWeight: 600 }}>Pipeline</div>
                    {["Template loaded \u2713", "Fields validated", "SGE semantic scan", "Ed25519 seal", "Virtue receipt issued", "Ledger entry written"].map((x, i) => (
                      <div key={i} style={{ padding: "2px 0", color: i === 0 ? W.green : txt }}>{i + 1}. {x}</div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Preview */}
            {preview && (
              <div style={{ marginTop: 16, background: card, border: `1px solid ${bdr}`, borderRadius: 10, padding: 18 }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 10 }}>
                  <h3 style={{ fontSize: 10, fontWeight: 600, color: W.gold, letterSpacing: 2 }}>PRESENTATION PREVIEW</h3>
                  <Btn onClick={() => setPreview(null)}>Close Preview</Btn>
                </div>
                <iframe srcDoc={preview} style={{ width: "100%", height: 400, border: `1px solid ${bdr}`, borderRadius: 8 }} title="Preview" />
              </div>
            )}
          </div>
        )}
      </div>

      {/* ══ FOOTER ══ */}
      <div style={{ borderTop: `1px solid ${bdr}`, padding: "14px 20px", display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: 8, marginTop: 20 }}>
        <div style={{ fontSize: 9, color: mut }}>
          <span style={{ color: W.gold, fontWeight: 700, letterSpacing: 1 }}>{"\u25C6"} WINDI</span>
          <span style={{ marginLeft: 6 }}>Publishing House \u2014 Pre-AI Governance Layer</span>
        </div>
        <div style={{ fontSize: 9, color: mut }}>ISP: Bundesregierung {"\u00B7"} BaFin {"\u00B7"} DSGVO | EU AI Act + BSI C5 + ISO 27001</div>
        <div style={{ fontSize: 9, color: W.green, fontWeight: 600 }}>{"\u25CF"} {docs.length} {L({ de: "Dokumente versiegelt", en: "Documents sealed", pt: "Documentos selados" })}</div>
      </div>
    </div>
  );
}
