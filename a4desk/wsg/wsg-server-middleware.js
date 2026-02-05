/**
 * WINDI Surface Guard (WSG) - Server Middleware
 * Certificação de Virtude dos Assets - HARDENED
 * 
 * v0.1.1 - Com assinatura Ed25519 e anti-replay
 * 
 * "O servidor não entrega arquivos. Entrega Promessas Assinadas."
 * 
 * @version 0.1.1
 * @author Three Dragons Protocol
 */

const crypto = require('crypto');
const fs = require('fs');
const path = require('path');

// ═══════════════════════════════════════════════════════════════
// ED25519 KEY MANAGEMENT
// ═══════════════════════════════════════════════════════════════

/**
 * Gera par de chaves Ed25519 (usar apenas uma vez em setup)
 */
function generateKeyPair() {
  const { publicKey, privateKey } = crypto.generateKeyPairSync('ed25519', {
    publicKeyEncoding: { type: 'spki', format: 'der' },
    privateKeyEncoding: { type: 'pkcs8', format: 'der' }
  });
  
  return {
    publicKey: publicKey.toString('base64'),
    privateKey: privateKey.toString('base64')
  };
}

/**
 * Assina dados com chave privada Ed25519
 */
function signData(data, privateKeyBase64) {
  const privateKeyDer = Buffer.from(privateKeyBase64, 'base64');
  const privateKey = crypto.createPrivateKey({
    key: privateKeyDer,
    format: 'der',
    type: 'pkcs8'
  });
  
  const signature = crypto.sign(null, Buffer.from(data), privateKey);
  return signature.toString('base64');
}

// ═══════════════════════════════════════════════════════════════
// CONFIGURATION - HARDENED
// ═══════════════════════════════════════════════════════════════

const WSG_CONFIG = {
  // Diretórios de assets
  assetDirectories: ['/js', '/css', '/components', '/modules'],
  
  // Extensões certificadas
  certifiedExtensions: ['.js', '.css', '.html', '.mjs'],
  
  // Domínios WINDI (para header X-WINDI-Domain)
  domains: {
    institutional: { paths: ['/institutional/', '/epapers/'] },
    industrial: { paths: ['/industrial/', '/isp/'] },
    operational: { paths: ['/ops/', '/babel/'] },
    forensic: { paths: ['/ledger/', '/audit/'] }
  },
  
  // Níveis de integridade por padrão
  integrityPatterns: [
    { pattern: /decisao|governance|approval|reject/i, level: 'CRITICAL' },
    { pattern: /sge|risk|validation/i, level: 'CRITICAL' },
    { pattern: /auth|login|session/i, level: 'HIGH' },
    { pattern: /main|app|index/i, level: 'HIGH' },
    { pattern: /theme|style|layout/i, level: 'STANDARD' },
    { pattern: /.*/, level: 'STANDARD' }
  ],
  
  // Validade do manifesto
  manifestTTL: 3600000, // 1 hora
  
  // Chave privada (em produção: variável de ambiente ou HSM)
  privateKey: process.env.WSG_PRIVATE_KEY || null,
  
  // Build ID inicial (deve ser persistido e incrementado)
  buildIdFile: '.wsg-build-id'
};

// ═══════════════════════════════════════════════════════════════
// BUILD ID MANAGEMENT (Monotônico)
// ═══════════════════════════════════════════════════════════════

let currentBuildId = 1;

function loadBuildId(staticDir) {
  const buildIdPath = path.join(staticDir, WSG_CONFIG.buildIdFile);
  try {
    if (fs.existsSync(buildIdPath)) {
      currentBuildId = parseInt(fs.readFileSync(buildIdPath, 'utf8'), 10) || 1;
    }
  } catch (e) {
    currentBuildId = 1;
  }
  return currentBuildId;
}

function incrementBuildId(staticDir) {
  currentBuildId++;
  const buildIdPath = path.join(staticDir, WSG_CONFIG.buildIdFile);
  try {
    fs.writeFileSync(buildIdPath, String(currentBuildId));
  } catch (e) {
    console.error('[WSG] Failed to persist build ID');
  }
  return currentBuildId;
}

// ═══════════════════════════════════════════════════════════════
// HASH CACHE
// ═══════════════════════════════════════════════════════════════

class VirtueHashCache {
  constructor() {
    this.cache = new Map();
    this.lastManifest = null;
    this.previousManifestHash = null;
  }
  
  calculateHash(buffer) {
    return `sha256-${crypto.createHash('sha256').update(buffer).digest('hex')}`;
  }
  
  getHash(filePath) {
    const cached = this.cache.get(filePath);
    const stats = fs.statSync(filePath);
    
    // Verificar se cache ainda válido
    if (cached && cached.mtime === stats.mtime.toISOString()) {
      return cached;
    }
    
    // Calcular novo
    try {
      const content = fs.readFileSync(filePath);
      const hash = this.calculateHash(content);
      const integrityLevel = this.determineIntegrityLevel(filePath);
      const domain = this.determineDomain(filePath);
      
      const entry = {
        hash,
        size: stats.size,
        mtime: stats.mtime.toISOString(),
        integrityLevel,
        domain,
        scope: this.determineScope(filePath)
      };
      
      this.cache.set(filePath, entry);
      return entry;
    } catch (error) {
      console.error(`[WSG] Error hashing ${filePath}:`, error.message);
      return null;
    }
  }
  
  determineIntegrityLevel(filePath) {
    const filename = path.basename(filePath);
    for (const { pattern, level } of WSG_CONFIG.integrityPatterns) {
      if (pattern.test(filename)) return level;
    }
    return 'STANDARD';
  }
  
  determineDomain(filePath) {
    for (const [domain, config] of Object.entries(WSG_CONFIG.domains)) {
      for (const pathPrefix of config.paths) {
        if (filePath.includes(pathPrefix.replace(/\//g, path.sep))) {
          return domain;
        }
      }
    }
    return 'operational';
  }
  
  determineScope(filePath) {
    if (/governance|decisao|approval/i.test(filePath)) return 'governance-decision';
    if (/sge|risk|validation/i.test(filePath)) return 'risk-assessment';
    if (/auth|login|session/i.test(filePath)) return 'authentication';
    if (/css|style|theme/i.test(filePath)) return 'visual-presentation';
    return 'general';
  }
  
  /**
   * Gera Virtue Manifest ASSINADO com anti-replay
   */
  generateManifest(staticDir, privateKey) {
    const now = new Date();
    const expiresAt = new Date(now.getTime() + WSG_CONFIG.manifestTTL);
    const buildId = incrementBuildId(staticDir);
    
    // Coletar assets
    const assets = {};
    for (const assetDir of WSG_CONFIG.assetDirectories) {
      const fullPath = path.join(staticDir, assetDir);
      if (fs.existsSync(fullPath)) {
        this.scanDirectory(fullPath, staticDir, assets);
      }
    }
    
    // Construir manifesto (sem assinatura ainda)
    const manifest = {
      version: '1.1.0',
      generated: now.toISOString(),
      signer: 'WINDI-BABEL-API',
      
      // Anti-replay fields
      build_id: buildId,
      not_before: now.toISOString(),
      expires_at: expiresAt.toISOString(),
      previous_manifest_hash: this.previousManifestHash,
      
      // Assets
      assets
    };
    
    // Calcular hash do manifesto (para chain)
    const manifestString = JSON.stringify(manifest, Object.keys(manifest).sort());
    const manifestHash = crypto.createHash('sha256').update(manifestString).digest('hex');
    manifest.manifest_hash = `sha256-${manifestHash}`;
    
    // Assinar com Ed25519
    if (privateKey) {
      manifest.signature = signData(manifestString, privateKey);
      manifest.signature_algorithm = 'Ed25519';
    } else {
      // Dev mode: assinatura placeholder
      manifest.signature = `DEV-SIG-${manifestHash.substring(0, 32)}`;
      manifest.signature_algorithm = 'none';
      console.warn('[WSG] ⚠️ Running without Ed25519 signature (dev mode)');
    }
    
    // Atualizar state
    this.previousManifestHash = manifest.manifest_hash;
    this.lastManifest = manifest;
    
    return manifest;
  }
  
  scanDirectory(dir, baseDir, assets) {
    const entries = fs.readdirSync(dir, { withFileTypes: true });
    
    for (const entry of entries) {
      const fullPath = path.join(dir, entry.name);
      
      if (entry.isDirectory()) {
        this.scanDirectory(fullPath, baseDir, assets);
      } else if (entry.isFile()) {
        const ext = path.extname(entry.name);
        if (WSG_CONFIG.certifiedExtensions.includes(ext)) {
          const relativePath = '/' + path.relative(baseDir, fullPath).replace(/\\/g, '/');
          const hashEntry = this.getHash(fullPath);
          
          if (hashEntry) {
            assets[relativePath] = {
              hash: hashEntry.hash,
              size: hashEntry.size,
              integrity: hashEntry.integrityLevel,
              domain: hashEntry.domain,
              scope: hashEntry.scope
            };
          }
        }
      }
    }
  }
  
  invalidate(filePath) {
    this.cache.delete(filePath);
  }
  
  clear() {
    this.cache.clear();
  }
}

const virtueCache = new VirtueHashCache();

// ═══════════════════════════════════════════════════════════════
// CSP POLICIES (Hardened por scope)
// ═══════════════════════════════════════════════════════════════

const CSP_POLICIES = {
  // CRITICAL/HIGH: Zero inline
  strict: [
    "default-src 'self'",
    "script-src 'self'",  // NO unsafe-inline, NO unsafe-eval
    "style-src 'self'",   // NO unsafe-inline
    "img-src 'self' data: https:",
    "font-src 'self' https://fonts.gstatic.com",
    "connect-src 'self'",
    "frame-ancestors 'none'",
    "base-uri 'self'",
    "form-action 'self'",
    "upgrade-insecure-requests"
  ].join('; '),
  
  // STANDARD: Transição (permitir inline com warning)
  standard: [
    "default-src 'self'",
    "script-src 'self' 'wasm-unsafe-eval'",
    "style-src 'self' 'unsafe-inline'", // Transição
    "img-src 'self' data: https:",
    "font-src 'self' https://fonts.gstatic.com",
    "connect-src 'self'",
    "frame-ancestors 'none'",
    "base-uri 'self'",
    "form-action 'self'"
  ].join('; ')
};

function getCSPForLevel(integrityLevel) {
  if (integrityLevel === 'CRITICAL' || integrityLevel === 'HIGH') {
    return CSP_POLICIES.strict;
  }
  return CSP_POLICIES.standard;
}

// ═══════════════════════════════════════════════════════════════
// EXPRESS MIDDLEWARE
// ═══════════════════════════════════════════════════════════════

/**
 * Middleware que adiciona Virtue Headers
 */
function wsgMiddleware(staticDir, options = {}) {
  const { privateKey } = options;
  
  // Carregar build ID
  loadBuildId(staticDir);
  
  return function(req, res, next) {
    const ext = path.extname(req.path);
    if (!WSG_CONFIG.certifiedExtensions.includes(ext)) {
      return next();
    }
    
    const isProtected = WSG_CONFIG.assetDirectories.some(
      dir => req.path.startsWith(dir)
    );
    
    if (!isProtected) {
      return next();
    }
    
    const filePath = path.join(staticDir, req.path);
    const hashEntry = virtueCache.getHash(filePath);
    
    if (hashEntry) {
      // Virtue Headers
      res.set('X-WINDI-Virtue-Hash', hashEntry.hash);
      res.set('X-WINDI-Integrity-Level', hashEntry.integrityLevel);
      res.set('X-WINDI-Domain', hashEntry.domain);
      res.set('X-WINDI-Asset-Scope', hashEntry.scope);
      res.set('X-WINDI-Build-ID', String(currentBuildId));
      res.set('X-WINDI-Manifest-Version', '1.1.0');
      
      // CSP baseado no nível
      res.set('Content-Security-Policy', getCSPForLevel(hashEntry.integrityLevel));
      
      // Cache headers
      res.set('ETag', `"${hashEntry.hash.substring(7, 23)}"`);
      res.set('Cache-Control', 'public, max-age=300, must-revalidate');
    }
    
    next();
  };
}

/**
 * Rota do Virtue Manifest
 */
function virtueManifestRoute(staticDir, options = {}) {
  const { privateKey } = options;
  
  return function(req, res) {
    const manifest = virtueCache.generateManifest(staticDir, privateKey);
    
    // Headers de controle
    res.set('Cache-Control', 'no-store, must-revalidate');
    res.set('X-WINDI-Build-ID', String(manifest.build_id));
    
    res.json(manifest);
  };
}

/**
 * Rota de violações (com hash chain support)
 */
function violationReportRoute(options = {}) {
  const { ledgerCallback, receiptStore } = options;
  const receiptChain = [];
  
  return function(req, res) {
    const violation = req.body;
    
    if (!violation || !violation.receipt_type) {
      return res.status(400).json({ error: 'Invalid violation report' });
    }
    
    // Adicionar hash chain
    const lastReceipt = receiptChain[receiptChain.length - 1];
    if (lastReceipt) {
      violation.previous_receipt_hash = lastReceipt.receipt_hash;
    }
    
    // Calcular hash do receipt
    const receiptString = JSON.stringify(violation);
    const receiptHash = crypto.createHash('sha256').update(receiptString).digest('hex');
    violation.receipt_hash = `sha256-${receiptHash}`;
    
    // Armazenar na chain
    receiptChain.push(violation);
    
    // Log
    console.warn('[WSG] 🚨 VIOLATION:', JSON.stringify(violation, null, 2));
    
    // Callback para ledger externo
    if (typeof ledgerCallback === 'function') {
      try {
        ledgerCallback(violation);
      } catch (error) {
        console.error('[WSG] Ledger callback error:', error);
      }
    }
    
    res.json({
      received: true,
      receipt_hash: violation.receipt_hash,
      chain_length: receiptChain.length,
      timestamp: new Date().toISOString()
    });
  };
}

// ═══════════════════════════════════════════════════════════════
// SETUP HELPER
// ═══════════════════════════════════════════════════════════════

/**
 * Setup completo para Express
 */
function setup(app, staticDir, options = {}) {
  const {
    ledgerCallback,
    privateKey = WSG_CONFIG.privateKey,
    enableWatcher = process.env.NODE_ENV !== 'production'
  } = options;
  
  // Middleware de headers
  app.use(wsgMiddleware(staticDir, { privateKey }));
  
  // Rotas
  app.get('/api/wsg/virtue-manifest.json', virtueManifestRoute(staticDir, { privateKey }));
  app.post('/api/wsg/violation', violationReportRoute({ ledgerCallback }));
  
  // Key generation helper route (apenas em dev)
  if (process.env.NODE_ENV !== 'production') {
    app.get('/api/wsg/generate-keys', (req, res) => {
      const keys = generateKeyPair();
      res.json({
        warning: 'SAVE THESE KEYS SECURELY. This endpoint is dev-only.',
        ...keys,
        instructions: {
          privateKey: 'Set as WSG_PRIVATE_KEY environment variable',
          publicKey: 'Embed in wsg-service-worker.js PINNED_PUBLIC_KEY'
        }
      });
    });
  }
  
  // File watcher
  if (enableWatcher) {
    try {
      const chokidar = require('chokidar');
      const watchPaths = WSG_CONFIG.assetDirectories.map(
        dir => path.join(staticDir, dir, '**/*')
      );
      
      chokidar.watch(watchPaths, { ignored: /node_modules/ })
        .on('change', (filePath) => {
          console.log(`[WSG] Asset changed: ${filePath}`);
          virtueCache.invalidate(filePath);
        });
      
      console.log('[WSG] File watcher enabled');
    } catch (e) {
      console.warn('[WSG] chokidar not available');
    }
  }
  
  console.log(`[WSG] 🛡️ WINDI Surface Guard v0.1.1 middleware initialized`);
  console.log(`[WSG] Signature: ${privateKey ? 'Ed25519 ENABLED' : 'DEV MODE (no signature)'}`);
  
  return virtueCache;
}

// ═══════════════════════════════════════════════════════════════
// EXPORTS
// ═══════════════════════════════════════════════════════════════

module.exports = {
  middleware: wsgMiddleware,
  manifestRoute: virtueManifestRoute,
  violationRoute: violationReportRoute,
  cache: virtueCache,
  setup,
  generateKeyPair,
  config: WSG_CONFIG
};
