# WINDI JMPG Export — Desktop Integration Reference

## Architecture

```
a4Desk Desktop (:8100)         Export Engine (:8103)        Ledger (:8101)
     │                              │                           │
     │  POST /api/export/jmpg      │                           │
     │ ──────────────────────────► │                           │
     │   {content_blocks, meta}    │   POST /api/receipts      │
     │                              │ ────────────────────────► │
     │                              │   ◄──── receipt_id        │
     │                              │                           │
     │   ◄──── .jmpg file          │                           │
     │   (or JSON with base64)     │                           │
     │                              │                           │
     └── User downloads / shares ──┘                           │
```

## Quick Start — Call from Desktop Frontend

```javascript
// In the Desktop React app (:8100)

async function exportAsJMPG() {
  // 1. Collect content from Tiptap editor
  const editor = useEditorStore.getState().editor;
  const contentBlocks = tiptapToJMPGBlocks(editor.getJSON());

  // 2. Call Export Engine
  const response = await fetch('/export/api/export/jmpg', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      title: document.title || 'Untitled',
      author: currentUser.name,
      template: currentISP.template || 'generic',
      content_blocks: contentBlocks,
      metadata: {
        doc_type: currentISP.doc_type || 'COMMUNIQUE',
        impact_level: documentMeta.impact || 'MED',
        department_code: currentISP.department || 'GENERAL',
        language: currentISP.language || 'de',
        tags: documentMeta.tags || [],
        sge_score: sgeResult?.score || null,
        risk_level: sgeResult?.risk || 'R0'
      },
      media: embeddedMedia,       // optional: [{filename, mime_type, data}]
      return_format: 'file'       // 'file' for download, 'json' for programmatic
    })
  });

  // 3. Trigger download
  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const filename = response.headers.get('Content-Disposition')
    ?.match(/filename="(.+)"/)?.[1] || 'communique.jmpg';

  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}
```

## Content Block Format

Convert Tiptap JSON nodes to JMPG blocks:

```javascript
function tiptapToJMPGBlocks(tiptapJSON) {
  const blocks = [];

  for (const node of tiptapJSON.content || []) {
    switch (node.type) {
      case 'heading':
        blocks.push({
          type: 'heading',
          level: node.attrs?.level || 1,
          text: extractText(node)
        });
        break;

      case 'paragraph':
        blocks.push({
          type: 'paragraph',
          text: extractText(node)
        });
        break;

      case 'bulletList':
      case 'orderedList':
        blocks.push({
          type: 'list',
          ordered: node.type === 'orderedList',
          items: node.content?.map(li => extractText(li)) || []
        });
        break;

      case 'blockquote':
        blocks.push({
          type: 'quote',
          text: extractText(node)
        });
        break;

      case 'codeBlock':
        blocks.push({
          type: 'code',
          language: node.attrs?.language || '',
          text: extractText(node)
        });
        break;

      case 'image':
        blocks.push({
          type: 'image',
          src: node.attrs?.src || '',
          alt: node.attrs?.alt || '',
          title: node.attrs?.title || ''
        });
        break;

      case 'horizontalRule':
        blocks.push({ type: 'divider' });
        break;

      case 'table':
        blocks.push({
          type: 'table',
          rows: extractTableRows(node)
        });
        break;
    }
  }

  return blocks;
}

function extractText(node) {
  if (node.text) return node.text;
  if (node.content) return node.content.map(extractText).join('');
  return '';
}
```

## API Endpoints Reference

### POST /api/export/jmpg

Create a .jmpg package.

**Request:**
```json
{
  "title": "Report Title",
  "author": "Author Name",
  "template": "jornaline | field-report | comunicado | pressemitteilung | internal-memo | generic",
  "content_blocks": [
    { "type": "heading", "level": 1, "text": "..." },
    { "type": "paragraph", "text": "..." },
    { "type": "image", "src": "...", "alt": "..." },
    { "type": "quote", "text": "..." },
    { "type": "list", "ordered": false, "items": ["..."] },
    { "type": "table", "rows": [["cell", "cell"], ["cell", "cell"]] },
    { "type": "divider" }
  ],
  "metadata": {
    "doc_type": "COMMUNIQUE",
    "impact_level": "LOW | MED | HIGH | CRIT",
    "department_code": "EDITORIAL",
    "language": "de | en | pt",
    "tags": ["tag1", "tag2"],
    "sge_score": 0.85,
    "risk_level": "R0 | R1 | R2 | R3 | R4 | R5"
  },
  "media": [
    {
      "filename": "photo.jpg",
      "mime_type": "image/jpeg",
      "data": "<base64>"
    }
  ],
  "return_format": "file | json"
}
```

**Response (file):** Binary .jmpg download

**Response (json):**
```json
{
  "success": true,
  "package_id": "JMPG-20260218-A1B2C3D4",
  "content_hash": "abc123...",
  "manifest_hash": "def456...",
  "receipt_id": "REC-...",
  "ledger_registered": true,
  "size_bytes": 1234,
  "elapsed_ms": 45.2,
  "filename": "JMPG-20260218-A1B2C3D4.jmpg",
  "data_base64": "<base64 encoded .jmpg>"
}
```

### POST /api/export/jmpg/preview

Preview hash without creating package or registering with Ledger.

### GET /api/export/spec

Returns format specification.

### GET /api/export/templates

Returns available ISP templates.

### GET /health

Service health check.

## .jmpg Internal Structure

```
JMPG-20260218-A1B2C3D4.jmpg (ZIP)
├── manifest.json      ← package identity, hashes, governance
├── content.json       ← editorial blocks
├── receipt.json       ← Forensic Ledger receipt
└── media/             ← embedded assets
    ├── photo_001.jpg
    └── chart_002.png
```

## Desktop Button Integration

Add to the Desktop toolbar (React):

```jsx
<button
  className="btn-export-jmpg"
  onClick={exportAsJMPG}
  title="Export as Communiqué (.jmpg)"
>
  📰 Export .jmpg
</button>
```

## Nginx Route

The Export Engine is accessible via:
```
https://admin.windia4desk.tech/export/...
```

Nginx proxies `/export/` → `127.0.0.1:8103/`
