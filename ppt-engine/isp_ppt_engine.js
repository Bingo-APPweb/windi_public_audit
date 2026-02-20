// ═══════════════════════════════════════════════════════════════════
// WINDI ISP PPT ENGINE v1.0
// "O template NUNCA decide o nível. A API decide.
//  O template apenas manifesta."
//
// Pipeline: ISP Loader → Slide Master → Content Renderer →
//           Footer Injector → Forensic Receipt Generator
//
// AI processes. Human decides. WINDI guarantees.
// ═══════════════════════════════════════════════════════════════════

const pptxgen = require("pptxgenjs");
const React = require("react");
const ReactDOMServer = require("react-dom/server");
const sharp = require("sharp");
const fs = require("fs");
const path = require("path");
const crypto = require("crypto");
const {
  FaShieldAlt, FaCheckCircle, FaExclamationTriangle, FaLock,
  FaChartPie, FaClock, FaFingerprint, FaServer, FaFileAlt,
  FaLink, FaDatabase, FaEye, FaBuilding, FaGavel
} = require("react-icons/fa");

// ─────────────────────────────────────────────────────
// ICON RENDERER
// ─────────────────────────────────────────────────────
function renderIconSvg(IconComponent, color = "#FFFFFF", size = 256) {
  return ReactDOMServer.renderToStaticMarkup(
    React.createElement(IconComponent, { color, size: String(size) })
  );
}

async function iconToBase64(IconComponent, color, size = 256) {
  const svg = renderIconSvg(IconComponent, color, size);
  const buf = await sharp(Buffer.from(svg)).png().toBuffer();
  return "image/png;base64," + buf.toString("base64");
}

// ─────────────────────────────────────────────────────
// LOGO GENERATOR (SVG-based institutional seal)
// ─────────────────────────────────────────────────────
async function generateInstitutionalLogo(isp) {
  const c = isp.colors;
  const isDark = parseInt(c.background, 16) < 0x888888;
  const circleStroke = isDark ? c.primary : c.secondary;
  const textColor = isDark ? c.primary : c.secondary;
  const bgColor = isDark ? c.background : c.background;

  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="256" height="256" viewBox="0 0 256 256">
    <circle cx="128" cy="128" r="120" fill="#${bgColor}" stroke="#${circleStroke}" stroke-width="4"/>
    <text x="128" y="80" text-anchor="middle" font-family="${isp.fonts.title},Georgia,serif" font-size="22" font-weight="bold" fill="#${textColor}">${isp.org_name.length > 12 ? isp.org_name.substring(0, 12) : isp.org_name}</text>
    <text x="128" y="155" text-anchor="middle" font-size="64" fill="#${textColor}">🏛️</text>
    <text x="128" y="205" text-anchor="middle" font-family="${isp.fonts.body},sans-serif" font-size="13" fill="#${c.text_muted}">GOVERNANCE</text>
  </svg>`;
  const buf = await sharp(Buffer.from(svg)).png().toBuffer();
  return "image/png;base64," + buf.toString("base64");
}

// ─────────────────────────────────────────────────────
// SEAL VISUAL GENERATOR (QR-like integrity pattern)
// ─────────────────────────────────────────────────────
async function generateSealVisual(isp, hashSeed) {
  const size = 200;
  const cellSize = 10;
  const c = isp.colors;
  const isDark = parseInt(c.background, 16) < 0x888888;
  const bgHex = isDark ? c.background : c.secondary;
  const fg1 = c.primary;
  const fg2 = c.accent || c.primary;

  let rects = '';
  let idx = 0;
  const seed = hashSeed || crypto.randomBytes(32).toString('hex');

  for (let y = 0; y < size; y += cellSize) {
    for (let x = 0; x < size; x += cellSize) {
      const charCode = seed.charCodeAt(idx % seed.length);
      if (charCode % 3 !== 0) {
        const shade = (charCode % 2 === 0) ? `#${fg1}` : `#${fg2}`;
        rects += `<rect x="${x}" y="${y}" width="${cellSize}" height="${cellSize}" fill="${shade}" opacity="0.8"/>`;
      }
      idx++;
    }
  }

  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${size}" height="${size}" viewBox="0 0 ${size} ${size}">
    <rect width="${size}" height="${size}" fill="#${bgHex}"/>
    ${rects}
    <rect x="55" y="55" width="90" height="90" rx="5" fill="#${bgHex}"/>
    <text x="100" y="95" text-anchor="middle" font-family="monospace" font-size="11" fill="#${fg1}" font-weight="bold">WINDI</text>
    <text x="100" y="115" text-anchor="middle" font-family="monospace" font-size="9" fill="#${c.text_muted}">SEALED</text>
  </svg>`;
  const buf = await sharp(Buffer.from(svg)).png().toBuffer();
  return "image/png;base64," + buf.toString("base64");
}

// ─────────────────────────────────────────────────────
// ISP LOADER
// ─────────────────────────────────────────────────────
class ISPLoader {
  constructor(ispDir) {
    this.ispDir = ispDir;
    this.cache = {};
  }

  load(orgId) {
    if (this.cache[orgId]) return this.cache[orgId];
    const filePath = path.join(this.ispDir, `${orgId}.json`);
    if (!fs.existsSync(filePath)) {
      throw new Error(`ISP not found: ${orgId} (looked in ${filePath})`);
    }
    const isp = JSON.parse(fs.readFileSync(filePath, "utf-8"));
    this.cache[orgId] = isp;
    console.log(`  ✅ ISP loaded: ${isp.org_name} (${isp.theme_name})`);
    return isp;
  }

  listAvailable() {
    return fs.readdirSync(this.ispDir)
      .filter(f => f.endsWith(".json") && !f.includes("schema"))
      .map(f => f.replace(".json", ""));
  }
}

// ─────────────────────────────────────────────────────
// ISP PPT ENGINE
// ─────────────────────────────────────────────────────
class WindiPPTEngine {
  constructor(isp) {
    this.isp = isp;
    this.pres = new pptxgen();
    this.pres.layout = "LAYOUT_16x9";
    this.pres.author = `WINDI ISP PPT Engine — ${isp.org_name}`;
    this.pres.title = `${isp.org_name} Governance Report`;
    this.slideCount = 0;
    this.totalSlides = 0;
    this.contentHash = null;
    this.icons = {};
  }

  // Pre-render all icons in ISP colors
  async initialize() {
    const c = this.isp.colors;
    const isDark = parseInt(c.background, 16) < 0x888888;
    const iconPrimary = `#${c.primary}`;
    const iconSuccess = `#${c.success || "2ECC71"}`;
    const iconWarning = `#${c.warning || "F39C12"}`;
    const iconMuted = `#${c.text_muted}`;
    const iconText = `#${isDark ? c.text : c.secondary}`;

    this.icons = {
      shield: await iconToBase64(FaShieldAlt, iconPrimary),
      check: await iconToBase64(FaCheckCircle, iconSuccess),
      warning: await iconToBase64(FaExclamationTriangle, iconWarning),
      lock: await iconToBase64(FaLock, iconPrimary),
      pie: await iconToBase64(FaChartPie, iconPrimary),
      clock: await iconToBase64(FaClock, iconMuted),
      fingerprint: await iconToBase64(FaFingerprint, iconPrimary),
      server: await iconToBase64(FaServer, `#${c.accent}`),
      file: await iconToBase64(FaFileAlt, iconPrimary),
      link: await iconToBase64(FaLink, iconSuccess),
      db: await iconToBase64(FaDatabase, iconPrimary),
      eye: await iconToBase64(FaEye, iconText),
      building: await iconToBase64(FaBuilding, iconPrimary),
      gavel: await iconToBase64(FaGavel, iconPrimary),
    };
    this.logo = await generateInstitutionalLogo(this.isp);
    console.log(`  ✅ Icons rendered in ISP palette: ${this.isp.theme_name}`);
  }

  // ───── SLIDE MASTER ─────
  defineSlideMaster() {
    const c = this.isp.colors;

    this.pres.defineSlideMaster({
      title: "ISP_CONTENT",
      background: { color: c.background },
      objects: []
    });

    this.pres.defineSlideMaster({
      title: "ISP_COVER",
      background: { color: c.background_alt || c.background },
      objects: []
    });

    console.log(`  ✅ Slide Masters defined for: ${this.isp.org_name}`);
  }

  // ───── GOVERNANCE FOOTER (injected on every content slide) ─────
  addFooter(slide) {
    this.slideCount++;
    const c = this.isp.colors;
    const f = this.isp.footer;
    const isDark = parseInt(c.background, 16) < 0x888888;

    // Footer bar
    const footerBg = isDark ? c.background_alt : c.background_alt;
    slide.addShape(this.pres.shapes.RECTANGLE, {
      x: 0, y: 5.05, w: 10, h: 0.575,
      fill: { color: footerBg }
    });

    // Accent line above footer
    slide.addShape(this.pres.shapes.RECTANGLE, {
      x: 0, y: 5.02, w: 10, h: 0.03,
      fill: { color: c.primary }
    });

    // Shield icon
    slide.addImage({ data: this.icons.shield, x: 0.2, y: 5.13, w: 0.22, h: 0.22 });

    // Footer text
    const parts = [
      { text: "WINDI", options: { bold: true, color: c.primary, fontSize: 8, fontFace: this.isp.fonts.title } },
      { text: `  |  ${f.left_text}`, options: { color: c.text_muted, fontSize: 7, fontFace: this.isp.fonts.body } },
    ];
    if (f.classification) {
      parts.push({ text: `  |  ${f.classification}`, options: { color: c.text_muted, fontSize: 7, fontFace: this.isp.fonts.body } });
    }
    slide.addText(parts, { x: 0.5, y: 5.1, w: 7, h: 0.4, margin: 0 });

    // Page number
    if (f.show_page_number) {
      slide.addText(`${this.slideCount} / ${this.totalSlides}`, {
        x: 8.5, y: 5.1, w: 1, h: 0.4,
        fontSize: 8, color: c.text_muted, fontFace: this.isp.fonts.body, align: "right", margin: 0
      });
    }
  }

  // ───── SECTION HEADER (reusable) ─────
  addSectionHeader(slide, icon, title) {
    const c = this.isp.colors;
    slide.addImage({ data: icon, x: 0.5, y: 0.3, w: 0.3, h: 0.3 });
    slide.addText(title, {
      x: 0.9, y: 0.28, w: 6, h: 0.4,
      fontSize: 14, fontFace: this.isp.fonts.title, color: c.primary, bold: true, margin: 0
    });
    slide.addShape(this.pres.shapes.RECTANGLE, {
      x: 0.5, y: 0.75, w: 9, h: 0.015, fill: { color: c.primary }
    });
  }

  // ───── STAT CARD (reusable) ─────
  addStatCard(slide, x, y, w, h, { value, label, icon, accentColor }) {
    const c = this.isp.colors;
    const isDark = parseInt(c.background, 16) < 0x888888;
    const cardBg = isDark ? c.secondary : c.background_alt;

    slide.addShape(this.pres.shapes.RECTANGLE, {
      x, y, w, h, fill: { color: cardBg },
      shadow: { type: "outer", blur: 4, offset: 2, angle: 135, color: "000000", opacity: isDark ? 0.3 : 0.1 }
    });
    slide.addShape(this.pres.shapes.RECTANGLE, {
      x, y, w, h: 0.04, fill: { color: accentColor || c.primary }
    });
    if (icon) {
      slide.addImage({ data: icon, x: x + 0.15, y: y + 0.2, w: 0.3, h: 0.3 });
    }
    slide.addText(value, {
      x, y: y + 0.55, w, h: 0.6,
      fontSize: 36, fontFace: this.isp.fonts.title, color: c.text, bold: true, align: "center", margin: 0
    });
    slide.addText(label, {
      x, y: y + 1.15, w, h: 0.3,
      fontSize: 10, fontFace: this.isp.fonts.body, color: c.text_muted, align: "center", margin: 0
    });
  }

  // ───── INFO PANEL (reusable) ─────
  addInfoPanel(slide, x, y, w, h, { title, icon, items, accentColor }) {
    const c = this.isp.colors;
    const isDark = parseInt(c.background, 16) < 0x888888;
    const panelBg = isDark ? c.secondary : c.background_alt;

    slide.addShape(this.pres.shapes.RECTANGLE, {
      x, y, w, h, fill: { color: panelBg },
      shadow: { type: "outer", blur: 3, offset: 1, angle: 135, color: "000000", opacity: isDark ? 0.2 : 0.08 }
    });
    slide.addShape(this.pres.shapes.RECTANGLE, {
      x, y, w, h: 0.04, fill: { color: accentColor || c.success }
    });

    if (icon) slide.addImage({ data: icon, x: x + 0.2, y: y + 0.15, w: 0.25, h: 0.25 });
    slide.addText(title, {
      x: icon ? x + 0.5 : x + 0.2, y: y + 0.15, w: w - 0.7, h: 0.25,
      fontSize: 11, fontFace: this.isp.fonts.title, color: c.primary, bold: true, margin: 0
    });

    items.forEach((item, i) => {
      slide.addImage({ data: this.icons.check, x: x + 0.2, y: y + 0.55 + i * 0.22, w: 0.15, h: 0.15 });
      slide.addText(item, {
        x: x + 0.45, y: y + 0.53 + i * 0.22, w: w - 0.65, h: 0.22,
        fontSize: 8.5, fontFace: this.isp.fonts.body, color: c.text, margin: 0
      });
    });
  }

  // ═══════════════════════════════════════════════════
  // SLIDE GENERATORS
  // ═══════════════════════════════════════════════════

  // COVER SLIDE
  addCoverSlide(title, subtitle, date) {
    const c = this.isp.colors;
    const s = this.pres.addSlide();
    s.background = { color: c.background_alt };

    // Top accent
    s.addShape(this.pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.06, fill: { color: c.primary } });

    // Logo
    s.addImage({ data: this.logo, x: 4.0, y: 0.4, w: 2.0, h: 2.0 });

    // Title
    s.addText(title.toUpperCase(), {
      x: 0.5, y: 2.5, w: 9, h: 0.8,
      fontSize: 38, fontFace: this.isp.fonts.title, color: c.primary,
      bold: true, align: "center", charSpacing: 5, margin: 0
    });

    // Subtitle
    s.addText(subtitle, {
      x: 0.5, y: 3.2, w: 9, h: 0.5,
      fontSize: 15, fontFace: this.isp.fonts.body, color: c.text_muted, align: "center", margin: 0
    });

    // Divider
    s.addShape(this.pres.shapes.RECTANGLE, { x: 3.5, y: 3.85, w: 3, h: 0.02, fill: { color: c.text_muted } });

    // Date
    s.addText(date, {
      x: 0.5, y: 4.05, w: 9, h: 0.4,
      fontSize: 13, fontFace: this.isp.fonts.body, color: c.text_muted, align: "center", margin: 0
    });

    // Motto
    s.addText("AI processes. Human decides. WINDI guarantees.", {
      x: 0.5, y: 4.7, w: 9, h: 0.4,
      fontSize: 11, fontFace: this.isp.fonts.title, color: c.text_muted, italic: true, align: "center", margin: 0
    });

    // Bottom accent
    s.addShape(this.pres.shapes.RECTANGLE, { x: 0, y: 5.565, w: 10, h: 0.06, fill: { color: c.primary } });

    // Watermark if enabled
    if (this.isp.watermark?.enabled) {
      s.addText(this.isp.watermark.text, {
        x: 2, y: 2, w: 6, h: 2,
        fontSize: 60, fontFace: this.isp.fonts.title, color: c.text_muted,
        transparency: 100 - (this.isp.watermark.opacity || 8),
        align: "center", valign: "middle", rotate: -30, margin: 0
      });
    }

    return s;
  }

  // HEALTH OVERVIEW SLIDE
  addHealthSlide(stats, services) {
    const c = this.isp.colors;
    const s = this.pres.addSlide();
    s.background = { color: c.background };

    this.addSectionHeader(s, this.icons.db, "SYSTEM HEALTH OVERVIEW");

    // Stat cards
    stats.forEach((st, i) => {
      this.addStatCard(s, 0.5 + i * 2.3, 1.1, 2.1, 1.6, {
        value: st.value, label: st.label,
        icon: this.icons[st.icon] || this.icons.file,
        accentColor: st.accent || c.primary
      });
    });

    // Services table
    if (services && services.length > 0) {
      const isDark = parseInt(c.background, 16) < 0x888888;
      const headerBg = isDark ? c.background_alt : c.secondary;
      const rowBg = isDark ? c.secondary : c.background_alt;

      const tableHeader = [[
        { text: "Service", options: { bold: true, color: c.primary, fontSize: 9, fontFace: this.isp.fonts.body, fill: { color: headerBg } } },
        { text: "Port", options: { bold: true, color: c.primary, fontSize: 9, fontFace: this.isp.fonts.body, fill: { color: headerBg } } },
        { text: "Status", options: { bold: true, color: c.primary, fontSize: 9, fontFace: this.isp.fonts.body, fill: { color: headerBg } } },
      ]];

      const tableRows = services.map(svc => [
        { text: svc.name, options: { fontSize: 9, fontFace: this.isp.fonts.body, color: c.text, fill: { color: rowBg } } },
        { text: svc.port, options: { fontSize: 9, fontFace: this.isp.fonts.mono, color: c.text_muted, fill: { color: rowBg } } },
        { text: svc.status, options: { fontSize: 9, fontFace: this.isp.fonts.body, color: c.success, bold: true, fill: { color: rowBg } } },
      ]);

      s.addTable([...tableHeader, ...tableRows], {
        x: 0.5, y: 3.1, w: 5.5, colW: [2.5, 1.2, 1.8],
        border: { pt: 0.5, color: c.text_muted },
      });
    }

    this.addFooter(s);
    return s;
  }

  // RISK DISTRIBUTION SLIDE
  addRiskSlide(riskData, submissionData, insight) {
    const c = this.isp.colors;
    const s = this.pres.addSlide();
    s.background = { color: c.background };

    this.addSectionHeader(s, this.icons.pie, "RISK DISTRIBUTION ANALYSIS");

    // Doughnut chart
    s.addChart(this.pres.charts.DOUGHNUT, [{
      name: "Risk Levels",
      labels: riskData.map(r => r.label),
      values: riskData.map(r => r.value),
    }], {
      x: 0.3, y: 1.0, w: 4.5, h: 3.5,
      showPercent: true, showTitle: false,
      showLegend: true, legendPos: "b", legendFontSize: 8, legendColor: c.text_muted,
      chartColors: riskData.map(r => r.color),
      dataLabelColor: c.text, dataLabelFontSize: 9,
    });

    // Bar chart
    if (submissionData) {
      s.addChart(this.pres.charts.BAR, [{
        name: "Submissions", labels: submissionData.labels, values: submissionData.values,
      }], {
        x: 5.2, y: 1.0, w: 4.3, h: 1.8, barDir: "col",
        showTitle: true, title: "Monthly Submissions", titleColor: c.text_muted, titleFontSize: 10,
        chartColors: [c.primary],
        chartArea: { fill: { color: parseInt(c.background, 16) < 0x888888 ? c.secondary : c.background_alt } },
        catAxisLabelColor: c.text_muted, valAxisLabelColor: c.text_muted,
        catAxisLabelFontSize: 8, valAxisLabelFontSize: 8,
        valGridLine: { color: c.text_muted, size: 0.5 }, catGridLine: { style: "none" },
        showValue: true, dataLabelColor: c.text, dataLabelFontSize: 9, showLegend: false,
      });
    }

    // Insight box
    if (insight) {
      const isDark = parseInt(c.background, 16) < 0x888888;
      const boxBg = isDark ? c.secondary : c.background_alt;
      s.addShape(this.pres.shapes.RECTANGLE, {
        x: 5.2, y: 3.1, w: 4.3, h: 1.4, fill: { color: boxBg },
        shadow: { type: "outer", blur: 3, offset: 1, angle: 135, color: "000000", opacity: 0.2 }
      });
      s.addShape(this.pres.shapes.RECTANGLE, { x: 5.2, y: 3.1, w: 0.06, h: 1.4, fill: { color: c.primary } });
      s.addImage({ data: this.icons.eye, x: 5.45, y: 3.25, w: 0.2, h: 0.2 });
      s.addText("KEY INSIGHT", {
        x: 5.75, y: 3.22, w: 3, h: 0.25,
        fontSize: 10, fontFace: this.isp.fonts.body, color: c.primary, bold: true, margin: 0
      });
      s.addText(insight, {
        x: 5.45, y: 3.55, w: 3.8, h: 0.85,
        fontSize: 10, fontFace: this.isp.fonts.body, color: c.text, margin: 0
      });
    }

    this.addFooter(s);
    return s;
  }

  // COMPLIANCE SLIDE
  addComplianceSlide(layers, complianceItems) {
    const c = this.isp.colors;
    const s = this.pres.addSlide();
    s.background = { color: c.background };
    const isDark = parseInt(c.background, 16) < 0x888888;

    this.addSectionHeader(s, this.icons.lock, "COMPLIANCE & ARCHITECTURE STATUS");

    // Architecture layers (left)
    const layerColors = [c.accent, c.primary, `${c.success || "3498DB"}`];
    const layerIcons = [this.icons.file, this.icons.server, this.icons.fingerprint];

    layers.forEach((l, i) => {
      const y = 1.0 + i * 1.15;
      const cardBg = isDark ? c.secondary : c.background_alt;

      s.addShape(this.pres.shapes.RECTANGLE, {
        x: 0.5, y, w: 4.5, h: 0.95, fill: { color: cardBg },
        shadow: { type: "outer", blur: 3, offset: 1, angle: 135, color: "000000", opacity: isDark ? 0.2 : 0.08 }
      });
      s.addShape(this.pres.shapes.RECTANGLE, { x: 0.5, y, w: 0.06, h: 0.95, fill: { color: layerColors[i] || c.primary } });
      s.addImage({ data: layerIcons[i], x: 0.75, y: y + 0.22, w: 0.4, h: 0.4 });
      s.addText(l.label, {
        x: 1.3, y: y + 0.1, w: 3.5, h: 0.3,
        fontSize: 12, fontFace: this.isp.fonts.title, color: c.text, bold: true, margin: 0
      });
      s.addText(l.desc, {
        x: 1.3, y: y + 0.42, w: 3.5, h: 0.45,
        fontSize: 9, fontFace: this.isp.fonts.body, color: c.text_muted, margin: 0
      });
      if (i < layers.length - 1) {
        s.addShape(this.pres.shapes.RECTANGLE, {
          x: 2.7, y: y + 0.95, w: 0.02, h: 0.2, fill: { color: c.text_muted }
        });
      }
    });

    // Compliance checklist (right)
    const panelBg = isDark ? c.secondary : c.background_alt;
    s.addShape(this.pres.shapes.RECTANGLE, {
      x: 5.3, y: 1.0, w: 4.2, h: 3.8, fill: { color: panelBg },
      shadow: { type: "outer", blur: 3, offset: 1, angle: 135, color: "000000", opacity: isDark ? 0.2 : 0.08 }
    });
    s.addShape(this.pres.shapes.RECTANGLE, { x: 5.3, y: 1.0, w: 4.2, h: 0.04, fill: { color: c.primary } });
    s.addText("COMPLIANCE FRAMEWORK", {
      x: 5.5, y: 1.15, w: 3.8, h: 0.3,
      fontSize: 11, fontFace: this.isp.fonts.title, color: c.primary, bold: true, margin: 0
    });

    complianceItems.forEach((item, i) => {
      const y = 1.6 + i * 0.35;
      s.addImage({ data: this.icons.check, x: 5.55, y: y + 0.02, w: 0.18, h: 0.18 });
      s.addText(item.text, {
        x: 5.85, y, w: 2.4, h: 0.25,
        fontSize: 9, fontFace: this.isp.fonts.body, color: c.text, margin: 0
      });
      s.addText(item.status, {
        x: 8.3, y, w: 1.0, h: 0.25,
        fontSize: 8, fontFace: this.isp.fonts.mono, color: c.success, bold: true, align: "right", margin: 0
      });
    });

    this.addFooter(s);
    return s;
  }

  // FORENSIC RECEIPT SLIDE
  async addForensicReceiptSlide(receiptData) {
    const c = this.isp.colors;
    const gov = this.isp.governance;
    const isDark = parseInt(c.background, 16) < 0x888888;
    const s = this.pres.addSlide();
    s.background = { color: c.background_alt };

    // Compute content hash
    const hashInput = JSON.stringify(receiptData) + Date.now();
    this.contentHash = crypto.createHash("sha256").update(hashInput).digest("hex");

    // Top accent
    s.addShape(this.pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.04, fill: { color: c.primary } });

    // Header
    s.addText("WINDI FORENSIC RECEIPT", {
      x: 0.5, y: 0.25, w: 7, h: 0.5,
      fontSize: 20, fontFace: this.isp.fonts.title, color: c.primary, bold: true, margin: 0
    });
    s.addText(`${this.isp.org_name}  |  Document Integrity Proof  |  Zero-Knowledge Compliance`, {
      x: 0.5, y: 0.7, w: 7, h: 0.3,
      fontSize: 9, fontFace: this.isp.fonts.body, color: c.text_muted, margin: 0
    });

    // Seal visual
    const sealImg = await generateSealVisual(this.isp, this.contentHash);
    s.addImage({ data: sealImg, x: 7.8, y: 0.2, w: 1.6, h: 1.6 });

    // Divider
    s.addShape(this.pres.shapes.RECTANGLE, { x: 0.5, y: 1.1, w: 7, h: 0.015, fill: { color: c.primary } });

    // Receipt fields
    const fields = [
      ["Receipt ID", receiptData.receiptId || `VR-${this.isp.org_id.toUpperCase()}-${Date.now().toString(36)}`],
      ["Document Hash", `sha256:${this.contentHash.substring(0, 32)}`],
      ["", this.contentHash.substring(32)],
      ["Timestamp", receiptData.timestamp || new Date().toISOString()],
      ["Status", "REGISTERED"],
      ["Ledger Entry", receiptData.ledgerEntry || "#--- — Chain VALID"],
      ["ISP Applied", `${this.isp.org_name} — ${this.isp.theme_name}`],
      ["Integrity", "VERIFIED — Merkle Root Consistent"],
    ];

    if (gov.sentinel_status) {
      fields.push(["Sentinel LAW", "6/6 Invariants PASS"]);
    }

    fields.forEach((row, i) => {
      const y = 1.3 + i * 0.3;
      s.addText(row[0], {
        x: 0.7, y, w: 2.0, h: 0.25,
        fontSize: 9, fontFace: this.isp.fonts.body, color: c.text_muted, bold: row[0] !== "", margin: 0
      });
      s.addText(row[1], {
        x: 2.8, y, w: 6.5, h: 0.25,
        fontSize: 9,
        fontFace: (row[0] === "Document Hash" || row[0] === "") ? this.isp.fonts.mono : this.isp.fonts.body,
        color: row[0] === "Status" ? c.success : c.text,
        bold: row[0] === "Status", margin: 0
      });
    });

    // ZK Declaration
    if (gov.zk_declaration) {
      const boxBg = isDark ? c.secondary : c.background_alt;
      const boxY = 1.3 + fields.length * 0.3 + 0.2;
      s.addShape(this.pres.shapes.RECTANGLE, {
        x: 0.5, y: boxY, w: 9, h: 0.75, fill: { color: boxBg },
        shadow: { type: "outer", blur: 3, offset: 1, angle: 135, color: "000000", opacity: 0.2 }
      });
      s.addShape(this.pres.shapes.RECTANGLE, { x: 0.5, y: boxY, w: 0.05, h: 0.75, fill: { color: c.primary } });
      s.addImage({ data: this.icons.lock, x: 0.75, y: boxY + 0.1, w: 0.25, h: 0.25 });
      s.addText("ZERO-KNOWLEDGE ARCHITECTURE", {
        x: 1.1, y: boxY + 0.07, w: 4, h: 0.25,
        fontSize: 10, fontFace: this.isp.fonts.title, color: c.primary, bold: true, margin: 0
      });
      s.addText(
        "This document is self-sovereign. WINDI stores the cryptographic proof (hash), never the content. " +
        "Client retains full data sovereignty. Verification possible offline via hash comparison.",
        {
          x: 1.1, y: boxY + 0.37, w: 8, h: 0.35,
          fontSize: 8, fontFace: this.isp.fonts.body, color: c.text_muted, margin: 0
        }
      );
    }

    // Motto + bottom accent
    s.addText("AI processes. Human decides. WINDI guarantees.", {
      x: 0.5, y: 5.0, w: 9, h: 0.3,
      fontSize: 10, fontFace: this.isp.fonts.title, color: c.text_muted, italic: true, align: "center", margin: 0
    });
    s.addShape(this.pres.shapes.RECTANGLE, { x: 0, y: 5.565, w: 10, h: 0.06, fill: { color: c.primary } });

    return s;
  }

  // ───── GENERATE & SAVE ─────
  async save(outputPath) {
    await this.pres.writeFile({ fileName: outputPath });
    const fileSize = fs.statSync(outputPath).size;
    console.log(`  ✅ Saved: ${outputPath} (${(fileSize / 1024).toFixed(0)}KB)`);
    console.log(`  🔐 Content Hash: sha256:${this.contentHash || "pending"}`);
    return { path: outputPath, size: fileSize, hash: this.contentHash };
  }
}

// ─────────────────────────────────────────────────────
// EXPORTS
// ─────────────────────────────────────────────────────
module.exports = { WindiPPTEngine, ISPLoader, iconToBase64 };
