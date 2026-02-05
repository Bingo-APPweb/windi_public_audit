/**
 * WINDI PDF Virtue Receipt Engine v1.0
 * =====================================
 * "What is not in a signed document does not exist."
 *
 * Generates a forensic-grade A4 PDF from the live /api/briefing payload.
 * Every page carries the Master Hash and Ledger Reference in the footer.
 *
 * The PDF transforms an email notification into an Administrative Act.
 *
 * Three Dragons Protocol: Guardian builds, Witness certifies, Architect designs.
 */

const PDFDocument = require("pdfkit");
const axios = require("axios");
const crypto = require("crypto");
const path = require("path");
const fs = require("fs");

const BRIEFING_URL = process.env.WINDI_BRIEFING_URL || "http://127.0.0.1:8090/api/briefing";

// ─── Color Palette (WINDI Sovereign) ────────────────────────────
const C = {
  black: "#0f172a",
  darkGray: "#1e293b",
  midGray: "#475569",
  lightGray: "#94a3b8",
  paleGray: "#e2e8f0",
  warmBg: "#fafaf8",
  gold: "#c9a84c",
  goldDark: "#a07c2e",
  red: "#dc2626",
  redLight: "#fef2f2",
  redBorder: "#f87171",
  green: "#16a34a",
  greenLight: "#f0fdf4",
  yellow: "#ca8a04",
  yellowLight: "#fefce8",
  white: "#ffffff",
};

// ─── Risk Level Colors ──────────────────────────────────────────
const RISK_COLORS = {
  R0: C.green, R1: "#65a30d", R2: C.yellow,
  R3: "#ea580c", R4: C.red, R5: "#991b1b",
};

// ─── Compliance Labels ──────────────────────────────────────────
const COMPLIANCE_MAP = {
  euAiAct: "EU AI Act",
  bsiC5: "BSI C5",
  iso27001: "ISO 27001",
  gdpr: "GDPR",
};

// ─── Metric Labels ──────────────────────────────────────────────
const METRIC_MAP = {
  docsProcessed: { de: "Dokumente verarbeitet", en: "Documents Processed" },
  sgeAvg: { de: "SGE Durchschnitt", en: "SGE Average Score" },
  complianceRate: { de: "Compliance-Rate", en: "Compliance Rate" },
  avgResponse: { de: "Ø Reaktionszeit", en: "Avg Response Time" },
  overrides: { de: "Menschliche Übersteuerungen", en: "Human Overrides" },
  flagged: { de: "Markierte Einträge", en: "Flagged Items" },
};

// ─── Font Registration Helper ───────────────────────────────────
function registerFonts(doc) {
  // pdfkit ships with Helvetica, Courier, Times — use Courier for monospace feel
  // If IBM Plex Mono is available on the system, register it
  const fontPaths = [
    "/usr/share/fonts/truetype/ibm-plex/IBMPlexMono-Regular.ttf",
    "/usr/share/fonts/truetype/ibm-plex/IBMPlexMono-Bold.ttf",
  ];

  const hasIBM = fontPaths.every((p) => {
    try { return fs.existsSync(p); } catch { return false; }
  });

  if (hasIBM) {
    doc.registerFont("Mono", fontPaths[0]);
    doc.registerFont("MonoBold", fontPaths[1]);
    return { body: "Mono", bold: "MonoBold", mono: "Mono" };
  }

  // Fallback to built-in fonts
  return { body: "Helvetica", bold: "Helvetica-Bold", mono: "Courier" };
}

// ─── Drawing Helpers ────────────────────────────────────────────
function drawLine(doc, y, opts = {}) {
  const { color = C.paleGray, width = 0.5, margin = 50 } = opts;
  doc.strokeColor(color).lineWidth(width)
    .moveTo(margin, y).lineTo(doc.page.width - margin, y).stroke();
}

function drawRect(doc, x, y, w, h, opts = {}) {
  const { fill, stroke, radius = 0 } = opts;
  if (radius > 0) {
    doc.roundedRect(x, y, w, h, radius);
  } else {
    doc.rect(x, y, w, h);
  }
  if (fill && stroke) {
    doc.fillAndStroke(fill, stroke);
  } else if (fill) {
    doc.fill(fill);
  } else if (stroke) {
    doc.strokeColor(stroke).stroke();
  }
}

function checkPageSpace(doc, needed, fonts) {
  const bottomLimit = doc.page.height - 100; // leave space for footer
  if (doc.y + needed > bottomLimit) {
    doc.addPage();
    drawPageFooter(doc, doc._windiMeta, fonts);
    doc.y = 60;
  }
}

// ─── Page Footer (on EVERY page) ────────────────────────────────
function drawPageFooter(doc, meta, fonts) {
  const y = doc.page.height - 45;
  const pageW = doc.page.width;
  const margin = 50;

  drawLine(doc, y - 8, { color: C.gold, width: 1 });

  doc.font(fonts.mono).fontSize(7).fillColor(C.midGray);
  doc.text(
    `WINDI Virtue Receipt  |  Hash: ${meta.hash}  |  Ledger: ${meta.ledgerRef}  |  Report: ${meta.reportId}`,
    margin, y, { width: pageW - margin * 2, align: "center" }
  );
  doc.text(
    "This document is part of the continuous governance evidence chain. AI processes. Human decides. WINDI guarantees.",
    margin, y + 10, { width: pageW - margin * 2, align: "center" }
  );
}

// ─── Header Section ─────────────────────────────────────────────
function drawHeader(doc, data, fonts, lang) {
  const pageW = doc.page.width;
  const margin = 50;
  const contentW = pageW - margin * 2;

  // Gold top bar
  drawRect(doc, 0, 0, pageW, 4, { fill: C.gold });

  // Dark header band
  drawRect(doc, margin, 30, contentW, 70, { fill: C.black, radius: 4 });

  // WINDI title
  doc.font(fonts.bold).fontSize(20).fillColor(C.gold);
  doc.text("WINDI", margin + 20, 42);

  doc.font(fonts.body).fontSize(9).fillColor(C.lightGray);
  doc.text("SOVEREIGN GOVERNANCE REPORT", margin + 20, 66);

  // Status badge (right side)
  const status = (data.systemStatus || "operational").toUpperCase();
  const badgeColor = status === "OPERATIONAL" ? C.green : C.red;
  const badgeW = 100;
  const badgeX = pageW - margin - badgeW - 15;
  drawRect(doc, badgeX, 47, badgeW, 22, { fill: badgeColor, radius: 3 });
  doc.font(fonts.bold).fontSize(8).fillColor(C.white);
  doc.text(status, badgeX, 53, { width: badgeW, align: "center" });

  // Sub-header info line
  doc.y = 115;
  doc.font(fonts.mono).fontSize(8.5).fillColor(C.midGray);

  const dateStr = data.briefingDate || "—";
  const timeStr = data.genTime || "—";
  const reportStr = data.reportId || "—";
  const contStr = String(data.contDays ?? "—");

  doc.text(
    `${dateStr}  ·  ${timeStr}  ·  Report: ${reportStr}  ·  Continuity: Day ${contStr}`,
    margin, doc.y, { width: contentW, align: "center" }
  );

  doc.y += 20;
  drawLine(doc, doc.y, { color: C.paleGray });
  doc.y += 12;
}

// ─── Integrity Block ────────────────────────────────────────────
function drawIntegrityBlock(doc, data, fonts, lang) {
  const margin = 50;
  const contentW = doc.page.width - margin * 2;

  checkPageSpace(doc, 90, fonts);

  const blockY = doc.y;
  drawRect(doc, margin, blockY, contentW, 72, { fill: "#f8f7f4", stroke: C.gold, radius: 4 });

  // Gold left accent
  drawRect(doc, margin, blockY, 4, 72, { fill: C.gold });

  doc.font(fonts.bold).fontSize(8).fillColor(C.goldDark);
  doc.text(lang === "de" ? "INTEGRITÄTSBLOCK" : "INTEGRITY BLOCK", margin + 16, blockY + 10);

  doc.font(fonts.mono).fontSize(9).fillColor(C.black);
  const col1X = margin + 16;
  const col2X = margin + 140;
  let rowY = blockY + 26;

  const rows = [
    [lang === "de" ? "Master Hash:" : "Master Hash:", data.hash || "—"],
    [lang === "de" ? "Ledger-Referenz:" : "Ledger Reference:", data.ledgerRef || "—"],
    [lang === "de" ? "Kontinuitätstage:" : "Continuity Days:", String(data.contDays ?? "—")],
  ];

  rows.forEach(([label, value]) => {
    doc.font(fonts.body).fontSize(8).fillColor(C.midGray).text(label, col1X, rowY);
    doc.font(fonts.mono).fontSize(9).fillColor(C.black).text(value, col2X, rowY);
    rowY += 14;
  });

  doc.y = blockY + 84;
}

// ─── Critical Decision Block ────────────────────────────────────
function drawCriticalDecisions(doc, data, fonts, lang) {
  const margin = 50;
  const contentW = doc.page.width - margin * 2;
  const decisions = data.decisions || [];

  if (!decisions.length) return;

  const hasHigh = decisions.some((d) => d.urgency === "high" && d.status === "pending");

  checkPageSpace(doc, 40 + decisions.length * 80, fonts);

  // Section title
  doc.font(fonts.bold).fontSize(10).fillColor(hasHigh ? C.red : C.black);
  doc.text(
    hasHigh
      ? (lang === "de" ? "⚠  KRITISCHE GOVERNANCE-PUNKTE" : "⚠  CRITICAL GOVERNANCE ITEMS")
      : (lang === "de" ? "OFFENE ENTSCHEIDUNGEN" : "PENDING DECISIONS"),
    margin, doc.y
  );
  doc.y += 8;

  decisions.forEach((d) => {
    checkPageSpace(doc, 80, fonts);

    const isHigh = d.urgency === "high";
    const blockY = doc.y;
    const riskColor = RISK_COLORS[d.sge] || C.midGray;

    // Card background
    drawRect(doc, margin, blockY, contentW, 68, {
      fill: isHigh ? C.redLight : C.warmBg,
      stroke: isHigh ? C.redBorder : C.paleGray,
      radius: 4,
    });

    // Risk severity left bar
    drawRect(doc, margin, blockY, 5, 68, { fill: riskColor, radius: 2 });

    // Topic
    const topic = d.topic?.[lang] || d.topic?.en || "—";
    doc.font(fonts.bold).fontSize(11).fillColor(C.black);
    doc.text(topic, margin + 16, blockY + 10, { width: contentW - 140 });

    // Badges (right side)
    const badgeY = blockY + 10;
    const badgeX = doc.page.width - margin - 90;

    // SGE badge
    drawRect(doc, badgeX, badgeY, 36, 18, { fill: riskColor, radius: 3 });
    doc.font(fonts.bold).fontSize(9).fillColor(C.white);
    doc.text(d.sge || "—", badgeX, badgeY + 4, { width: 36, align: "center" });

    // Urgency badge
    const urgColor = isHigh ? C.red : "#2563eb";
    drawRect(doc, badgeX + 40, badgeY, 45, 18, { fill: urgColor, radius: 3 });
    doc.font(fonts.bold).fontSize(7).fillColor(C.white);
    doc.text((d.urgency || "—").toUpperCase(), badgeX + 40, badgeY + 5, { width: 45, align: "center" });

    // Status line
    doc.font(fonts.mono).fontSize(8).fillColor(C.midGray);
    doc.text(
      `ID: ${d.id}  ·  Status: ${(d.status || "—").toUpperCase()}`,
      margin + 16, blockY + 38
    );

    // Risk gravity bar
    const barY = blockY + 54;
    const barW = contentW - 32;
    const riskIdx = parseInt(d.sge?.replace("R", "") || "0");
    const fillPct = Math.min(((riskIdx + 1) / 6) * 100, 100);

    drawRect(doc, margin + 16, barY, barW, 5, { fill: "#e2e8f0", radius: 2 });
    drawRect(doc, margin + 16, barY, barW * (fillPct / 100), 5, { fill: riskColor, radius: 2 });

    doc.y = blockY + 76;
  });
}

// ─── Executive Summary ──────────────────────────────────────────
function drawSummary(doc, data, fonts, lang) {
  const margin = 50;
  const contentW = doc.page.width - margin * 2;
  const summary = data.summary?.[lang] || data.summary?.en || "";

  if (!summary) return;

  checkPageSpace(doc, 80, fonts);

  doc.font(fonts.bold).fontSize(10).fillColor(C.black);
  doc.text(lang === "de" ? "KURZFASSUNG" : "EXECUTIVE SUMMARY", margin, doc.y);
  doc.y += 8;

  const blockY = doc.y;
  // Measure text height first
  const textHeight = doc.heightOfString(summary, {
    width: contentW - 32,
    fontSize: 9,
  });
  const boxHeight = textHeight + 24;

  drawRect(doc, margin, blockY, contentW, boxHeight, { fill: "#f8f7f4", radius: 4 });
  drawRect(doc, margin, blockY, 3, boxHeight, { fill: C.gold });

  doc.font(fonts.body).fontSize(9).fillColor(C.darkGray);
  doc.text(summary, margin + 16, blockY + 12, { width: contentW - 32, lineGap: 3 });

  doc.y = blockY + boxHeight + 12;
}

// ─── Metrics Table ──────────────────────────────────────────────
function drawMetrics(doc, data, fonts, lang) {
  const margin = 50;
  const contentW = doc.page.width - margin * 2;
  const metrics = data.metrics || [];

  if (!metrics.length) return;

  checkPageSpace(doc, 40 + metrics.length * 22, fonts);

  doc.font(fonts.bold).fontSize(10).fillColor(C.black);
  doc.text(lang === "de" ? "SCHLÜSSELMETRIKEN" : "KEY METRICS", margin, doc.y);
  doc.y += 10;

  // Table header
  const colX = [margin, margin + 220, margin + 340, margin + 420];
  const headerY = doc.y;

  drawRect(doc, margin, headerY, contentW, 18, { fill: C.black, radius: 2 });
  doc.font(fonts.bold).fontSize(7).fillColor(C.white);
  doc.text(lang === "de" ? "METRIK" : "METRIC", colX[0] + 10, headerY + 5);
  doc.text(lang === "de" ? "WERT" : "VALUE", colX[1], headerY + 5);
  doc.text("TARGET", colX[2], headerY + 5);
  doc.text("STATUS", colX[3], headerY + 5);

  doc.y = headerY + 22;

  metrics.forEach((m, i) => {
    const rowY = doc.y;
    const labels = METRIC_MAP[m.k] || { de: m.k, en: m.k };
    const isGood = m.inv ? m.v === 0 : m.v >= (m.p || 0);
    const statusColor = isGood ? C.green : C.yellow;
    const statusText = isGood ? "OK" : "REVIEW";

    // Alternate row bg
    if (i % 2 === 0) {
      drawRect(doc, margin, rowY, contentW, 18, { fill: "#f8fafc" });
    }

    doc.font(fonts.body).fontSize(8).fillColor(C.darkGray);
    doc.text(labels[lang] || labels.en, colX[0] + 10, rowY + 5, { width: 200 });

    doc.font(fonts.mono).fontSize(9).fillColor(C.black);
    doc.text(`${m.v}${m.u}`, colX[1], rowY + 5);

    doc.font(fonts.mono).fontSize(8).fillColor(C.midGray);
    doc.text(m.p > 0 ? `${m.p}${m.u}` : "—", colX[2], rowY + 5);

    // Status dot
    doc.circle(colX[3] + 4, rowY + 11, 4).fill(statusColor);
    doc.font(fonts.bold).fontSize(7).fillColor(statusColor);
    doc.text(statusText, colX[3] + 14, rowY + 6);

    doc.y = rowY + 20;
  });

  doc.y += 8;
}

// ─── Compliance Snapshot ────────────────────────────────────────
function drawCompliance(doc, data, fonts, lang) {
  const margin = 50;
  const contentW = doc.page.width - margin * 2;
  const compliance = data.compliance || [];

  if (!compliance.length) return;

  checkPageSpace(doc, 60, fonts);

  doc.font(fonts.bold).fontSize(10).fillColor(C.black);
  doc.text("COMPLIANCE STATUS", margin, doc.y);
  doc.y += 10;

  const badgeW = (contentW - 30) / compliance.length;
  const startX = margin;
  const badgeY = doc.y;

  compliance.forEach((c, i) => {
    const x = startX + i * (badgeW + 10);
    const label = COMPLIANCE_MAP[c.k] || c.k.toUpperCase();
    const isOk = c.s === "compliant";
    const isPartial = c.s === "partial";

    const bgColor = isOk ? C.greenLight : isPartial ? C.yellowLight : C.redLight;
    const textColor = isOk ? C.green : isPartial ? C.yellow : C.red;
    const statusLabel = isOk
      ? (lang === "de" ? "KONFORM" : "COMPLIANT")
      : isPartial
        ? (lang === "de" ? "TEILWEISE" : "PARTIAL")
        : (lang === "de" ? "FEHLEND" : "FAIL");

    drawRect(doc, x, badgeY, badgeW, 40, { fill: bgColor, stroke: textColor, radius: 4 });

    doc.font(fonts.bold).fontSize(8).fillColor(C.black);
    doc.text(label, x, badgeY + 8, { width: badgeW, align: "center" });

    doc.font(fonts.bold).fontSize(7).fillColor(textColor);
    doc.text(statusLabel, x, badgeY + 24, { width: badgeW, align: "center" });
  });

  doc.y = badgeY + 52;
}

// ─── ISP Profiles Section ───────────────────────────────────────
function drawProfiles(doc, data, fonts, lang) {
  const margin = 50;
  const contentW = doc.page.width - margin * 2;
  const loaded = data._meta?.engine?.profiles_loaded || [];
  const available = data._meta?.engine?.profiles_available || [];

  if (!available.length) return;

  checkPageSpace(doc, 60, fonts);

  doc.font(fonts.bold).fontSize(10).fillColor(C.black);
  doc.text("ISP PROFILES", margin, doc.y);
  doc.y += 8;

  doc.font(fonts.body).fontSize(8).fillColor(C.midGray);
  doc.text(
    `${loaded.length} ${lang === "de" ? "aktiv" : "active"} / ${available.length} ${lang === "de" ? "verfügbar" : "available"}`,
    margin, doc.y
  );
  doc.y += 12;

  // Profile badges in a flowing row
  let curX = margin;
  const maxX = doc.page.width - margin;
  const badgeH = 20;

  available.forEach((p) => {
    const isLoaded = loaded.includes(p);
    const displayName = p.replace(/_/g, " ").replace(/-/g, " ").toUpperCase();
    const textW = doc.widthOfString(displayName, { fontSize: 7 }) + 20;

    if (curX + textW > maxX) {
      curX = margin;
      doc.y += badgeH + 6;
    }

    checkPageSpace(doc, badgeH + 10, fonts);

    drawRect(doc, curX, doc.y, textW, badgeH, {
      fill: isLoaded ? C.black : "#f1f5f9",
      stroke: isLoaded ? C.gold : C.paleGray,
      radius: 3,
    });

    doc.font(fonts.bold).fontSize(7).fillColor(isLoaded ? C.gold : C.lightGray);
    doc.text(displayName, curX, doc.y + 6, { width: textW, align: "center" });

    curX += textW + 8;
  });

  doc.y += badgeH + 16;
}

// ─── Risk Summary Bar ───────────────────────────────────────────
function drawRiskSummary(doc, data, fonts, lang) {
  const margin = 50;
  const contentW = doc.page.width - margin * 2;
  const risks = data.risks || {};

  checkPageSpace(doc, 50, fonts);

  const boxW = (contentW - 20) / 3;
  const boxH = 36;
  const y = doc.y;

  const items = [
    { label: lang === "de" ? "AKTIV" : "ACTIVE", value: risks.active || 0, color: C.yellow },
    { label: lang === "de" ? "NEU" : "NEW", value: risks.new || 0, color: "#3b82f6" },
    { label: lang === "de" ? "GELÖST" : "RESOLVED", value: risks.resolved || 0, color: C.green },
  ];

  items.forEach((item, i) => {
    const x = margin + i * (boxW + 10);
    drawRect(doc, x, y, boxW, boxH, { fill: "#f8fafc", stroke: C.paleGray, radius: 4 });

    doc.font(fonts.bold).fontSize(18).fillColor(item.color);
    doc.text(String(item.value), x, y + 4, { width: boxW, align: "center" });

    doc.font(fonts.bold).fontSize(7).fillColor(C.midGray);
    doc.text(item.label, x, y + 24, { width: boxW, align: "center" });
  });

  doc.y = y + boxH + 12;
}

// ─── Signature Block ────────────────────────────────────────────
function drawSignatureBlock(doc, data, fonts, lang) {
  const margin = 50;
  const contentW = doc.page.width - margin * 2;

  checkPageSpace(doc, 100, fonts);

  drawLine(doc, doc.y, { color: C.gold, width: 1 });
  doc.y += 16;

  // PDF hash (of this document generation)
  const pdfHash = crypto
    .createHash("sha256")
    .update(`${data.reportId}|${data.hash}|${data.ledgerRef}|${new Date().toISOString()}`)
    .digest("hex")
    .slice(0, 16);

  doc.font(fonts.bold).fontSize(9).fillColor(C.goldDark);
  doc.text(lang === "de" ? "DOKUMENTENZERTIFIZIERUNG" : "DOCUMENT CERTIFICATION", margin, doc.y);
  doc.y += 10;

  const certY = doc.y;
  drawRect(doc, margin, certY, contentW, 56, { fill: "#f8f7f4", stroke: C.gold, radius: 4 });

  doc.font(fonts.mono).fontSize(8).fillColor(C.darkGray);
  doc.text(`Document Hash:    ${pdfHash}`, margin + 12, certY + 10);
  doc.text(`Briefing Hash:    ${data.hash}`, margin + 12, certY + 22);
  doc.text(`Generated:        ${new Date().toISOString()}`, margin + 12, certY + 34);

  doc.y = certY + 68;

  // Motto
  doc.font(fonts.bold).fontSize(8).fillColor(C.gold);
  doc.text("AI processes. Human decides. WINDI guarantees.", margin, doc.y, {
    width: contentW,
    align: "center",
  });

  doc.y += 14;
  doc.font(fonts.body).fontSize(7).fillColor(C.lightGray);
  doc.text("Three Dragons Protocol — Guardian · Architect · Witness", margin, doc.y, {
    width: contentW,
    align: "center",
  });
}

// ═══════════════════════════════════════════════════════════════
// MAIN: Generate PDF Buffer
// ═══════════════════════════════════════════════════════════════
async function generateVirtueReceipt(briefingData, options = {}) {
  const lang = options.lang || (process.env.WINDI_LANG || "de").toLowerCase();
  const data = briefingData;

  return new Promise((resolve, reject) => {
    try {
      const doc = new PDFDocument({
        size: "A4",
        margins: { top: 50, bottom: 60, left: 50, right: 50 },
        info: {
          Title: `WINDI Governance Report — ${data.briefingDate || "Daily"}`,
          Author: "WINDI Sovereign System",
          Subject: `Governance Briefing ${data.reportId || ""}`,
          Creator: "WINDI PDF Virtue Receipt Engine v1.0",
          Keywords: "governance, audit, compliance, WINDI",
        },
        bufferPages: true,
      });

      // Store meta for footer access
      doc._windiMeta = {
        hash: data.hash || "—",
        ledgerRef: data.ledgerRef || "—",
        reportId: data.reportId || "—",
      };

      const fonts = registerFonts(doc);
      const buffers = [];

      doc.on("data", (chunk) => buffers.push(chunk));
      doc.on("end", () => {
        const pdfBuffer = Buffer.concat(buffers);
        resolve(pdfBuffer);
      });
      doc.on("error", reject);

      // ── Build Document ──
      drawHeader(doc, data, fonts, lang);
      drawIntegrityBlock(doc, data, fonts, lang);

      doc.y += 4;
      drawCriticalDecisions(doc, data, fonts, lang);

      doc.y += 4;
      drawSummary(doc, data, fonts, lang);

      doc.y += 4;
      drawMetrics(doc, data, fonts, lang);

      doc.y += 4;
      drawCompliance(doc, data, fonts, lang);

      doc.y += 4;
      drawRiskSummary(doc, data, fonts, lang);

      doc.y += 4;
      drawProfiles(doc, data, fonts, lang);

      doc.y += 8;
      drawSignatureBlock(doc, data, fonts, lang);

      // ── Add footers to ALL pages ──
      const pageCount = doc.bufferedPageRange().count;
      for (let i = 0; i < pageCount; i++) {
        doc.switchToPage(i);
        drawPageFooter(doc, doc._windiMeta, fonts);
      }

      doc.end();
    } catch (err) {
      reject(err);
    }
  });
}

// ═══════════════════════════════════════════════════════════════
// EXPRESS ROUTE
// ═══════════════════════════════════════════════════════════════
const express = require("express");
const router = express.Router();

// POST /api/report/pdf
// Body (optional): { lang: "de"|"en", mode: "meeting"|"full", type: "daily" }
router.post("/report/pdf", async (req, res) => {
  try {
    const { lang, mode, type } = req.body || {};

    // Fetch live briefing
    const response = await axios.get(BRIEFING_URL, { timeout: 8000 });
    if (!response.data?.success) {
      return res.status(502).json({ success: false, error: "Briefing API returned success=false" });
    }

    const briefingData = response.data.data;
    const pdfBuffer = await generateVirtueReceipt(briefingData, { lang: lang || undefined });

    const filename = `WINDI_Daily_Report_${(briefingData.briefingDate || "unknown").replace(/\./g, "-")}.pdf`;

    res.json({
      success: true,
      filename,
      pdfBase64: pdfBuffer.toString("base64"),
      meta: {
        hash: briefingData.hash,
        ledgerRef: briefingData.ledgerRef,
        reportId: briefingData.reportId,
        pages: 1,
        sizeBytes: pdfBuffer.length,
        generatedAt: new Date().toISOString(),
      },
    });
  } catch (err) {
    console.error("[PDF ENGINE] Error:", err.message);
    res.status(500).json({ success: false, error: `PDF generation failed: ${err.message}` });
  }
});

// GET /api/report/pdf/download — Direct PDF download (for browser)
router.get("/report/pdf/download", async (req, res) => {
  try {
    const lang = req.query.lang || undefined;

    const response = await axios.get(BRIEFING_URL, { timeout: 8000 });
    if (!response.data?.success) {
      return res.status(502).send("Briefing API unavailable");
    }

    const briefingData = response.data.data;
    const pdfBuffer = await generateVirtueReceipt(briefingData, { lang });
    const filename = `WINDI_Daily_Report_${(briefingData.briefingDate || "unknown").replace(/\./g, "-")}.pdf`;

    res.set({
      "Content-Type": "application/pdf",
      "Content-Disposition": `attachment; filename="${filename}"`,
      "Content-Length": pdfBuffer.length,
      "X-WINDI-Hash": (briefingData.hash || "").replace(/[^\x20-\x7E]/g, "."),
      "X-WINDI-Ledger-Ref": briefingData.ledgerRef || "",
    });
    res.send(pdfBuffer);
  } catch (err) {
    console.error("[PDF ENGINE] Download error:", err.message);
    res.status(500).send("PDF generation failed");
  }
});

module.exports = router;
module.exports.generateVirtueReceipt = generateVirtueReceipt;
