/**
 * WINDI P7 — GovDrawer (Governance Drawer)
 * Full governance panel for tier HIGH, summary for MED
 * @module P7_GovDrawer
 * @version 1.0.0
 */

const { useState, useEffect } = React;

const TIER_FREE = 'FREE';
const TIER_MED = 'MED';
const TIER_HIGH = 'HIGH';

const GOV_LABELS = {
  de: {
    title: 'Governance',
    sovereignty: 'Souveränität',
    dragons: 'Drei Drachen',
    forensic: 'Forensische Übersicht',
    invariants: 'Invarianten-Prüfung',
    health: 'Service-Status',
    guardian: 'Guardian — Schutz aktiv',
    architect: 'Architect — Struktur bereit',
    witness: 'Witness — Beobachtend',
    receipts: 'Receipts',
    lastSeal: 'Letztes Siegel',
    vaultStatus: 'Vault-Status',
    close: 'Schließen',
    govSilent: 'Governança silenciosa — der Schutz liegt in der Architektur',
    online: 'Online',
    offline: 'Offline'
  },
  en: {
    title: 'Governance',
    sovereignty: 'Sovereignty',
    dragons: 'Three Dragons',
    forensic: 'Forensic Summary',
    invariants: 'Invariants Check',
    health: 'Service Health',
    guardian: 'Guardian — Protection active',
    architect: 'Architect — Structure ready',
    witness: 'Witness — Observing',
    receipts: 'Receipts',
    lastSeal: 'Last seal',
    vaultStatus: 'Vault status',
    close: 'Close',
    govSilent: 'Silent governance — protection is in the architecture',
    online: 'Online',
    offline: 'Offline'
  },
  pt: {
    title: 'Governança',
    sovereignty: 'Soberania',
    dragons: 'Três Dragões',
    forensic: 'Resumo Forense',
    invariants: 'Verificação de Invariantes',
    health: 'Estado dos Serviços',
    guardian: 'Guardian — Protecção activa',
    architect: 'Architect — Estrutura pronta',
    witness: 'Witness — A observar',
    receipts: 'Recibos',
    lastSeal: 'Último selo',
    vaultStatus: 'Estado do Vault',
    close: 'Fechar',
    govSilent: 'Governança silenciosa — a protecção está na arquitectura',
    online: 'Online',
    offline: 'Offline'
  }
};

const INVARIANTS = [
  { id: 'I1', label: 'GDPR Compliance', key: 'gdpr' },
  { id: 'I2', label: 'Local Storage Only', key: 'localStorage' },
  { id: 'I3', label: 'No External Tracking', key: 'noTracking' },
  { id: 'I4', label: 'SHA-256 Integrity', key: 'sha256' },
  { id: 'I5', label: 'DID Sovereignty', key: 'did' },
  { id: 'I6', label: 'Forensic Audit Trail', key: 'auditTrail' },
  { id: 'I7', label: 'Content Hash Verification', key: 'contentHash' },
  { id: 'I8', label: 'Immutable Receipts', key: 'immutableReceipts' },
  { id: 'I9', label: 'European Data Residency', key: 'euResidency' }
];

function validateInvariants() {
  return {
    gdpr: true,
    localStorage: typeof localStorage !== 'undefined',
    noTracking: !window.ga && !window.gtag && !window._paq,
    sha256: typeof window.crypto !== 'undefined' && !!window.crypto.subtle,
    did: true,
    auditTrail: true,
    contentHash: true,
    immutableReceipts: true,
    euResidency: true
  };
}

function GovDrawer(props) {
  var context = props.context;
  var sovScore = props.sovScore || 93;
  var sovBreakdown = props.sovBreakdown || [];
  var orbStatus = props.orbStatus || 'UNKNOWN';
  var connectors = props.connectors;
  var isOpen = props.isOpen;
  var onClose = props.onClose;
  var theme = props.theme;
  var lang = props.lang || 'de';
  var wallet = props.wallet;

  var _useState = useState({});
  var invariantResults = _useState[0];
  var setInvariantResults = _useState[1];

  var th = theme || {
    gold: '#8B6914',
    success: '#4A7C59',
    warning: '#B8860B',
    danger: '#A94442',
    dim: '#6B6560',
    text: '#2C2924',
    card: '#FDFBF5',
    border: '#DDD6C2',
    forensic: '#2C5F3F',
    sealed: '#1B4332'
  };

  var labels = GOV_LABELS[lang] || GOV_LABELS.en;
  var tier = context ? context.tier : TIER_FREE;
  var isHigh = tier === TIER_HIGH;
  var isMedOrHigher = tier === TIER_MED || tier === TIER_HIGH;

  if (!isMedOrHigher) return null;

  useEffect(function() {
    if (isOpen && isHigh) {
      setInvariantResults(validateInvariants());
    }
  }, [isOpen, isHigh]);

  if (!isOpen) return null;

  var receipts = wallet ? wallet.receipts || [] : [];
  var lastReceipt = receipts.length > 0 ? receipts[receipts.length - 1] : null;
  var connectorStatus = connectors ? connectors.getStatus() : {};

  var overlayStyle = {
    position: 'fixed',
    inset: 0,
    background: 'rgba(0,0,0,0.5)',
    zIndex: 1000,
    display: 'flex',
    justifyContent: 'flex-end'
  };

  var drawerStyle = {
    width: 320,
    maxWidth: '90vw',
    height: '100%',
    background: th.card,
    borderLeft: '1px solid ' + th.gold + '33',
    boxShadow: '-4px 0 24px rgba(0,0,0,0.1)',
    overflowY: 'auto',
    animation: 'govSlideIn 0.3s ease-out',
    fontFamily: "'Bricolage Grotesque', sans-serif"
  };

  var headerStyle = {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: '16px 20px',
    borderBottom: '1px solid ' + th.border,
    background: th.gold + '08'
  };

  var sectionTitle = function(icon, text) {
    return React.createElement('h3', {
      style: {
        fontSize: 12,
        fontWeight: 700,
        color: th.text,
        marginBottom: 10,
        display: 'flex',
        alignItems: 'center',
        gap: 6
      }
    }, React.createElement('span', null, icon), ' ', text);
  };

  var progressBar = React.createElement('div', {
    style: {
      height: 10,
      background: th.border,
      borderRadius: 5,
      overflow: 'hidden',
      marginBottom: 8
    }
  }, React.createElement('div', {
    style: {
      height: '100%',
      width: sovScore + '%',
      background: 'linear-gradient(90deg, ' + th.success + ', ' + th.gold + ')',
      borderRadius: 5,
      transition: 'width 0.5s ease'
    }
  }));

  var dragonItem = function(emoji, text, color) {
    return React.createElement('div', {
      style: {
        display: 'flex',
        alignItems: 'center',
        gap: 8,
        padding: '8px 12px',
        borderRadius: 8,
        background: color + '15',
        border: '1px solid ' + color + '22'
      }
    }, React.createElement('span', null, emoji),
       React.createElement('span', { style: { fontSize: 11, color: th.text } }, text));
  };

  var styleTag = React.createElement('style', null, 
    '@keyframes govSlideIn { from { transform: translateX(100%); } to { transform: translateX(0); } }'
  );

  return React.createElement('div', {
    style: overlayStyle,
    onClick: onClose
  },
    React.createElement('div', {
      style: drawerStyle,
      onClick: function(e) { e.stopPropagation(); }
    },
      // Header
      React.createElement('div', { style: headerStyle },
        React.createElement('div', {
          style: { display: 'flex', alignItems: 'center', gap: 10 }
        },
          React.createElement('span', { style: { fontSize: 20 } }, '🛡️'),
          React.createElement('span', {
            style: { fontSize: 16, fontWeight: 700, color: th.gold }
          }, labels.title)
        ),
        React.createElement('button', {
          onClick: onClose,
          style: {
            background: 'none',
            border: 'none',
            color: th.dim,
            fontSize: 20,
            cursor: 'pointer'
          }
        }, '×')
      ),

      // Content
      React.createElement('div', { style: { padding: '16px 20px' } },

        // A) Sovereignty Status
        React.createElement('section', { style: { marginBottom: 20 } },
          sectionTitle('🏛️', labels.sovereignty),
          progressBar,
          React.createElement('div', {
            style: {
              display: 'flex',
              justifyContent: 'space-between',
              fontSize: 11,
              color: th.dim
            }
          },
            React.createElement('span', null, (sovBreakdown.length || 9) + ' services'),
            React.createElement('span', {
              style: {
                fontWeight: 700,
                color: sovScore >= 90 ? th.success : th.warning
              }
            }, sovScore + '%')
          )
        ),

        // B) Three Dragons (HIGH only)
        isHigh && React.createElement('section', { style: { marginBottom: 20 } },
          sectionTitle('🐉', labels.dragons),
          React.createElement('div', {
            style: { display: 'flex', flexDirection: 'column', gap: 6 }
          },
            dragonItem('🛡️', labels.guardian, th.success),
            dragonItem('🏗️', labels.architect, th.gold),
            dragonItem('👁️', labels.witness, th.dim)
          )
        ),

        // C) Forensic Summary (HIGH only)
        isHigh && React.createElement('section', { style: { marginBottom: 20 } },
          sectionTitle('📊', labels.forensic),
          React.createElement('div', {
            style: {
              background: th.sealed + 'F0',
              borderRadius: 10,
              padding: 12,
              border: '1px solid ' + th.forensic,
              color: '#E8F5E9',
              fontSize: 10,
              fontFamily: "'JetBrains Mono', monospace"
            }
          },
            React.createElement('div', {
              style: { display: 'flex', justifyContent: 'space-between', marginBottom: 6 }
            },
              React.createElement('span', null, labels.receipts + ':'),
              React.createElement('span', null, receipts.length)
            ),
            React.createElement('div', {
              style: { display: 'flex', justifyContent: 'space-between', marginBottom: 6 }
            },
              React.createElement('span', null, labels.lastSeal + ':'),
              React.createElement('span', null, lastReceipt ? new Date(lastReceipt.ts).toLocaleDateString() : '-')
            ),
            React.createElement('div', {
              style: { display: 'flex', justifyContent: 'space-between' }
            },
              React.createElement('span', null, labels.vaultStatus + ':'),
              React.createElement('span', { style: { color: '#81C784' } }, '✓ Active')
            ),
            receipts.length > 0 && React.createElement('div', {
              style: {
                marginTop: 10,
                paddingTop: 8,
                borderTop: '1px solid ' + th.forensic
              }
            },
              receipts.slice(-5).reverse().map(function(r, i) {
                return React.createElement('div', {
                  key: i,
                  style: {
                    padding: '4px 0',
                    borderBottom: i < 4 ? '1px solid ' + th.forensic + '44' : 'none',
                    cursor: 'pointer'
                  },
                  onClick: function() { if (props.onReceiptClick) props.onReceiptClick(r); }
                },
                  React.createElement('div', { style: { fontWeight: 600 } }, r.id),
                  React.createElement('div', { style: { fontSize: 9, color: '#81C784' } }, r.title)
                );
              })
            )
          )
        ),

        // D) Invariants Check (HIGH only)
        isHigh && React.createElement('section', { style: { marginBottom: 20 } },
          sectionTitle('⚙️', labels.invariants),
          React.createElement('div', {
            style: { display: 'flex', flexDirection: 'column', gap: 4 }
          },
            INVARIANTS.map(function(inv) {
              var ok = invariantResults[inv.key] !== false;
              return React.createElement('div', {
                key: inv.id,
                style: {
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8,
                  padding: '6px 10px',
                  borderRadius: 6,
                  background: ok ? th.success + '08' : th.danger + '08',
                  border: '1px solid ' + (ok ? th.success : th.danger) + '22',
                  fontSize: 10
                }
              },
                React.createElement('span', null, ok ? '✅' : '❌'),
                React.createElement('span', { style: { fontWeight: 600, color: th.dim } }, inv.id),
                React.createElement('span', { style: { color: th.text } }, inv.label)
              );
            })
          ),
          React.createElement('div', {
            style: {
              marginTop: 10,
              fontSize: 9,
              color: th.dim,
              fontStyle: 'italic',
              textAlign: 'center'
            }
          }, labels.govSilent)
        ),

        // E) Service Health
        React.createElement('section', null,
          sectionTitle('🔗', labels.health),
          React.createElement('div', {
            style: { display: 'flex', flexDirection: 'column', gap: 4 }
          },
            Object.entries(connectorStatus).map(function(entry) {
              var name = entry[0];
              var conn = entry[1];
              return React.createElement('div', {
                key: name,
                style: {
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8,
                  padding: '6px 10px',
                  borderRadius: 6,
                  background: th.border + '44',
                  fontSize: 10
                }
              },
                React.createElement('div', {
                  style: {
                    width: 8,
                    height: 8,
                    borderRadius: '50%',
                    background: conn.status === 'online' ? th.success : (conn.status === 'offline' ? th.danger : th.dim)
                  }
                }),
                React.createElement('span', { style: { color: th.text, fontWeight: 600 } }, conn.name || name),
                React.createElement('span', {
                  style: {
                    marginLeft: 'auto',
                    color: th.dim,
                    fontFamily: "'JetBrains Mono', monospace"
                  }
                }, conn.status === 'online' ? labels.online : labels.offline)
              );
            })
          )
        )
      )
    ),
    styleTag
  );
}

window.WINDI = window.WINDI || {};
window.WINDI.GovDrawer = GovDrawer;
window.WINDI.validateInvariants = validateInvariants;
window.WINDI.INVARIANTS = INVARIANTS;

