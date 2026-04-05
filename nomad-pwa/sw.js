/**
 * WINDI Nomad PWA — Service Worker
 * §129 PWA Upload · 05 Abril 2026
 *
 * Cache básico para offline fallback.
 * Upload sempre requer conexão (não cached).
 */

const CACHE_NAME = 'windi-nomad-v1';
const CACHE_URLS = [
  '/nomad-upload/',
  '/nomad-upload/manifest.json'
];

// Install — cache static assets
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(CACHE_URLS))
      .then(() => self.skipWaiting())
  );
});

// Activate — clean old caches
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys => {
      return Promise.all(
        keys.filter(key => key !== CACHE_NAME)
            .map(key => caches.delete(key))
      );
    }).then(() => self.clients.claim())
  );
});

// Fetch — network first, cache fallback
self.addEventListener('fetch', event => {
  // Skip non-GET and API calls
  if (event.request.method !== 'GET' ||
      event.request.url.includes('/vd-cut/') ||
      event.request.url.includes('/api/')) {
    return;
  }

  event.respondWith(
    fetch(event.request)
      .catch(() => caches.match(event.request))
  );
});
