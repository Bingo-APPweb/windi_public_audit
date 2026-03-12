/**
 * WINDI DragonEngine v2.0 — Manifest Registry
 * ============================================
 * Loads and provides access to all document type manifests.
 *
 * Three Dragons Protocol: AI processes. Human decides. WINDI guarantees.
 * (c) 2026 WINDI Publishing House — Kempten, Bavaria
 */

// In browser context, manifests are loaded via fetch
// In Node.js context, manifests are loaded via require

const MANIFEST_FILES = [
  'letter',
  'email',
  'memo',
  'note',
  'journal',
  'recipe',
  'report',
  'contract',
  'invoice',
  'protocol',
  'analysis',
  'presentation',
  'communique',
  'certificate',
  'declaration',
  'creative_virtue'
];

// Tier hierarchy for access control
const TIER_HIERARCHY = {
  FREE: 0,
  MED: 1,
  HIGH: 2
};

class ManifestRegistry {
  constructor() {
    this.manifests = {};
    this.loaded = false;
  }

  /**
   * Load all manifests
   * @param {string} basePath - Base path to manifests directory
   */
  async load(basePath = '/engine/manifests') {
    if (this.loaded) return;

    const loadPromises = MANIFEST_FILES.map(async (name) => {
      try {
        const url = `${basePath}/${name}.json`;
        const response = await fetch(url);
        if (response.ok) {
          const manifest = await response.json();
          this.manifests[manifest.id] = manifest;
        }
      } catch (e) {
        console.warn(`[ManifestRegistry] Failed to load ${name}:`, e.message);
      }
    });

    await Promise.all(loadPromises);
    this.loaded = true;
    console.log(`[ManifestRegistry] Loaded ${Object.keys(this.manifests).length} manifests`);
  }

  /**
   * Load manifests synchronously (Node.js only)
   */
  loadSync(basePath = __dirname) {
    if (typeof require === 'undefined') {
      console.warn('[ManifestRegistry] loadSync only works in Node.js');
      return;
    }

    for (const name of MANIFEST_FILES) {
      try {
        const manifest = require(`${basePath}/${name}.json`);
        this.manifests[manifest.id] = manifest;
      } catch (e) {
        console.warn(`[ManifestRegistry] Failed to load ${name}:`, e.message);
      }
    }
    this.loaded = true;
  }

  /**
   * Get manifest by ID
   */
  get(id) {
    return this.manifests[id] || null;
  }

  /**
   * Get all manifests
   */
  getAll() {
    return { ...this.manifests };
  }

  /**
   * Get manifests by tier
   */
  getByTier(tier) {
    const tierLevel = TIER_HIERARCHY[tier] ?? 0;
    return Object.values(this.manifests).filter(m => {
      const manifestTier = TIER_HIERARCHY[m.tier] ?? 0;
      return manifestTier <= tierLevel;
    });
  }

  /**
   * Get manifests by category
   */
  getByCategory(category) {
    return Object.values(this.manifests).filter(m => m.category === category);
  }

  /**
   * Check if user can access document type
   */
  canAccess(docType, userTier) {
    const manifest = this.get(docType);
    if (!manifest) return false;

    const userTierLevel = TIER_HIERARCHY[userTier] ?? 0;
    const requiredTierLevel = TIER_HIERARCHY[manifest.tier] ?? 0;

    return userTierLevel >= requiredTierLevel;
  }

  /**
   * Get schema for document type
   */
  getSchema(docType) {
    const manifest = this.get(docType);
    return manifest?.schema || null;
  }

  /**
   * Get flow for document type
   */
  getFlow(docType) {
    const manifest = this.get(docType);
    return manifest?.flow || [];
  }

  /**
   * Get seal policy for document type
   */
  getSealPolicy(docType) {
    const manifest = this.get(docType);
    return manifest?.sealPolicy || { required: false, defaultSeal: false, governanceLevel: 'minimal' };
  }

  /**
   * Get name in specified language
   */
  getName(docType, lang = 'en') {
    const manifest = this.get(docType);
    if (!manifest) return docType;
    return manifest.names?.[lang] || manifest.names?.en || docType;
  }

  /**
   * Get breath (tagline) in specified language
   */
  getBreath(docType, lang = 'en') {
    const manifest = this.get(docType);
    if (!manifest) return '';
    return manifest.breath?.[lang] || manifest.breath?.en || '';
  }

  /**
   * Get prompt in specified language
   */
  getPrompt(docType, lang = 'en') {
    const manifest = this.get(docType);
    if (!manifest) return '';
    return manifest.prompts?.[lang] || manifest.prompts?.en || '';
  }

  /**
   * Get DOC_TYPES compatible object (for backwards compatibility)
   */
  getDocTypesCompat() {
    const result = {};
    for (const [id, manifest] of Object.entries(this.manifests)) {
      result[id] = {
        icon: manifest.icon,
        tier: manifest.tier,
        cat: manifest.category,
        breath: manifest.breath
      };
    }
    return result;
  }

  /**
   * Get summary of loaded manifests
   */
  getSummary() {
    const byTier = { FREE: 0, MED: 0, HIGH: 0 };
    const byCategory = {};

    for (const manifest of Object.values(this.manifests)) {
      byTier[manifest.tier] = (byTier[manifest.tier] || 0) + 1;
      byCategory[manifest.category] = (byCategory[manifest.category] || 0) + 1;
    }

    return {
      total: Object.keys(this.manifests).length,
      byTier,
      byCategory,
      types: Object.keys(this.manifests)
    };
  }
}

// Singleton instance
let _registryInstance = null;

/**
 * Get or create registry instance
 */
function getManifestRegistry() {
  if (!_registryInstance) {
    _registryInstance = new ManifestRegistry();
  }
  return _registryInstance;
}

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { ManifestRegistry, getManifestRegistry, TIER_HIERARCHY };
}

// Export for browser
if (typeof window !== 'undefined') {
  window.ManifestRegistry = ManifestRegistry;
  window.getManifestRegistry = getManifestRegistry;
  window.TIER_HIERARCHY = TIER_HIERARCHY;
}
