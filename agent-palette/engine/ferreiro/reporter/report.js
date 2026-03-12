/**
 * W-FERR-001 — Report Generator
 * =============================
 * Gera relatórios de saúde em múltiplos formatos.
 */

(function() {
  'use strict';

  /**
   * Generate health summary
   */
  function generateSummary(probeResults) {
    const issues = probeResults.issues || [];

    return {
      timestamp: probeResults.timestamp,
      score: probeResults.score,
      status: probeResults.score >= 90 ? 'HEALTHY' :
              probeResults.score >= 70 ? 'WARNING' : 'CRITICAL',
      services: {
        total: probeResults.services?.total || 0,
        ok: probeResults.services?.ok || 0,
        down: probeResults.services?.down || 0
      },
      manifests: {
        total: probeResults.manifests?.total || 0,
        ok: probeResults.manifests?.ok || 0,
        error: probeResults.manifests?.error || 0
      },
      code: {
        total: probeResults.code?.total || 0,
        ok: probeResults.code?.ok || 0,
        issues: probeResults.code?.issues || 0
      },
      issueCount: issues.length,
      criticalCount: issues.filter(i => i.critical).length
    };
  }

  /**
   * Generate detailed report
   */
  function generateReport(cycleResults) {
    const { probe, diagnosis, heal } = cycleResults;

    return {
      version: '1.0.0',
      timestamp: new Date().toISOString(),
      summary: generateSummary(probe),
      probe: {
        duration: probe.duration,
        services: probe.services?.results || [],
        manifests: probe.manifests?.results || [],
        code: probe.code?.results || []
      },
      diagnosis: {
        total: diagnosis.issues.length,
        byLevel: {
          immediate: diagnosis.actions.immediate.length,
          withSeal: diagnosis.actions.withSeal.length,
          proposals: diagnosis.actions.proposals.length,
          alerts: diagnosis.actions.alerts.length
        },
        issues: diagnosis.issues
      },
      heal: {
        cured: heal.cured,
        failed: heal.failed,
        proposed: heal.proposed,
        alerted: heal.alerted
      }
    };
  }

  /**
   * Generate HTML report
   */
  function generateHtmlReport(report) {
    const statusColor = {
      'HEALTHY': '#22c55e',
      'WARNING': '#f59e0b',
      'CRITICAL': '#ef4444'
    }[report.summary.status] || '#6b7280';

    return `
<!DOCTYPE html>
<html lang="pt">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>WINDI Health Report - ${report.timestamp}</title>
  <style>
    body { font-family: system-ui, -apple-system, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; background: #0f172a; color: #e2e8f0; }
    h1 { color: #f8fafc; border-bottom: 2px solid #334155; padding-bottom: 10px; }
    .score { font-size: 48px; font-weight: bold; color: ${statusColor}; }
    .status { display: inline-block; padding: 4px 12px; border-radius: 4px; background: ${statusColor}; color: white; }
    .section { background: #1e293b; border-radius: 8px; padding: 16px; margin: 16px 0; }
    .section h2 { margin-top: 0; color: #94a3b8; font-size: 14px; text-transform: uppercase; }
    table { width: 100%; border-collapse: collapse; }
    th, td { padding: 8px; text-align: left; border-bottom: 1px solid #334155; }
    th { color: #94a3b8; }
    .ok { color: #22c55e; }
    .warning { color: #f59e0b; }
    .error { color: #ef4444; }
    .badge { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 12px; }
    .badge-1 { background: #22c55e; }
    .badge-2 { background: #3b82f6; }
    .badge-3 { background: #f59e0b; }
    .badge-4 { background: #ef4444; }
  </style>
</head>
<body>
  <h1>🐉 WINDI Health Report</h1>
  <p>Generated: ${report.timestamp}</p>

  <div class="section">
    <div class="score">${report.summary.score}%</div>
    <span class="status">${report.summary.status}</span>
  </div>

  <div class="section">
    <h2>Overview</h2>
    <table>
      <tr><th>Category</th><th>OK</th><th>Issues</th><th>Total</th></tr>
      <tr>
        <td>Services</td>
        <td class="ok">${report.summary.services.ok}</td>
        <td class="error">${report.summary.services.down}</td>
        <td>${report.summary.services.total}</td>
      </tr>
      <tr>
        <td>Manifests</td>
        <td class="ok">${report.summary.manifests.ok}</td>
        <td class="error">${report.summary.manifests.error}</td>
        <td>${report.summary.manifests.total}</td>
      </tr>
      <tr>
        <td>Code</td>
        <td class="ok">${report.summary.code.ok}</td>
        <td class="warning">${report.summary.code.issues}</td>
        <td>${report.summary.code.total}</td>
      </tr>
    </table>
  </div>

  <div class="section">
    <h2>Issues (${report.diagnosis.total})</h2>
    <table>
      <tr><th>Error</th><th>Level</th><th>Action</th></tr>
      ${report.diagnosis.issues.map(i => `
        <tr>
          <td>${i.errorId}</td>
          <td><span class="badge badge-${i.level}">${i.level}</span></td>
          <td>${i.label}</td>
        </tr>
      `).join('')}
    </table>
  </div>

  <div class="section">
    <h2>Heals</h2>
    <p>✅ Cured: ${report.heal.cured.length}</p>
    <p>❌ Failed: ${report.heal.failed.length}</p>
    <p>📋 Proposed: ${report.heal.proposed.length}</p>
    <p>⚠️ Alerts: ${report.heal.alerted.length}</p>
  </div>

  <footer style="margin-top: 40px; color: #64748b; font-size: 12px;">
    W-FERR-001 — O Ferreiro | WINDI Health Monitor v1.0.0
  </footer>
</body>
</html>
    `.trim();
  }

  /**
   * Generate Markdown report
   */
  function generateMarkdownReport(report) {
    return `
# 🐉 WINDI Health Report

**Generated:** ${report.timestamp}
**Score:** ${report.summary.score}%
**Status:** ${report.summary.status}

## Overview

| Category | OK | Issues | Total |
|----------|---:|-------:|------:|
| Services | ${report.summary.services.ok} | ${report.summary.services.down} | ${report.summary.services.total} |
| Manifests | ${report.summary.manifests.ok} | ${report.summary.manifests.error} | ${report.summary.manifests.total} |
| Code | ${report.summary.code.ok} | ${report.summary.code.issues} | ${report.summary.code.total} |

## Issues (${report.diagnosis.total})

| Error | Level | Action |
|-------|:-----:|--------|
${report.diagnosis.issues.map(i => `| ${i.errorId} | ${i.level} | ${i.label} |`).join('\n')}

## Heal Results

- ✅ Cured: ${report.heal.cured.length}
- ❌ Failed: ${report.heal.failed.length}
- 📋 Proposed: ${report.heal.proposed.length}
- ⚠️ Alerts: ${report.heal.alerted.length}

---
*W-FERR-001 — O Ferreiro | WINDI Health Monitor v1.0.0*
    `.trim();
  }

  // Export
  const FerreiroReport = {
    generateSummary,
    generateReport,
    generateHtmlReport,
    generateMarkdownReport
  };

  if (typeof module !== 'undefined' && module.exports) {
    module.exports = FerreiroReport;
  }

  if (typeof window !== 'undefined') {
    window.FerreiroReport = FerreiroReport;
  }

})();
