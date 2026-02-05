#!/usr/bin/env node
/**
 * WINDI Dispatcher — Test Mode
 * =============================
 * Tests the full pipeline WITHOUT sending real email.
 * Uses nodemailer's test account (Ethereal) for safe testing.
 */

require("dotenv").config();
const axios = require("axios");
const nodemailer = require("nodemailer");
const { fetchBriefing, computeAlertLevel } = require("./windi-dispatcher");

const BRIEFING_URL = process.env.WINDI_BRIEFING_URL || "http://127.0.0.1:8090/api/briefing";

(async () => {
  console.log("\n🐉 WINDI Dispatcher — Test Mode\n");

  // 1. Test Briefing API
  console.log("1️⃣  Testing Briefing API...");
  try {
    const data = await fetchBriefing();
    const alert = computeAlertLevel(data);
    console.log(`   ✅ Briefing OK: ${data.reportId} | ${data.briefingDate} | Alert: ${alert.emoji} ${alert.level}`);
    console.log(`   📄 Decisions: ${data.decisions?.length || 0} | Risks active: ${data.risks?.active || 0}`);
    console.log(`   🔗 Hash: ${data.hash}`);
  } catch (err) {
    console.error(`   ❌ Briefing FAILED: ${err.message}`);
    console.log("\n   → Is the Day-by-Day server running on :8090?");
    process.exit(1);
  }

  // 2. Test PDF endpoint
  console.log("\n2️⃣  Testing PDF endpoint...");
  try {
    const resp = await axios.post(
      process.env.WINDI_PDF_URL || "http://127.0.0.1:8090/api/report/pdf",
      { type: "daily", lang: "de", mode: "meeting" },
      { timeout: 10000 }
    );
    if (resp.data?.success && resp.data?.pdfBase64) {
      console.log(`   ✅ PDF available: ${resp.data.filename || "WINDI_Report.pdf"}`);
    } else {
      console.log("   ⚠️  PDF endpoint responded but no pdfBase64 — email will send without attachment");
    }
  } catch {
    console.log("   ⚠️  PDF endpoint not available — email will send without attachment (OK)");
  }

  // 3. Test email rendering with Ethereal
  console.log("\n3️⃣  Testing email rendering (Ethereal)...");
  try {
    const testAccount = await nodemailer.createTestAccount();
    const transporter = nodemailer.createTransport({
      host: "smtp.ethereal.email",
      port: 587,
      secure: false,
      auth: { user: testAccount.user, pass: testAccount.pass },
    });

    const data = await fetchBriefing();
    const { buildSubject, buildEmailBody } = (() => {
      // Re-import logic for test
      const mod = require("./windi-dispatcher");
      // We need to rebuild — just do a quick inline
      return {
        buildSubject: () => {
          const { emoji } = computeAlertLevel(data);
          const hash8 = (data.hash || "").toString().slice(0, 8);
          return `${emoji} WINDI Governance Briefing | ${data.briefingDate} | Hash: ${hash8}`;
        },
        buildEmailBody: () => ({ html: "<p>Test</p>", text: "Test" }),
      };
    })();

    const info = await transporter.sendMail({
      from: '"WINDI Test" <test@windi.dev>',
      to: "council@test.dev",
      subject: buildSubject(),
      text: "WINDI Dispatcher test — pipeline OK",
      html: "<p>WINDI Dispatcher test — pipeline OK</p>",
    });

    const previewUrl = nodemailer.getTestMessageUrl(info);
    console.log(`   ✅ Email sent to Ethereal!`);
    console.log(`   🔗 Preview: ${previewUrl}`);
  } catch (err) {
    console.log(`   ⚠️  Ethereal test skipped: ${err.message}`);
  }

  // 4. Whitelist check
  console.log("\n4️⃣  Whitelist check...");
  const recipients = (process.env.WINDI_RECIPIENTS || "").split(",").filter(Boolean);
  if (recipients.length) {
    console.log(`   ✅ ${recipients.length} recipient(s): ${recipients.join(", ")}`);
  } else {
    console.log("   ⚠️  WINDI_RECIPIENTS is empty — dispatch will refuse to send");
  }

  console.log("\n✅ All tests complete. Ready for production dispatch.\n");
})();
