/**
 * WINDI Sovereign Dispatcher v1.0
 * ================================
 * "AI processes. Human decides. WINDI guarantees."
 *
 * - Fetches live briefing from /api/briefing
 * - Fetches PDF Virtue Receipt from /api/report/pdf (if available)
 * - Sends bilingual DE/EN governance email (HTML + plaintext)
 * - Enforces recipient whitelist (WINDI_RECIPIENTS)
 * - Injects forensic headers (X-WINDI-Report-ID, X-WINDI-Hash, X-WINDI-Ledger-Ref)
 * - Logs dispatch event to Forensic Ledger
 *
 * Three Dragons Protocol: Guardian builds, Witness certifies, Architect designs.
 */

const axios = require("axios");
const nodemailer = require("nodemailer");
const crypto = require("crypto");

// ─── Configuration ───────────────────────────────────────────────
const BRIEFING_URL   = process.env.WINDI_BRIEFING_URL || "http://127.0.0.1:8090/api/briefing";
const PDF_URL        = process.env.WINDI_PDF_URL      || "http://127.0.0.1:8090/api/report/pdf";
const LEDGER_URL     = process.env.WINDI_LEDGER_URL   || "http://127.0.0.1:8080/api/ledger";
const FROM           = process.env.MAIL_FROM           || '"WINDI Sovereign System" <governance@windi.ai>';
const WAR_ROOM_URL   = process.env.WAR_ROOM_URL       || "https://master.winia4desk.tech/warroom";
const WINDI_LANG     = (process.env.WINDI_LANG || "de").toLowerCase();

// Comma-separated whitelist
const RECIPIENT_WHITELIST = (process.env.WINDI_RECIPIENTS || "")
  .split(",")
  .map((s) => s.trim().toLowerCase())
  .filter(Boolean);

// ─── Security ────────────────────────────────────────────────────
function assertAllowedRecipient(email) {
  if (!RECIPIENT_WHITELIST.length) {
    throw new Error("[DISPATCHER] BLOCKED: Recipient whitelist is empty (WINDI_RECIPIENTS). Refusing to send.");
  }
  const normalized = String(email).trim().toLowerCase();
  if (!RECIPIENT_WHITELIST.includes(normalized)) {
    throw new Error(`[DISPATCHER] BLOCKED: Recipient not on whitelist: ${email}`);
  }
}

// ─── Helpers ─────────────────────────────────────────────────────
function pickLang() {
  return WINDI_LANG === "en" ? "en" : "de";
}

function escapeHtml(s = "") {
  return String(s)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function computeAlertLevel(data) {
  const hasHighUrgency = (data.decisions || []).some(
    (d) => d.urgency === "high" && d.status === "pending"
  );
  const hasCriticalRisk = (data.riskDetails || []).some(
    (r) => r.level === "R4" || r.level === "R5"
  );
  if (hasCriticalRisk) return { emoji: "🔴", level: "CRITICAL" };
  if (hasHighUrgency || (data.risks?.active || 0) > 0) return { emoji: "⚠️", level: "HIGH" };
  return { emoji: "🛡️", level: "NOMINAL" };
}

function buildSubject(data) {
  const { emoji } = computeAlertLevel(data);
  const hash8 = (data.hash || "").toString().slice(0, 8) || "--------";
  return `${emoji} WINDI Governance Briefing | ${data.briefingDate || "—"} | Hash: ${hash8}`;
}

function formatDecision(d, lang) {
  if (!d) return lang === "de" ? "Keine offenen Punkte" : "No pending items";
  const topic = d.topic?.[lang] || d.topic?.en || "—";
  return `${topic} (SGE: ${d.sge || "—"} / ${(d.urgency || "—").toUpperCase()})`;
}

function formatComplianceBadges(compliance) {
  if (!compliance || !compliance.length) return "";
  const map = { compliant: "✅", partial: "🟡", "non-compliant": "🔴" };
  return compliance.map((c) => `${(c.k || "").toUpperCase()}: ${map[c.s] || "—"}`).join("  |  ");
}

// ─── Email Body Builder ──────────────────────────────────────────
function buildEmailBody(data) {
  const lang = pickLang();
  const summary = data.summary?.[lang] || data.summary?.en || "";
  const system = (data.systemStatus || "operational").toUpperCase();
  const decision = formatDecision(data.decisions?.[0], lang);
  const compliance = formatComplianceBadges(data.compliance);
  const { level } = computeAlertLevel(data);

  // ── Plain Text ──
  const labels = {
    de: {
      greeting: "Sehr geehrte Damen und Herren,",
      intro: "das WINDI Sovereign System hat den aktuellen Governance-Zyklus abgeschlossen.",
      status: "Systemstatus",
      chain: "Audit-Kette",
      pending: "Offener Punkt",
      alert: "Alert-Stufe",
      summary: "Kurzfassung",
      compliance: "Compliance",
      pdf: "Der vollständige signierte Forensikbericht ist als PDF beigefügt.",
      noPdf: "PDF-Bericht wird im nächsten Zyklus verfügbar sein.",
      footer: "AI verarbeitet. Sie entscheiden. WINDI garantiert.",
      warn: "Governance-relevante Informationen. Weitergabe nur an autorisierte Empfänger.",
    },
    en: {
      greeting: "Dear all,",
      intro: "the WINDI Sovereign System has completed the latest governance cycle.",
      status: "System Status",
      chain: "Audit Chain",
      pending: "Pending Item",
      alert: "Alert Level",
      summary: "Executive Summary",
      compliance: "Compliance",
      pdf: "The full signed forensic report is attached as a PDF.",
      noPdf: "PDF report will be available in the next cycle.",
      footer: "AI processes. You decide. WINDI guarantees.",
      warn: "Governance-sensitive information. Distribution restricted to authorized recipients.",
    },
  };
  const L = labels[lang];

  const text = `
${L.greeting}

${L.intro}

${L.status}: ${system}
${L.alert}: ${level}
${L.chain}: Ledger ${data.ledgerRef || "—"} | Hash ${data.hash || "—"}
${L.pending}: ${decision}
${compliance ? `${L.compliance}: ${compliance}` : ""}

${L.summary}:
${summary}

War Room: ${WAR_ROOM_URL}

---
${L.warn}
${L.footer}
`.trim();

  // ── HTML ──
  const alertColor = level === "CRITICAL" ? "#ef4444" : level === "HIGH" ? "#f59e0b" : "#22c55e";

  const html = `
<!DOCTYPE html>
<html lang="${lang}">
<head><meta charset="utf-8"/></head>
<body style="margin:0; padding:0; background:#f8f7f4;">
<div style="max-width:640px; margin:24px auto; font-family:'IBM Plex Mono','Courier New',monospace; border:2px solid #1a1814; background:#fff;">

  <!-- Header -->
  <div style="background:#1a1814; padding:20px 24px; display:flex; justify-content:space-between; align-items:center;">
    <div>
      <div style="letter-spacing:3px; font-weight:700; color:#c9a84c; font-size:18px;">WINDI</div>
      <div style="color:#a09888; font-size:11px; margin-top:2px;">SOVEREIGN GOVERNANCE REPORT</div>
    </div>
    <div style="background:${alertColor}; color:#fff; padding:6px 12px; border-radius:3px; font-size:11px; font-weight:700;">
      ${escapeHtml(level)}
    </div>
  </div>

  <!-- Meta Bar -->
  <div style="background:#f3f0ea; padding:12px 24px; font-size:11px; color:#6b6458; border-bottom:1px solid #e0dbd2;">
    <strong>${escapeHtml(data.briefingDate || "—")}</strong> &mdash; ${escapeHtml(data.genTime || "—")}
    &nbsp;&bull;&nbsp; Report: ${escapeHtml(data.reportId || "—")}
    &nbsp;&bull;&nbsp; Continuity: Day ${escapeHtml(String(data.contDays ?? "—"))}
  </div>

  <!-- Body -->
  <div style="padding:24px; font-size:13px; line-height:1.7; color:#1a1814;">

    <table style="width:100%; border-collapse:collapse; margin-bottom:16px;">
      <tr>
        <td style="padding:6px 0; font-size:12px; color:#6b6458; width:140px;">${lang === "de" ? "Ledger-Referenz" : "Ledger Reference"}</td>
        <td style="padding:6px 0; font-size:12px; font-weight:600;">${escapeHtml(data.ledgerRef || "—")}</td>
      </tr>
      <tr>
        <td style="padding:6px 0; font-size:12px; color:#6b6458;">Master Hash</td>
        <td style="padding:6px 0; font-size:12px; font-family:monospace;">${escapeHtml(data.hash || "—")}</td>
      </tr>
      <tr>
        <td style="padding:6px 0; font-size:12px; color:#6b6458;">${lang === "de" ? "Kritischer Punkt" : "Critical Item"}</td>
        <td style="padding:6px 0; font-size:12px; font-weight:600; color:${alertColor};">${escapeHtml(decision)}</td>
      </tr>
    </table>

    <div style="background:#fafaf8; border-left:3px solid #c9a84c; padding:14px 16px; margin-bottom:18px;">
      <div style="font-size:11px; color:#6b6458; margin-bottom:6px; text-transform:uppercase; letter-spacing:1px;">
        ${lang === "de" ? "Kurzfassung" : "Executive Summary"}
      </div>
      <div style="font-size:12px; line-height:1.6;">${escapeHtml(summary)}</div>
    </div>

    ${compliance ? `
    <div style="margin-bottom:18px; font-size:11px; color:#6b6458;">
      <strong>Compliance:</strong>&nbsp; ${escapeHtml(compliance)}
    </div>` : ""}

    <div style="text-align:center; margin:24px 0;">
      <a href="${WAR_ROOM_URL}"
         style="display:inline-block; background:#1a1814; color:#c9a84c; padding:12px 28px; border-radius:4px; text-decoration:none; font-weight:700; font-size:13px; letter-spacing:1px;">
        ${lang === "de" ? "🐉 WAR ROOM ÖFFNEN" : "🐉 OPEN WAR ROOM"}
      </a>
    </div>
  </div>

  <!-- Footer -->
  <div style="background:#1a1814; padding:16px 24px; font-size:10px; color:#6b6458; text-align:center; line-height:1.6;">
    ${escapeHtml(L.warn)}<br/>
    <span style="color:#c9a84c; font-weight:600;">${escapeHtml(L.footer)}</span>
  </div>

</div>
</body>
</html>`.trim();

  return { html, text };
}

// ─── Data Fetchers ───────────────────────────────────────────────
async function fetchBriefing() {
  const resp = await axios.get(BRIEFING_URL, { timeout: 8000 });
  if (!resp.data?.success) throw new Error("[DISPATCHER] Briefing API returned success=false");
  return resp.data.data;
}

async function fetchPdfAttachment() {
  try {
    const resp = await axios.post(
      PDF_URL,
      { type: "daily", lang: pickLang(), mode: "meeting" },
      { timeout: 15000 }
    );
    if (!resp.data?.success || !resp.data?.pdfBase64) return null;
    return {
      filename: resp.data.filename || `WINDI_Report_${new Date().toISOString().slice(0, 10)}.pdf`,
      content: resp.data.pdfBase64,
      encoding: "base64",
    };
  } catch {
    return null; // PDF not available yet — still send email
  }
}

// ─── SMTP Transport ──────────────────────────────────────────────
function createTransport() {
  return nodemailer.createTransport({
    host: process.env.SMTP_HOST,
    port: Number(process.env.SMTP_PORT || 465),
    secure: String(process.env.SMTP_SECURE || "true") === "true",
    auth: {
      user: process.env.SMTP_USER,
      pass: process.env.SMTP_PASS,
    },
  });
}

// ─── Forensic Ledger Log ─────────────────────────────────────────
async function logToLedger(data, recipient, messageId, hadPdf) {
  try {
    const dispatchHash = crypto
      .createHash("sha256")
      .update(`${data.reportId}|${recipient}|${messageId}|${Date.now()}`)
      .digest("hex")
      .slice(0, 16);

    await axios.post(LEDGER_URL + "/dispatch", {
      type: "DISPATCH",
      reportId: data.reportId,
      recipient: recipient,
      messageId: messageId,
      briefingHash: data.hash,
      dispatchHash: dispatchHash,
      hadPdfAttachment: hadPdf,
      timestamp: new Date().toISOString(),
    }, { timeout: 5000 });

    console.log(`[DISPATCHER] Ledger logged: ${dispatchHash}`);
  } catch (err) {
    // Ledger failure must NOT block dispatch — log warning only
    console.warn(`[DISPATCHER] Ledger log failed (non-blocking): ${err.message}`);
  }
}

// ─── Main Dispatch Function ──────────────────────────────────────
async function dispatchGovernanceBriefing(recipientEmail) {
  const startTime = Date.now();
  console.log(`[DISPATCHER] Starting dispatch to: ${recipientEmail}`);

  // 1. Security gate
  assertAllowedRecipient(recipientEmail);

  // 2. Fetch live data
  const data = await fetchBriefing();
  console.log(`[DISPATCHER] Briefing fetched: ${data.reportId} (${data.briefingDate})`);

  // 3. Build email
  const subject = buildSubject(data);
  const { html, text } = buildEmailBody(data);

  // 4. Fetch PDF (optional, non-blocking)
  const attachment = await fetchPdfAttachment();
  console.log(`[DISPATCHER] PDF attachment: ${attachment ? "YES" : "NOT AVAILABLE"}`);

  // 5. Send
  const transporter = createTransport();
  const mailOptions = {
    from: FROM,
    to: recipientEmail,
    subject,
    text,
    html,
    headers: {
      "X-WINDI-Report-ID": data.reportId || "—",
      "X-WINDI-Hash": data.hash || "—",
      "X-WINDI-Ledger-Ref": data.ledgerRef || "—",
      "X-WINDI-Alert-Level": computeAlertLevel(data).level,
    },
    attachments: attachment ? [attachment] : [],
  };

  const info = await transporter.sendMail(mailOptions);
  const elapsed = Date.now() - startTime;

  console.log(`[DISPATCHER] SENT to ${recipientEmail} in ${elapsed}ms — messageId: ${info.messageId}`);

  // 6. Log to Forensic Ledger (non-blocking)
  await logToLedger(data, recipientEmail, info.messageId, Boolean(attachment));

  return {
    success: true,
    messageId: info.messageId,
    subject,
    recipient: recipientEmail,
    reportId: data.reportId,
    alertLevel: computeAlertLevel(data).level,
    hadPdfAttachment: Boolean(attachment),
    elapsedMs: elapsed,
  };
}

module.exports = { dispatchGovernanceBriefing, fetchBriefing, computeAlertLevel };
