# ARCHITECTURE.md — WINDI One Touch
## Detalhes Técnicos de Implementação

---

## 7 Motores — Código de Detecção

### Keywords de Detecção (gen7_gateway.py)

```python
_is_slides = any(kw in _intent_lower for kw in [
    "präsentation", "presentation", "slides", "slide deck",
    "apresentação", "apresentacao", "slide", "pitchdeck", "pitch deck"
])
_is_web = any(kw in _intent_lower for kw in [
    "website", "página web", "pagina web", "landing page",
    "site", "webpage", "microsite", "portfólio web", "portfolio web"
])
_is_art = any(kw in _intent_lower for kw in [
    "poster", "flyer", "capa", "cartaz", "banner",
    "identidade visual", "arte", "design gráfico", "design grafico",
    "ilustração", "ilustracao", "svg"
])
_is_data = any(kw in _intent_lower for kw in [
    "dashboard", "infográfico", "infografico", "gráfico", "grafico",
    "chart", "relatório visual", "relatorio visual", "dados visuais"
])
_is_code = any(kw in _intent_lower for kw in [
    "script", "código", "codigo", "api", "função", "funcao",
    "documentação técnica", "documentacao tecnica", "endpoint", "library"
])
_is_media = any(kw in _intent_lower for kw in [
    "newsletter", "press kit", "social", "instagram", "linkedin",
    "post", "email marketing", "campanha", "comunicado de imprensa"
])
```

### Routing em Cascata

```python
_active_motor = None
_active_prompt = None
if _is_slides:
    _active_motor, _active_prompt = "SLIDES", SLIDES_SYSTEM_PROMPT
elif _is_web:
    _active_motor, _active_prompt = "WEB", WEB_SYSTEM_PROMPT
elif _is_art:
    _active_motor, _active_prompt = "ART", ART_SYSTEM_PROMPT
elif _is_data:
    _active_motor, _active_prompt = "DATA", DATA_SYSTEM_PROMPT
elif _is_code:
    _active_motor, _active_prompt = "CODE", CODE_SYSTEM_PROMPT
elif _is_media:
    _active_motor, _active_prompt = "MEDIA", MEDIA_SYSTEM_PROMPT

if _active_motor and _ANTHROPIC_KEY:
    # Claude directo com system prompt específico
```

### Ledger Logging Dinâmico

```python
_ledger_payload = {
    "id": f"WINDI-{_active_motor}-{session_id}",
    "actor": "gen7-gateway",
    "app": f"canvas-{_active_motor.lower()}",
    "metadata": {
        "training_eligible": True,
        "canvas_type": _active_motor.lower(),
        "model": "claude-sonnet-4-20250514",
    }
}
```

---

## WINDI Web Engine — Endpoints

### POST /api/export/web

```python
Request:
{
    "session_id": "...",
    "html_content": "<h1>...</h1>",
    "sub_type": "micro_page"
}

Response:
{
    "ok": true,
    "receipt_id": "WINDI-WEB-{session_id}",
    "content_hash": "sha256:...",
    "html": "<!DOCTYPE html>...",
    "ledger_sealed": true,
    "verify_url": "https://windi-domain.com/verify-public/?id=..."
}
```

### POST /api/publish/web

```python
Request:
{
    "session_id": "...",
    "html_content": "<h1>...</h1>",
    "title": "Título para OG",
    "description": "Descrição para OG",
    "sub_type": "micro_page"
}

Response:
{
    "ok": true,
    "receipt_id": "WINDI-WEB-{session_id}",
    "hosted_url": "https://windi-domain.com/sites/{receipt_id}/",
    "short_url": "https://windi-domain.com/s/{receipt_id}",
    "whatsapp_url": "https://wa.me/?text=...",
    "ledger_sealed": true,
    "deployed_at": "2026-03-16T..."
}
```

---

## Dispatch Pipeline — Código

### DestinationsModel (Pydantic)

```python
class DestinationsModel(BaseModel):
    email: bool = False
    email_address: Optional[str] = None
    whatsapp: bool = False
    whatsapp_phone: Optional[str] = None
    linkedin: bool = False

class DispatchRequest(BaseModel):
    receipt_id: str
    content_hash: str
    wallet_id: str
    title: Optional[str] = "WINDI Document"
    verify_url: Optional[str] = None
    destinations: Optional[DestinationsModel] = None
```

### Email Sender — Import Directo

```python
# gen7_gateway.py linha 39-45
_sys.path.insert(0, "/opt/windi/agent-palette")
try:
    from email_sender import send_document_email
    EMAIL_AVAILABLE = True
except ImportError:
    EMAIL_AVAILABLE = False
```

### Frontend Integration

```javascript
// /opt/windi/agent-palette/ui/index.html (linha 7285)
const dispatchUrl = 'https://windi-domain.com/desktop/api/onetouch/dispatch';
const res = await fetch(dispatchUrl, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        receipt_id: receipt?.id,
        content_hash: receipt?.ch,
        wallet_id: wallet?.id,
        title: docTitle,
        verify_url: receipt?.verifyUrl,
        destinations: { email: true, whatsapp: false, linkedin: false }
    }),
});
```

---

## nginx Configurations

### VPR Static Pages

```nginx
location /verify-public/vpr/ {
    alias /opt/windi/verify-public/vpr/;
    index index.html;
    try_files $uri $uri/ =404;
    add_header Cache-Control "public, max-age=3600";
    add_header X-WINDI-Service "vpr-static" always;
}

location /verify-public/static/ {
    alias /opt/windi/verify-public/static/;
    add_header Cache-Control "public, max-age=86400";
    add_header X-WINDI-Service "verify-static" always;
}
```

### Microsites Hosting

```nginx
location /sites/ {
    alias /opt/windi/microsites/;
    index index.html;
}

location ~ ^/s/(.+)$ {
    return 301 https://windi-domain.com/sites/$1/;
}
```

### OG Tags Template

```html
<meta property="og:title" content="{title}">
<meta property="og:description" content="{description}">
<meta property="og:url" content="https://windi-domain.com/sites/{id}/">
<meta property="og:image" content=".../dragon-three-seal.svg">
```

---

## GEN 7 Backend Routes

```python
# gen7_gateway.py — serve index.html para TODOS
@app.get("/")
async def root(request: Request):
    """Serve index.html — unified experience for all devices (GEN 7 Canvas)"""
    template_path = STATIC_DIR / "index.html"
    if template_path.exists():
        return FileResponse(template_path)
```

---

## Three Dragons Seal — SVG Design

```
Path: /opt/windi/verify-public/static/dragon-three-seal.svg
Size: 120×120px
Viewbox: 0 0 200 200

Cores:
- Background: #1A1208 (NOIR profundo)
- Outer Ring: #C9A84C (Dragon Gold)
- Guardian: #85B7EB (Azul claro) — Escudo
- Architect: #EF9F27 (Amber) — Compasso
- Witness: #5DCAA5 (Teal) — Olho
```

---

*Detalhes técnicos — ver CLAUDE.md para estado actual e regras*
