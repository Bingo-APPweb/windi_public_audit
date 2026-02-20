Fix URGENTE: Clone 1 API calls retornam 404 via Nginx proxy.

## PROBLEMA

O Clone roda em admin.windia4desk.tech/clone/ via Nginx proxy.
O frontend faz fetch('/api/documents') que vai para a RAIZ do domínio (:8086 admin),
não para o Clone (:8095).

## FIX 1: Nginx — adicionar rotas /clone/api/*

Edita /etc/nginx/sites-available/admin.windia4desk.tech

Precisa ter TODAS estas location blocks para o Clone:

```nginx
    # Clone frontend
    location /clone/ {
        proxy_pass http://127.0.0.1:8095/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Clone API proxy (CRITICAL — sem isso dá 404)
    location /clone/api/ {
        proxy_pass http://127.0.0.1:8095/api/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Clone health
    location /clone/health {
        proxy_pass http://127.0.0.1:8095/health;
        proxy_set_header Host $host;
    }

    # Clone static files
    location /clone/static/ {
        proxy_pass http://127.0.0.1:8095/static/;
        proxy_set_header Host $host;
    }
```

Verifica se já existem blocos location com "clone" e SUBSTITUI todos por estes acima.
Os blocos devem ficar DENTRO do server block que tem "listen 443 ssl", ANTES da linha "listen 443 ssl".

Depois:
```bash
sudo nginx -t
sudo systemctl reload nginx
```

## FIX 2: Frontend — detectar base path

Edita /opt/windi/clone-app/static/editor.html

No JavaScript, TODAS as chamadas fetch devem usar base path relativo.
Encontra onde as URLs da API estão definidas e muda para detecção automática:

Procura por algo como:
```javascript
const API_BASE = '/api'
// ou
const HUB_URL = ''
// ou chamadas diretas como
fetch('/api/documents')
fetch('/api/document/' + id)
fetch('/api/chat')
fetch('/api/health')
```

Substitui por:

```javascript
// Detecta base path automaticamente
const BASE_PATH = window.location.pathname.includes('/clone') 
    ? '/clone' 
    : '';
const API = BASE_PATH + '/api';

// Exemplo de uso:
// fetch(API + '/documents')         → /clone/api/documents
// fetch(API + '/document/' + id)    → /clone/api/document/123
// fetch(API + '/chat')              → /clone/api/chat
```

Garante que TODAS as chamadas fetch no arquivo usem API + '/...' em vez de '/api/...'.

Busca TODAS as ocorrências de:
- fetch('/api/
- fetch("/api/
- '/api/
- "/api/
- window.open('/api/
- window.open("/api/

E substitui pela versão com a variável API.

Para export (window.open), mesma lógica:
```javascript
window.open(API + '/document/' + id + '/export/pdf')
```

## FIX 3: Health check no frontend

O frontend provavelmente faz health check assim:
```javascript
fetch('/api/health')
// ou
fetch('/health')
```

Muda para:
```javascript
fetch(BASE_PATH + '/health')
```

## TESTES

```bash
# Nginx OK?
sudo nginx -t

# Clone respondendo?
curl -s http://localhost:8095/health
curl -s http://localhost:8095/api/documents

# Via Nginx proxy?
curl -s https://admin.windia4desk.tech/clone/ | head -5
curl -s https://admin.windia4desk.tech/clone/health
curl -s https://admin.windia4desk.tech/clone/api/documents
```

Todos devem retornar 200 com dados.
