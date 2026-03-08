/**
 * WINDI D1 — Main Application
 * Desktop DOC Editor — Foundation v1.1 (Status Indicator)
 *
 * Changes from v1.0:
 *   + StatusIndicator in header (governance state display)
 *   + Sign button wired to governance flow
 *   + R0-R5 scale preview strip
 */
import React, { useState, useEffect } from 'react';
import D1Editor from './components/D1Editor';
import DocSidebar from './components/DocSidebar';
import GovernancePanel from './components/GovernancePanel';
import StatusIndicator from './components/StatusIndicator';
import useDocStore from './stores/docStore';
import { loadDragonDraft } from './stores/docStore';

import DocumentSeal from './components/DocumentSeal';
import A4PageWrapper from './components/A4PageWrapper';
import ExportMenu, { LangSelector } from './components/ExportMenu';
import './a4-page.css';
import './m3-refinements.css';

export default function App() {
  const { docId, title, setTitle, createDoc, saveStatus, integrityStatus, content , sealReceiptId, sealHash, sealTimestamp, sealStatus, sealSgeScore, sealGovernanceLevel } = useDocStore();
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [lang, setLang] = useState('de');
  const [govPanelOpen, setGovPanelOpen] = useState(false);

  // Determine if Sign should be enabled (document is protected)
  const isProtected = saveStatus === 'saved' && integrityStatus === 'ok' && content &&
    JSON.stringify(content) !== '{"type":"doc","content":[{"type":"paragraph"}]}';
  const isSigned = false; // Phase M4 — will come from store

  // Auto-create first document OR load Dragon draft
  useEffect(() => {
    const init = async () => {
      // ═══ DRAGON BRIDGE ═══════════════════════════════════════════
      const params = new URLSearchParams(window.location.search);
      const draftId = params.get('doc');
      const hasLocalDraft = !!localStorage.getItem('windi_dragon_draft');

      if (draftId || hasLocalDraft) {
        const draft = await loadDragonDraft(draftId);
        if (draft) {
          // Criar doc novo com conteúdo do Dragon
          await createDoc();
          // Aguardar criação e então popular
          setTimeout(() => {
            useDocStore.getState().setTitle(draft.title);
            useDocStore.getState().updateContent(draft.content);
          }, 100);
          setSidebarOpen(false);
          // Limpar URL sem reload
          window.history.replaceState({}, '', window.location.pathname);
          console.log('[Dragon Bridge] Draft loaded:', draft.title);
          return;
        }
      }

      // ═══ FLUXO NORMAL ════════════════════════════════════════════
      const docs = await useDocStore.getState().listDocs();
      if (docs.length === 0) {
        await createDoc();
        setSidebarOpen(false);
      } else {
        await useDocStore.getState().loadDoc(docs[0].docId);
      }
    };
    init();
  }, []);

  return (
    <div className="d1-app">
      {/* Top Header */}
      <header className="d1-header">
        <div className="header-left">
          <button
            className="btn-icon btn-sidebar-toggle"
            onClick={() => setSidebarOpen(!sidebarOpen)}
            title="Toggle documents"
          >
            ☰
          </button>
          <div className="windi-logo">
            <span className="logo-w">W</span>
            <span className="logo-text">INDI</span>
            <span className="logo-sep">|</span>
            <span className="logo-product">DOC</span>
          </div>

          {/* ★ STATUS INDICATOR — Governance State ★ */}
          {docId && <StatusIndicator lang={lang} />}
        </div>

        <div className="header-center">
          {docId && (
            <input
              className="doc-title-input"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Document title..."
            />
          )}
        </div>

        <div className="header-right">
          {/* R0-R5 Governance Scale Preview */}
          <div className="r-scale-strip" title="SGE Governance Scale (R0–R5)">
            <div className="r-dot" style={{ background: 'var(--r0-integrity)' }} title="R0 — Total Integrity" />
            <div className="r-dot" style={{ background: 'var(--r1-low)' }} title="R1 — Low Risk" />
            <div className="r-dot" style={{ background: 'var(--r2-moderate)' }} title="R2 — Moderate" />
            <div className="r-dot" style={{ background: 'var(--r3-alert)' }} title="R3 — Semantic Alert" />
            <div className="r-dot" style={{ background: 'var(--r4-high)' }} title="R4 — High Risk" />
            <div className="r-dot" style={{ background: 'var(--r5-critical)' }} title="R5 — Critical" />
          </div>

          <button
            className={`btn-icon btn-governance ${govPanelOpen ? 'active' : ''}`}
            onClick={() => setGovPanelOpen(!govPanelOpen)}
            title="Governance trail"
          >
            🛡
          </button>
          <button
            className={`btn-save ${saveStatus === 'saved' ? 'saved' : ''}`}
            onClick={() => { /* trigger save */ }}
            title="Save document"
          >
            💾 {saveStatus === 'saved' ? 'Saved' : 'Save'}
          </button>
          <button
            className="btn-print"
            onClick={() => window.print()}
            title="Print document"
          >
            🖨 Print
          </button>
          <ExportMenu
              getHTML={() => {
                const pm = document.querySelector('.ProseMirror');
                return pm ? pm.innerHTML : '';
              }}
            lang={lang}
              docId={docId}
              title={title}
              content={content}
              getHTML={() => {
                const pm = document.querySelector('.ProseMirror');
                return pm ? pm.innerHTML : '';
              }}
              sealData={{
              receiptId: sealReceiptId,
              hash: sealHash,
              timestamp: sealTimestamp,
              status: sealStatus,
            }}
          />
          <button
            className={`btn-sign ${isProtected ? 'btn-sign-ready' : ''} ${isSigned ? 'btn-sign-sealed' : ''}`}
            title={isProtected ? 'Seal with legal validity (eIDAS)' : isSigned ? 'Sealed with legal validity' : 'Write and save content first'}
            disabled={!isProtected || isSigned}
          >
            <svg className="sign-shield-icon" viewBox="0 0 16 16" width="14" height="14">
              <path d="M8 1L2 4v4c0 3.5 2.5 6.4 6 7 3.5-.6 6-3.5 6-7V4L8 1z"
                    fill="none" stroke="currentColor" strokeWidth="1.3" />
              {isSigned && (
                <path d="M5.5 8.5l2 2 3-3.5" fill="none" stroke="currentColor"
                      strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round" />
              )}
            </svg>
            {isSigned ? 'Sealed' : 'Sign'}
          </button>
        </div>
      </header>

      {/* Main Content */}
      <div className="d1-main">
        {sidebarOpen && (
          <DocSidebar onClose={() => setSidebarOpen(false)} />
        )}

        <div className="d1-editor-area">
          {docId ? (
            <A4PageWrapper
                sealReceiptId={sealReceiptId}
                sealHash={sealHash}
                sealTimestamp={sealTimestamp}
                sealStatus={sealStatus}
                sealSgeScore={sealSgeScore}
                sealGovernanceLevel={sealGovernanceLevel}
                sealLang={lang}
                docId={docId}
                integrityState={integrityStatus === 'ok' ? 'ok' : 'pending'}
              >
                <D1Editor />
              </A4PageWrapper>
          ) : (
            <div className="d1-welcome">
              <h1>WINDI Desktop — DOC</h1>
              <p>Governance-aware document editing.</p>
              <p><em>AI processes. Human decides. WINDI guarantees.</em></p>
              <button className="btn-create-welcome" onClick={createDoc}>
                Create your first document
              </button>
            </div>
          )}
        </div>

        <GovernancePanel
          visible={govPanelOpen}
          onClose={() => setGovPanelOpen(false)}
        />
      </div>
    </div>
  );
}
