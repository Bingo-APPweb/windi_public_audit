/**
 * WINDI Surface Guard (WSG) - Service Worker
 * Frontend Constitutional Security Layer
 * 
 * v0.1.1 - HARDENED
 * - Ed25519 manifest signature verification
 * - Anti-replay/downgrade protection
 * - Domain isolation
 * - Performance-optimized hash caching
 * 
 * "Se a interface mente, a soberania humana cai."
 * 
 * @version 0.1.1
 * @author Three Dragons Protocol
 */

const WSG_VERSION = '0.1.2';

// ═══════════════════════════════════════════════════════════════
// DEV MODE - Desabilitar verificação de assinatura para testes
// EM PRODUÇÃO: Mudar para false!
// ═══════════════════════════════════════════════════════════════
const WSG_DEV_MODE = true;

// ═══════════════════════════════════════════════════════════════
// PINNED PUBLIC KEY (Ed25519)
// Em produção: gerar par de chaves e embutir pubkey aqui
// ═══════════════════════════════════════════════════════════════

const PINNED_PUBLIC_KEY = {
  // Base64-encoded Ed25519 public key
  // Generated: 2026-02-04T15:03:57.764Z
  key: 'MCowBQYDK2VwAyEAAS0KHUjSsO+WlwaSBm/t31gkzQ5BdsO04E1xkRf41vM=',
  algorithm: { name: 'Ed25519' },
  format: 'spki'
};

// ═══════════════════════════════════════════════════════════════
// CONFIGURATION - HARDENED
// ═══════════════════════════════════════════════════════════════

const WSG_CONFIG = {
  manifestUrl: '/api/wsg/virtue-manifest.json',
  violationEndpoint: '/api/wsg/violation',
  
  // Domínios WINDI (isolamento)
  domains: {
    institutional: { paths: ['/institutional/', '/epapers/'], csp: 'strict' },
    industrial: { paths: ['/industrial/', '/isp/'], csp: 'strict' },
    operational: { paths: ['/ops/', '/babel/'], csp: 'standard' },
    forensic: { paths: ['/ledger/', '/audit/'], csp: 'strict' }
  },
  
  // Paths protegidos por domínio
  protectedPaths: ['/js/', '/css/', '/components/', '/modules/'],
  
  // Assets externos permitidos (não verificados)
  trustedExternals: [
    'https://fonts.googleapis.com',
    'https://fonts.gstatic.com',
    'https://cdnjs.cloudflare.com'
  ],
  
  // Níveis de integridade
  integrityLevels: {
    CRITICAL: { block: true, alert: true, report: true, allowInline: false },
    HIGH: { block: true, alert: false, report: true, allowInline: false },
    STANDARD: { block: false, alert: false, report: true, allowInline: true },
    LOW: { block: false, alert: false, report: false, allowInline: true }
  },
  
  // Manifest rolling window (aceita N-1 para tolerância)
  manifestRollingWindow: 2,
  
  // Cache TTL para hashes verificados (5 min)
  verifiedHashCacheTTL: 300000,
  
  // Headers
  headers: {
    virtueHash: 'X-WINDI-Virtue-Hash',
    integrityLevel: 'X-WINDI-Integrity-Level',
    domain: 'X-WINDI-Domain',
    manifestVersion: 'X-WINDI-Manifest-Version',
    buildId: 'X-WINDI-Build-ID'
  }
};

// ═══════════════════════════════════════════════════════════════
// STATE
// ═══════════════════════════════════════════════════════════════

const state = {
  manifest: null,
  manifestHistory: [], // Para anti-replay
  verifiedHashes: new Map(), // Cache: url+etag → { hash, timestamp }
  currentDomain: null,
  publicKey: null
};

// ═══════════════════════════════════════════════════════════════
// ED25519 SIGNATURE VERIFICATION
// ═══════════════════════════════════════════════════════════════

/**
 * Importa chave pública Ed25519 pinada
 */
async function importPublicKey() {
  if (state.publicKey) return state.publicKey;
  
  try {
    const keyData = Uint8Array.from(atob(PINNED_PUBLIC_KEY.key), c => c.charCodeAt(0));
    
    state.publicKey = await crypto.subtle.importKey(
      PINNED_PUBLIC_KEY.format,
      keyData,
      PINNED_PUBLIC_KEY.algorithm,
      false,
      ['verify']
    );
    
    return state.publicKey;
  } catch (error) {
    console.error('[WSG] Failed to import public key:', error);
    return null;
  }
}

/**
 * Verifica assinatura Ed25519 do manifesto
 */
async function verifyManifestSignature(manifest, signatureB64) {
  const publicKey = await importPublicKey();
  if (!publicKey) {
    console.error('[WSG] No public key available');
    return false;
  }
  
  try {
    // Reconstruir payload assinado (sem o campo signature)
    const { signature, ...payloadWithoutSig } = manifest;
    const payload = JSON.stringify(payloadWithoutSig, Object.keys(payloadWithoutSig).sort());
    const payloadBytes = new TextEncoder().encode(payload);
    
    // Decodificar assinatura
    const signatureBytes = Uint8Array.from(atob(signatureB64), c => c.charCodeAt(0));
    
    // Verificar
    const valid = await crypto.subtle.verify(
      PINNED_PUBLIC_KEY.algorithm,
      publicKey,
      signatureBytes,
      payloadBytes
    );
    
    return valid;
  } catch (error) {
    console.error('[WSG] Signature verification failed:', error);
    return false;
  }
}

// ═══════════════════════════════════════════════════════════════
// ANTI-REPLAY / ANTI-DOWNGRADE
// ═══════════════════════════════════════════════════════════════

/**
 * Valida manifesto contra replay/downgrade
 */
function validateManifestFreshness(manifest) {
  const now = Date.now();
  const notBefore = new Date(manifest.not_before).getTime();
  const expiresAt = new Date(manifest.expires_at).getTime();
  
  // Verificar janela de validade
  if (now < notBefore) {
    return { valid: false, reason: 'MANIFEST_NOT_YET_VALID' };
  }
  
  if (now > expiresAt) {
    return { valid: false, reason: 'MANIFEST_EXPIRED' };
  }
  
  // Verificar build_id monotônico
  if (state.manifest && manifest.build_id <= state.manifest.build_id) {
    // Permitir rolling window
    const isInWindow = state.manifestHistory.some(
      m => m.build_id === manifest.build_id
    );
    
    if (!isInWindow) {
      return { valid: false, reason: 'MANIFEST_DOWNGRADE_ATTEMPT' };
    }
  }
  
  // Verificar hash chain (previous_manifest_hash)
  if (state.manifest && manifest.previous_manifest_hash) {
    const expectedPrevHash = state.manifest.manifest_hash;
    if (manifest.previous_manifest_hash !== expectedPrevHash) {
      // Pode ser legítimo se pulou versões, apenas log
      console.warn('[WSG] Manifest chain break detected');
    }
  }
  
  return { valid: true };
}

/**
 * Atualiza histórico de manifestos (rolling window)
 */
function updateManifestHistory(manifest) {
  state.manifestHistory.unshift(manifest);
  
  // Manter apenas N manifestos
  if (state.manifestHistory.length > WSG_CONFIG.manifestRollingWindow) {
    state.manifestHistory.pop();
  }
}

// ═══════════════════════════════════════════════════════════════
// MANIFEST LOADING
// ═══════════════════════════════════════════════════════════════

/**
 * Carrega e valida Virtue Manifest
 */
async function loadVirtueManifest() {
  try {
    const response = await fetch(WSG_CONFIG.manifestUrl, {
      cache: 'no-store' // Sempre buscar fresh
    });
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    
    const manifest = await response.json();
    
    // 1. Verificar assinatura Ed25519
    // DEV_MODE: Pular verificação de assinatura
    if (WSG_DEV_MODE) {
      console.warn('[WSG] ⚠️ DEV_MODE: Signature verification SKIPPED');
    } else {
      const signatureValid = await verifyManifestSignature(manifest, manifest.signature);
      if (!signatureValid) {
        throw new Error('INVALID_MANIFEST_SIGNATURE');
      }
    }
    
    // 2. Verificar freshness (anti-replay)
    const freshness = validateManifestFreshness(manifest);
    if (!freshness.valid) {
      throw new Error(freshness.reason);
    }
    
    // 3. Aceitar manifesto
    state.manifest = manifest;
    updateManifestHistory(manifest);
    
    // 4. Limpar cache de hashes verificados (novo manifesto)
    state.verifiedHashes.clear();
    
    console.log(`[WSG] ✓ Manifest loaded: build ${manifest.build_id}, expires ${manifest.expires_at}`);
    return true;
    
  } catch (error) {
    console.error('[WSG] Failed to load manifest:', error.message);
    
    // Reportar violação
    await reportViolation({
      type: 'MANIFEST_LOAD_FAILURE',
      reason: error.message
    });
    
    return false;
  }
}

// ═══════════════════════════════════════════════════════════════
// DOMAIN ISOLATION
// ═══════════════════════════════════════════════════════════════

/**
 * Detecta domínio WINDI da URL
 */
function detectDomain(url) {
  const urlObj = new URL(url);
  
  for (const [domain, config] of Object.entries(WSG_CONFIG.domains)) {
    for (const pathPrefix of config.paths) {
      if (urlObj.pathname.startsWith(pathPrefix)) {
        return domain;
      }
    }
  }
  
  return 'operational'; // Default
}

/**
 * Verifica se request está tentando cross-domain
 */
function isCrossDomainViolation(request) {
  const requestDomain = detectDomain(request.url);
  const referrerDomain = request.referrer ? detectDomain(request.referrer) : null;
  
  // Se há referrer de outro domínio WINDI, é violação
  if (referrerDomain && referrerDomain !== requestDomain) {
    // Exceção: assets compartilhados (fonts, etc)
    const isSharedAsset = /\.(woff2?|ttf|eot)$/.test(request.url);
    if (!isSharedAsset) {
      return {
        violation: true,
        from: referrerDomain,
        to: requestDomain
      };
    }
  }
  
  return { violation: false };
}

/**
 * Retorna nome do cache por domínio
 */
function getCacheName(domain) {
  const version = state.manifest?.build_id || WSG_VERSION;
  return `wsg-${domain}-v${version}`;
}

// ═══════════════════════════════════════════════════════════════
// HASH VERIFICATION (Performance Optimized)
// ═══════════════════════════════════════════════════════════════

/**
 * Calcula SHA-256 com streaming (para assets grandes)
 */
async function calculateHashStreaming(response) {
  const reader = response.body.getReader();
  const chunks = [];
  
  // Ler todos os chunks
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    chunks.push(value);
  }
  
  // Concatenar
  const totalLength = chunks.reduce((acc, chunk) => acc + chunk.length, 0);
  const buffer = new Uint8Array(totalLength);
  let offset = 0;
  for (const chunk of chunks) {
    buffer.set(chunk, offset);
    offset += chunk.length;
  }
  
  // Hash
  const hashBuffer = await crypto.subtle.digest('SHA-256', buffer);
  const hashArray = Array.from(new Uint8Array(hashBuffer));
  const hashHex = hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
  
  // Retornar hash e body reconstruído
  return {
    hash: `sha256-${hashHex}`,
    body: buffer
  };
}

/**
 * Verifica se hash está em cache (url + etag)
 */
function getCachedVerification(url, etag) {
  const key = `${url}|${etag}`;
  const cached = state.verifiedHashes.get(key);
  
  if (cached && (Date.now() - cached.timestamp) < WSG_CONFIG.verifiedHashCacheTTL) {
    return cached;
  }
  
  return null;
}

/**
 * Armazena verificação em cache
 */
function cacheVerification(url, etag, hash, valid) {
  const key = `${url}|${etag}`;
  state.verifiedHashes.set(key, {
    hash,
    valid,
    timestamp: Date.now()
  });
}

// ═══════════════════════════════════════════════════════════════
// CSP INJECTION (Hardened)
// ═══════════════════════════════════════════════════════════════

/**
 * Retorna CSP hardened baseado no scope
 */
function getHardenedCSP(integrityLevel, domain) {
  const domainConfig = WSG_CONFIG.domains[domain];
  const levelConfig = WSG_CONFIG.integrityLevels[integrityLevel];
  
  // Base CSP (sempre)
  const base = [
    "default-src 'self'",
    "base-uri 'self'",
    "form-action 'self'",
    "frame-ancestors 'none'",
    "upgrade-insecure-requests"
  ];
  
  // Script-src: NUNCA inline em CRITICAL/HIGH
  if (levelConfig.allowInline) {
    base.push("script-src 'self' 'wasm-unsafe-eval'");
  } else {
    base.push("script-src 'self'"); // Zero inline
  }
  
  // Style-src: preferir sem inline, mas permitir em STANDARD/LOW
  if (levelConfig.allowInline) {
    base.push("style-src 'self' 'unsafe-inline'"); // Transição
  } else {
    base.push("style-src 'self'"); // Hardened
  }
  
  // Outros
  base.push("img-src 'self' data: https:");
  base.push("font-src 'self' https://fonts.gstatic.com");
  base.push("connect-src 'self'");
  
  return base.join('; ');
}

// ═══════════════════════════════════════════════════════════════
// VIOLATION REPORTING
// ═══════════════════════════════════════════════════════════════

/**
 * Cria receipt de violação com hash chain
 */
function createViolationReceipt(type, details) {
  const receipt = {
    receipt_type: 'SURFACE_VIOLATION',
    receipt_id: `WSG-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
    timestamp: new Date().toISOString(),
    wsg_version: WSG_VERSION,
    manifest_build_id: state.manifest?.build_id || null,
    
    violation: {
      type,
      ...details
    },
    
    context: {
      domain: state.currentDomain,
      user_agent: navigator.userAgent,
      online: navigator.onLine
    }
  };
  
  // Hash chain: incluir hash do receipt anterior (se houver)
  // Em produção: manter em IndexedDB
  receipt.previous_receipt_hash = null; // TODO: implementar chain
  
  return receipt;
}

/**
 * Envia violação para ledger
 */
async function reportViolation(details) {
  const receipt = createViolationReceipt(details.type, details);
  
  try {
    await fetch(WSG_CONFIG.violationEndpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(receipt)
    });
  } catch (error) {
    // Armazenar para sync posterior
    console.error('[WSG] Failed to report violation:', error);
  }
  
  console.warn('[WSG] 🚨 VIOLATION:', receipt);
  return receipt;
}

// ═══════════════════════════════════════════════════════════════
// BLOCKED RESPONSE (Kill Switch)
// ═══════════════════════════════════════════════════════════════

/**
 * Página de ambiente comprometido (Kill Switch)
 */
function createCompromisedEnvironmentPage(violation) {
  const html = `<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>WSG - Ambiente Comprometido</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
      font-family: system-ui, -apple-system, sans-serif;
      background: linear-gradient(135deg, #1a1a2e 0%, #0f0f1a 100%);
      color: #e0e0e0;
      min-height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 20px;
    }
    .container {
      max-width: 560px;
      text-align: center;
    }
    .shield {
      font-size: 80px;
      margin-bottom: 24px;
      animation: pulse 2s ease-in-out infinite;
    }
    @keyframes pulse {
      0%, 100% { transform: scale(1); opacity: 1; }
      50% { transform: scale(1.05); opacity: 0.8; }
    }
    h1 {
      color: #ff4757;
      font-size: 28px;
      margin-bottom: 16px;
      font-weight: 600;
    }
    .message {
      font-size: 16px;
      line-height: 1.6;
      color: #a0a0a0;
      margin-bottom: 24px;
    }
    .violation-box {
      background: rgba(255, 71, 87, 0.1);
      border: 1px solid rgba(255, 71, 87, 0.3);
      border-radius: 12px;
      padding: 20px;
      margin-bottom: 24px;
      text-align: left;
    }
    .violation-type {
      color: #ff4757;
      font-weight: 600;
      font-size: 14px;
      margin-bottom: 8px;
    }
    .violation-detail {
      font-family: monospace;
      font-size: 12px;
      color: #888;
      word-break: break-all;
    }
    .warning {
      background: rgba(255, 193, 7, 0.1);
      border: 1px solid rgba(255, 193, 7, 0.3);
      border-radius: 8px;
      padding: 16px;
      font-size: 14px;
      color: #ffc107;
      margin-bottom: 24px;
    }
    .badge {
      display: inline-block;
      background: rgba(255,255,255,0.05);
      padding: 8px 16px;
      border-radius: 20px;
      font-size: 12px;
      color: #666;
    }
    button {
      background: #3b82f6;
      color: white;
      border: none;
      padding: 12px 24px;
      border-radius: 8px;
      font-size: 14px;
      cursor: pointer;
      margin-top: 16px;
    }
    button:hover { background: #2563eb; }
  </style>
</head>
<body>
  <div class="container">
    <div class="shield">🛡️</div>
    <h1>Ambiente Comprometido</h1>
    <p class="message">
      O WINDI Surface Guard detectou uma modificação não autorizada em um componente crítico de decisão.
      <strong>Nenhuma ação de governança deve ser tomada neste ambiente.</strong>
    </p>
    
    <div class="violation-box">
      <div class="violation-type">${violation.type}</div>
      <div class="violation-detail">${violation.asset || 'N/A'}</div>
      ${violation.expected_hash ? `<div class="violation-detail">Esperado: ${violation.expected_hash.substring(0, 32)}...</div>` : ''}
      ${violation.received_hash ? `<div class="violation-detail">Recebido: ${violation.received_hash.substring(0, 32)}...</div>` : ''}
    </div>
    
    <div class="warning">
      ⚠️ Esta violação foi registrada no Forensic Ledger. Não tente recarregar a página ou prosseguir com decisões até que a integridade seja restaurada.
    </div>
    
    <button onclick="window.location.reload()">Tentar Novamente</button>
    
    <div style="margin-top: 24px;">
      <span class="badge">WSG v${WSG_VERSION} • Frontend Constitutional Security Layer</span>
    </div>
  </div>
</body>
</html>`;

  return new Response(html, {
    status: 403,
    headers: {
      'Content-Type': 'text/html; charset=utf-8',
      'X-WSG-Blocked': 'true',
      'X-WSG-Violation': violation.type
    }
  });
}

// ═══════════════════════════════════════════════════════════════
// MAIN VERIFICATION
// ═══════════════════════════════════════════════════════════════

/**
 * Verifica integridade de um asset
 */
async function verifyAssetIntegrity(request, response) {
  const url = request.url;
  const etag = response.headers.get('ETag') || '';
  
  // 1. Verificar cross-domain
  const crossDomain = isCrossDomainViolation(request);
  if (crossDomain.violation) {
    await reportViolation({
      type: 'CROSS_DOMAIN_VIOLATION',
      from_domain: crossDomain.from,
      to_domain: crossDomain.to,
      asset: url
    });
    return createCompromisedEnvironmentPage({
      type: 'CROSS_DOMAIN_VIOLATION',
      asset: url
    });
  }
  
  // 2. Extrair headers
  const serverHash = response.headers.get(WSG_CONFIG.headers.virtueHash);
  const integrityLevel = response.headers.get(WSG_CONFIG.headers.integrityLevel) || 'STANDARD';
  const domain = response.headers.get(WSG_CONFIG.headers.domain) || detectDomain(url);
  
  state.currentDomain = domain;
  
  // 3. Verificar se tem hash esperado
  if (!serverHash) {
    // Asset sem hash - verificar se deveria ter
    const isProtected = WSG_CONFIG.protectedPaths.some(p => new URL(url).pathname.startsWith(p));
    if (isProtected) {
      await reportViolation({
        type: 'MISSING_VIRTUE_HASH',
        asset: url,
        integrity_level: integrityLevel
      });
      
      const config = WSG_CONFIG.integrityLevels[integrityLevel];
      if (config.block) {
        return createCompromisedEnvironmentPage({
          type: 'MISSING_VIRTUE_HASH',
          asset: url
        });
      }
    }
    return response;
  }
  
  // 4. Verificar cache de verificações anteriores
  const cached = getCachedVerification(url, etag);
  if (cached && cached.valid) {
    console.log(`[WSG] ✓ Cache hit: ${new URL(url).pathname}`);
    return response;
  }
  
  // 5. Calcular hash local (streaming para performance)
  const clonedResponse = response.clone();
  const { hash: localHash, body } = await calculateHashStreaming(clonedResponse);
  
  // 6. Comparar hashes
  if (localHash !== serverHash) {
    await reportViolation({
      type: 'HASH_MISMATCH',
      asset: url,
      expected_hash: serverHash,
      received_hash: localHash,
      integrity_level: integrityLevel,
      domain: domain
    });
    
    cacheVerification(url, etag, localHash, false);
    
    const config = WSG_CONFIG.integrityLevels[integrityLevel];
    if (config.block) {
      return createCompromisedEnvironmentPage({
        type: 'HASH_MISMATCH',
        asset: url,
        expected_hash: serverHash,
        received_hash: localHash
      });
    }
  }
  
  // 7. Hash válido - cachear e retornar
  cacheVerification(url, etag, localHash, true);
  console.log(`[WSG] ✓ Verified: ${new URL(url).pathname}`);
  
  // Reconstruir response com body já lido
  return new Response(body, {
    status: response.status,
    statusText: response.statusText,
    headers: response.headers
  });
}

// ═══════════════════════════════════════════════════════════════
// SCOPE DETECTION
// ═══════════════════════════════════════════════════════════════

function isInProtectedScope(url) {
  const urlObj = new URL(url);
  
  // Assets externos de confiança
  for (const trusted of WSG_CONFIG.trustedExternals) {
    if (url.startsWith(trusted)) return false;
  }
  
  // Paths protegidos
  for (const path of WSG_CONFIG.protectedPaths) {
    if (urlObj.pathname.startsWith(path)) return true;
  }
  
  return false;
}

// ═══════════════════════════════════════════════════════════════
// SERVICE WORKER EVENTS
// ═══════════════════════════════════════════════════════════════

self.addEventListener('install', (event) => {
  console.log(`[WSG] Installing Surface Guard v${WSG_VERSION}`);
  
  event.waitUntil(
    loadVirtueManifest().then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (event) => {
  console.log('[WSG] Activating Surface Guard');
  
  event.waitUntil(
    // Limpar caches de outras versões/domínios antigos
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames
          .filter(name => name.startsWith('wsg-') && !name.includes(WSG_VERSION))
          .map(name => caches.delete(name))
      );
    }).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (event) => {
  const request = event.request;
  
  // Apenas GET
  if (request.method !== 'GET') return;
  
  // Verificar escopo
  if (!isInProtectedScope(request.url)) return;
  
  event.respondWith(
    fetch(request)
      .then(response => verifyAssetIntegrity(request, response))
      .catch(error => {
        console.error('[WSG] Fetch error:', error);
        return createCompromisedEnvironmentPage({
          type: 'FETCH_ERROR',
          asset: request.url,
          error: error.message
        });
      })
  );
});

self.addEventListener('message', (event) => {
  const { type, payload } = event.data || {};
  
  switch (type) {
    case 'WSG_GET_STATUS':
      event.ports[0]?.postMessage({
        version: WSG_VERSION,
        manifestLoaded: !!state.manifest,
        manifestBuildId: state.manifest?.build_id,
        currentDomain: state.currentDomain,
        verifiedHashCount: state.verifiedHashes.size
      });
      break;
      
    case 'WSG_RELOAD_MANIFEST':
      loadVirtueManifest().then(success => {
        event.ports[0]?.postMessage({ success });
      });
      break;
      
    case 'WSG_REPORT_DOM_VIOLATION':
      reportViolation({ type: 'DOM_MUTATION', ...payload });
      break;
  }
});

console.log(`[WSG] 🛡️ WINDI Surface Guard v${WSG_VERSION} - Frontend Constitutional Security Layer`);
