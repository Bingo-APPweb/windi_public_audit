/* ═══════════════════════════════════════════════════════════════
   WINDI Verify — Service Worker v1.0.0
   Estratégia: Cache-first para assets estáticos
               Network-first para API calls (:8101, :8091)
               Offline fallback para páginas core
   I9: SW nunca toma decisões de verificação — só serve ficheiros
   ═══════════════════════════════════════════════════════════════ */

const CACHE_NAME    = 'windi-verify-v1.0.0';
const OFFLINE_URL   = '/verify-public/web/offline.html';

/* Assets que entram no cache no install */
const PRECACHE = [
  '/verify-public/web/',
  '/verify-public/web/index.html',
  '/verify-public/web/hash-inspector.html',
  '/verify-public/web/qr-decoder.html',
  '/verify-public/web/offline.html',
  '/verify-public/web/manifest.json',
  '/verify-public/web/icons/icon-192.png',
  '/verify-public/web/icons/icon-512.png',
];

/* Domínios externos — sempre network, nunca cache */
const NETWORK_ONLY = [
  'cdn.jsdelivr.net',        /* jsQR + Tesseract */
  'cdnjs.cloudflare.com',
  'unpkg.com',
];

/* Prefixos de API — network-first com fallback */
const API_PREFIXES = [
  '/verify-public/document/',
  '/verify-public/hash/',
  '/verify-public/qr/',
  '/verify-public/file',
  '/verify-agent/',
  '/api/',
];

// ── INSTALL ───────────────────────────────────────────────────
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(PRECACHE))
      .then(() => self.skipWaiting())
  );
});

// ── ACTIVATE — limpa caches antigas ──────────────────────────
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(
        keys
          .filter(k => k !== CACHE_NAME)
          .map(k => caches.delete(k))
      )
    ).then(() => self.clients.claim())
  );
});

// ── FETCH ─────────────────────────────────────────────────────
self.addEventListener('fetch', event => {
  const { request } = event;
  const url = new URL(request.url);

  /* 1. Só intercepta GET */
  if (request.method !== 'GET') return;

  /* 2. Domínios externos → sempre network */
  if (NETWORK_ONLY.some(d => url.hostname.includes(d))) return;

  /* 3. APIs WINDI → network-first */
  if (API_PREFIXES.some(p => url.pathname.startsWith(p))) {
    event.respondWith(networkFirst(request));
    return;
  }

  /* 4. Assets estáticos → cache-first */
  event.respondWith(cacheFirst(request));
});

/* Cache-first: serve do cache, revalida em background */
async function cacheFirst(request) {
  const cached = await caches.match(request);
  if (cached) {
    /* Revalida em background sem bloquear */
    revalidate(request);
    return cached;
  }
  try {
    const response = await fetch(request);
    if (response.ok) {
      const cache = await caches.open(CACHE_NAME);
      cache.put(request, response.clone());
    }
    return response;
  } catch {
    /* Offline fallback para navegação */
    if (request.destination === 'document') {
      return caches.match(OFFLINE_URL);
    }
    return new Response('Offline', { status: 503 });
  }
}

/* Network-first: tenta rede, cai para cache se offline */
async function networkFirst(request) {
  try {
    const response = await fetch(request);
    if (response.ok) {
      const cache = await caches.open(CACHE_NAME);
      cache.put(request, response.clone());
    }
    return response;
  } catch {
    const cached = await caches.match(request);
    return cached || new Response(
      JSON.stringify({ error: 'offline', message: 'WINDI Verify offline' }),
      { status: 503, headers: { 'Content-Type': 'application/json' } }
    );
  }
}

/* Revalidação silenciosa em background */
async function revalidate(request) {
  try {
    const response = await fetch(request);
    if (response.ok) {
      const cache = await caches.open(CACHE_NAME);
      cache.put(request, response);
    }
  } catch { /* silencioso */ }
}

// ── MESSAGE — força update do SW ─────────────────────────────
self.addEventListener('message', event => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
});
