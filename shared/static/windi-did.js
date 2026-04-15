/**
 * §173 DID SIMPLIFICATION — Frontend Standard
 * ============================================
 * SINGLE SOURCE OF TRUTH for DID handling in all WINDI frontends.
 *
 * Usage:
 *   <script src="/shared/windi-did.js"></script>
 *
 *   // Get current DID
 *   const did = WindiDID.get();
 *
 *   // Validate against Genesis
 *   const result = await WindiDID.validate(did);
 *   if (result.valid) {
 *       console.log(`Tier: ${result.tier}`);  // ORACLE
 *   }
 *
 * Principle: "Um DID. Uma fonte. Zero fallbacks."
 *
 * Liga IA+H · Kempten, Bavaria · 2026
 */

const WindiDID = (function() {
    'use strict';

    // ═══════════════════════════════════════════════════════════════════════
    // CONFIGURATION — Single Key
    // ═══════════════════════════════════════════════════════════════════════

    const STORAGE_KEY = 'windi_did';
    const GENESIS_LOOKUP = '/api/genesis/lookup/';

    // ═══════════════════════════════════════════════════════════════════════
    // STORAGE FUNCTIONS
    // ═══════════════════════════════════════════════════════════════════════

    /**
     * Get the current DID from localStorage.
     * @returns {string|null} The DID or null if not set
     */
    function get() {
        return localStorage.getItem(STORAGE_KEY) || null;
    }

    /**
     * Set the DID in localStorage.
     * @param {string} did - The DID to store
     */
    function set(did) {
        if (did && typeof did === 'string' && did.startsWith('did:windi:')) {
            localStorage.setItem(STORAGE_KEY, did);
            console.log('[WindiDID] Set:', did.substring(0, 25) + '...');
        } else {
            console.warn('[WindiDID] Invalid DID format, not saving');
        }
    }

    /**
     * Clear the DID from localStorage.
     */
    function clear() {
        localStorage.removeItem(STORAGE_KEY);
        console.log('[WindiDID] Cleared');
    }

    /**
     * Check if a DID is currently stored.
     * @returns {boolean}
     */
    function exists() {
        return !!get();
    }

    // ═══════════════════════════════════════════════════════════════════════
    // VALIDATION
    // ═══════════════════════════════════════════════════════════════════════

    /**
     * Validate a DID against W-DID-GENESIS.
     * This calls the Single Source of Truth.
     *
     * @param {string} did - The DID to validate
     * @returns {Promise<Object>} Validation result
     */
    async function validate(did) {
        if (!did) {
            return { valid: false, error: 'DID não fornecido' };
        }

        try {
            const response = await fetch(GENESIS_LOOKUP + encodeURIComponent(did));
            const data = await response.json();

            if (data.valid) {
                console.log('[WindiDID] Validated:', did.substring(0, 25) + '... → tier=' + data.tier);
            } else {
                console.warn('[WindiDID] Invalid:', did.substring(0, 25) + '...', data.error);
            }

            return data;
        } catch (error) {
            console.error('[WindiDID] Validation error:', error);
            return {
                valid: false,
                did: did,
                error: 'Genesis offline — validação impossível [I14]'
            };
        }
    }

    /**
     * Validate the currently stored DID.
     * @returns {Promise<Object>} Validation result
     */
    async function validateCurrent() {
        const did = get();
        if (!did) {
            return { valid: false, error: 'Nenhum DID armazenado' };
        }
        return validate(did);
    }

    /**
     * Quick format check (no network call).
     * Use validate() for full validation.
     *
     * @param {string} did - The DID to check
     * @returns {boolean}
     */
    function isValidFormat(did) {
        if (!did || typeof did !== 'string') return false;
        if (!did.startsWith('did:windi:')) return false;
        return did.length >= 15;
    }

    // ═══════════════════════════════════════════════════════════════════════
    // TIER HELPERS
    // ═══════════════════════════════════════════════════════════════════════

    const TIERS = {
        SEED: { level: 1, emoji: '🌱', name: 'Seed' },
        NODAL: { level: 2, emoji: '🌿', name: 'Nodal' },
        SOVEREIGN: { level: 3, emoji: '🌳', name: 'Sovereign' },
        ORACLE: { level: 4, emoji: '🏛', name: 'Oracle' }
    };

    /**
     * Get tier information.
     * @param {string} tier - Tier name
     * @returns {Object} Tier info
     */
    function getTierInfo(tier) {
        return TIERS[tier] || TIERS.SEED;
    }

    /**
     * Check if a tier meets minimum requirement.
     * @param {string} tier - User's tier
     * @param {string} minimum - Required minimum tier
     * @returns {boolean}
     */
    function isAtLeast(tier, minimum) {
        const userLevel = (TIERS[tier] || TIERS.SEED).level;
        const minLevel = (TIERS[minimum] || TIERS.SEED).level;
        return userLevel >= minLevel;
    }

    // ═══════════════════════════════════════════════════════════════════════
    // MIGRATION HELPER
    // ═══════════════════════════════════════════════════════════════════════

    /**
     * Migrate from old storage keys to the new standard.
     * Call this once on page load to clean up legacy keys.
     */
    function migrateFromLegacy() {
        const legacyKeys = [
            'windi_desktop_wallet',
            'windi_enterprise_did',
            'windi_law_did',
            'windi_travel_did',
            'windi_wallet',
            'windi_vdcut_wallet'
        ];

        let migrated = false;
        const currentDid = get();

        if (!currentDid) {
            // Try to find a DID in legacy keys
            for (const key of legacyKeys) {
                const value = localStorage.getItem(key);
                if (value && value.startsWith('did:windi:')) {
                    set(value);
                    console.log('[WindiDID] Migrated from', key);
                    migrated = true;
                    break;
                }
            }
        }

        // Clean up legacy keys
        for (const key of legacyKeys) {
            if (localStorage.getItem(key)) {
                localStorage.removeItem(key);
                console.log('[WindiDID] Removed legacy key:', key);
            }
        }

        return migrated;
    }

    // ═══════════════════════════════════════════════════════════════════════
    // PUBLIC API
    // ═══════════════════════════════════════════════════════════════════════

    return {
        // Storage
        get,
        set,
        clear,
        exists,

        // Validation
        validate,
        validateCurrent,
        isValidFormat,

        // Tiers
        TIERS,
        getTierInfo,
        isAtLeast,

        // Migration
        migrateFromLegacy,

        // Constants
        STORAGE_KEY,
        VERSION: '1.0.0'
    };
})();

// Auto-migration on load
if (typeof window !== 'undefined') {
    window.addEventListener('DOMContentLoaded', () => {
        WindiDID.migrateFromLegacy();
    });
}

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = WindiDID;
}
