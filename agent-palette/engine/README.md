# WINDI DragonEngine v2.0

> AI processes. Human decides. WINDI guarantees.

Unified document intelligence engine for mobile and desktop.

## Architecture

```
engine/
├── index.js              # Main entry point
├── loader.js             # Browser loader script
├── README.md             # This file
│
├── session/              # Layer 1: SessionCore
│   └── dragon_session.js # History management with `content:` field
│
├── core/                 # Layer 2: DragonCore
│   └── dragon_engine_core.js # LLM call wrapper with valid_history
│
├── bridge/               # Layer 4: AgentBridge
│   └── agent_bridge.js   # Relative URLs for mobile+desktop
│
└── manifests/            # Layer 3: DocManifests
    ├── index.js          # Manifest registry
    ├── letter.json       # Letter (Brief/Carta)
    ├── email.json        # Email (E-Mail)
    ├── memo.json         # Memo (Memorando)
    ├── note.json         # Note (Notiz/Nota)
    ├── journal.json      # Journal (Tagebuch/Diário)
    ├── recipe.json       # Recipe (Rezept/Receita)
    ├── report.json       # Report (Bericht/Relatório)
    ├── contract.json     # Contract (Vertrag/Contrato)
    ├── invoice.json      # Invoice (Rechnung/Fatura)
    ├── protocol.json     # Protocol (Protokoll/Ata)
    ├── analysis.json     # Analysis (Analyse/Análise)
    ├── presentation.json # Presentation (Präsentation)
    ├── communique.json   # Communiqué (Comunicado)
    ├── certificate.json  # Certificate (Bescheinigung)
    ├── declaration.json  # Declaration (Erklärung)
    └── creative_virtue.json # Proof of Creation
```

## Key Fixes in v2.0

| Bug | v1 (Monolith) | v2 (Engine) |
|-----|---------------|-------------|
| Message format | `text:` | `content:` (Claude API) |
| URLs | `127.0.0.1:8108` hardcoded | Relative URLs via AgentBridge |
| Session storage | No guard | Length check before parse |
| History injection | Missing | `getHistoryForBackend()` |

## Usage

### Browser (via loader)

```html
<script src="/engine/loader.js"></script>
<script>
  document.addEventListener('DragonEngineReady', async () => {
    const engine = await initDragonEngine();

    // Chat with Dragon
    const response = await engine.chat('Hello Dragon!');
    console.log(response.message);

    // Get document type
    const letterManifest = engine.getDocType('letter');
    console.log(letterManifest.names.de); // "Brief"

    // Check health
    const health = await engine.checkHealth();
    console.log(health);
  });
</script>
```

### Browser (manual loading)

```html
<script src="/engine/session/dragon_session.js"></script>
<script src="/engine/core/dragon_engine_core.js"></script>
<script src="/engine/bridge/agent_bridge.js"></script>
<script src="/engine/manifests/index.js"></script>
<script src="/engine/index.js"></script>
<script>
  const engine = DragonEngine.quickInit();
  engine.chat('Hello!').then(console.log);
</script>
```

### Node.js

```javascript
const DragonEngine = require('./engine');
const { getSession } = require('./engine/session/dragon_session');
const { getBridge } = require('./engine/bridge/agent_bridge');

// Initialize
const session = getSession();
const bridge = getBridge();

// Use
const url = bridge.getUrl('dragon', '/chat');
console.log(url); // Production: https://windi-domain.com/app/api/dragon/chat
```

## Components

### SessionCore (dragon_session.js)

Manages conversation history with proper message format.

```javascript
const session = getSession();

// Add messages
session.addUserMessage('Hello');
session.addAssistantMessage('Hi there!', { dragon: 'guardian' });

// Get history for API (uses `content:` not `text:`)
const history = session.getValidHistory(20);
// [{ role: 'user', content: 'Hello' }, ...]

// Get for backend (role mapping)
const backendHistory = session.getHistoryForBackend(20);
// [{ role: 'human', content: 'Hello' }, ...]
```

### DragonCore (dragon_engine_core.js)

LLM call wrapper with automatic history injection.

```javascript
const core = createDragonCore({ session: getSession() });

const response = await core.chat('Write a letter', {
  tier: 'professional',
  lang: 'de',
  docType: 'letter'
});

console.log(response.message);
console.log(response.dragon); // 'guardian' | 'architect' | 'witness'
```

### AgentBridge (agent_bridge.js)

Resolves URLs for all WINDI services.

```javascript
const bridge = getBridge();

// Get URLs
bridge.getUrl('dragon', '/chat');  // /app/api/dragon/chat (prod)
bridge.getUrl('ledger', '/seal');  // /ledger/seal (prod)
bridge.getUrl('export', '/pdf');   // /export/pdf (prod)

// Health checks
const health = await bridge.checkHealth('dragon');
const allHealth = await bridge.checkAllHealth();
```

### ManifestRegistry (manifests/index.js)

Provides access to document type definitions.

```javascript
const registry = getManifestRegistry();
await registry.load('/engine/manifests');

// Get manifest
const letter = registry.get('letter');
console.log(letter.names.de); // "Brief"
console.log(letter.breath.de); // "Absicht senden"

// Check access
const canAccess = registry.canAccess('communique', 'HIGH'); // true

// Get by tier
const freeTypes = registry.getByTier('FREE');
```

## Service Map

| Service | Port | Proxy Path | Purpose |
|---------|------|------------|---------|
| Dragon | 8108 | `/app/api/dragon` | LLM + Document Intelligence |
| Ledger | 8101 | `/ledger` | Forensic Receipts |
| Export | 8103 | `/export` | PDF/DOCX/XLSX |
| Vault | 8106 | `/vault` | Document Storage |
| Communiqué | 8105 | `/communique` | Distribution |
| Wallet | 8098 | `/wallet` | Identity |
| Bridge | 8097 | `/bridge` | Command Routing |

## Migration from v1

1. Replace hardcoded URLs:
```javascript
// Before
fetch('http://localhost:8108/api/dragon/chat', ...)

// After
const bridge = getBridge();
fetch(bridge.getDragonUrl('/chat'), ...)
```

2. Fix message format:
```javascript
// Before
history.push({ role: 'human', text: message });

// After
session.addUserMessage(message); // Uses `content:` internally
```

3. Use session management:
```javascript
// Before
const history = JSON.parse(sessionStorage.getItem('history') || '[]');

// After
const session = getSession();
const history = session.getValidHistory();
```

## Stats

- **16 files** total
- **1,469 lines** of JavaScript
- **14 document manifests** (trilingual DE/EN/PT)
- **12 services** mapped in AgentBridge

---

*Three Dragons Protocol v2.0*
*(c) 2026 WINDI Publishing House — Kempten, Bavaria*
