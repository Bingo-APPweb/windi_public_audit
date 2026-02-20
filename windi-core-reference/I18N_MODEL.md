# WINDI Internationalization Model

## Design Decision

> **Core uses language-neutral codes. Human-readable messages come from external i18n packs.**

This separation ensures:

1. **Core Neutrality** — Engine code has no language dependencies
2. **Audit Consistency** — Forensic logs store only codes (reproducible)
3. **UI Flexibility** — Any locale can be supported without core changes
4. **Compliance** — Same codes map to local regulatory language

## Supported Locales

| Code | Language | Status |
|------|----------|--------|
| `en` | English | Primary |
| `de` | German | Supported |
| `pt` | Portuguese | Supported |

## Code Categories

### Decision Codes

| Code | EN | DE | PT |
|------|----|----|-----|
| `ALLOW` | Payment allowed | Zahlung erlaubt | Pagamento permitido |
| `HOLD` | Manual review required | Manuelle Prüfung erforderlich | Revisão manual necessária |
| `BLOCK` | Payment blocked | Zahlung gesperrt | Pagamento bloqueado |

### Reason Codes

| Code | EN | DE | PT |
|------|----|----|-----|
| `IBAN_MISMATCH` | IBAN does not match | IBAN stimmt nicht überein | IBAN não corresponde |
| `HIGH_VALUE_LOW_TRUST` | High value with insufficient trust | Hoher Wert mit unzureichendem Vertrauen | Alto valor com confiança insuficiente |
| `ISSUER_UNKNOWN` | Unknown document issuer | Unbekannter Dokumentenaussteller | Emissor desconhecido |
| `DOC_TAMPERED` | Document integrity compromised | Dokumentenintegrität beeinträchtigt | Integridade do documento comprometida |
| `SIGNATURE_INVALID` | Invalid signature | Ungültige Signatur | Assinatura inválida |

### Trust Levels

| Code | EN | DE | PT |
|------|----|----|-----|
| `LOW` | Low trust | Geringes Vertrauen | Confiança baixa |
| `MEDIUM` | Medium trust | Mittleres Vertrauen | Confiança média |
| `HIGH` | High trust | Hohes Vertrauen | Confiança alta |

## Implementation

### Forensics Storage

Events store **only codes**:

```json
{
  "type": "POLICY_DECISION",
  "payload": {
    "decision": "HOLD",
    "reason_codes": ["HIGH_VALUE_LOW_TRUST", "ISSUER_UNKNOWN"]
  }
}
```

### Translation Helper

```javascript
// windi-i18n-pack (future)
const { translate } = require("windi-i18n-pack");

const message = translate("IBAN_MISMATCH", "de");
// → "IBAN stimmt nicht überein"

const messages = translateCodes(["IBAN_MISMATCH", "HIGH_VALUE_LOW_TRUST"], "pt");
// → ["IBAN não corresponde", "Alto valor com confiança insuficiente"]
```

### Express Middleware (Future)

```javascript
const { i18nMiddleware } = require("windi-i18n-pack");

app.use(i18nMiddleware({
  defaultLocale: "en",
  supportedLocales: ["en", "de", "pt"],
  headerName: "Accept-Language"
}));

// In route handler:
res.json({
  decision: result.decision,
  message: req.t(result.decision)
});
```

## UI Integration

### React Example

```jsx
import { useTranslation } from "windi-i18n-pack/react";

function DecisionBadge({ code }) {
  const { t } = useTranslation();
  return <span className={`badge badge-${code.toLowerCase()}`}>{t(code)}</span>;
}
```

### CLI Example

```bash
$ LANG=de wcaf verify bundle.json

╔══════════════════════════════════════════════════╗
║           WCAF Bundle-Verifizierung              ║
╚══════════════════════════════════════════════════╝

Kettenintegrität: ✅ GÜLTIG
```

## Future: windi-i18n-pack

Structure:

```
windi-i18n-pack/
├── locales/
│   ├── en.json
│   ├── de.json
│   └── pt.json
├── src/
│   ├── translate.js
│   ├── middleware.js
│   └── react/
│       └── useTranslation.js
└── index.js
```

## Best Practices

1. **Never hardcode messages** in core components
2. **Always store codes** in forensic logs
3. **Translate at the edge** (API response, UI render)
4. **Include code with message** for debugging
5. **Test all locales** in CI/CD

## Adding a New Locale

1. Create `locales/{code}.json` with all code translations
2. Add to `supportedLocales` array
3. Test with `translateCodes()` for all code categories
4. Update this document
