/**
 * §173 DID SIMPLIFICATION — Frontend Standard
 * §194 SESSION IDENTITY BRIDGE — Cookie→localStorage Sync
 * ========================================================
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
 *   // §194 — Sync from authenticated session (cookie → localStorage)
 *   const session = await WindiDID.sync();
 *   if (session.synced) {
 *       console.log(`DID: ${session.did}`);
 *   }
 *
 * Principle: "Um DID. Uma fonte. Zero fallbacks."
 * Security: "Frontend never invents identity — only reflects the backend."
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
    // STORAGE FUNCTIONS — §190 Mobile Private Mode Fix
    // ═══════════════════════════════════════════════════════════════════════

    /**
     * Check if localStorage is available (fails in iOS Safari Private Mode).
     * @returns {boolean}
     */
    function isStorageAvailable() {
        try {
            const test = '__windi_storage_test__';
            localStorage.setItem(test, test);
            localStorage.removeItem(test);
            return true;
        } catch (e) {
            return false;
        }
    }

    // Cache storage availability check
    const HAS_LOCAL_STORAGE = isStorageAvailable();

    /**
     * Get the current DID from localStorage (with sessionStorage fallback for mobile).
     * @returns {string|null} The DID or null if not set
     */
    function get() {
        try {
            if (HAS_LOCAL_STORAGE) {
                return localStorage.getItem(STORAGE_KEY) || null;
            }
            // Fallback to sessionStorage for private mode
            return sessionStorage.getItem(STORAGE_KEY) || null;
        } catch (e) {
            console.warn('[WindiDID] Storage read error:', e.message);
            return null;
        }
    }

    /**
     * Set the DID in localStorage (with sessionStorage fallback for mobile).
     * @param {string} did - The DID to store
     */
    function set(did) {
        if (did && typeof did === 'string' && did.startsWith('did:windi:')) {
            try {
                if (HAS_LOCAL_STORAGE) {
                    localStorage.setItem(STORAGE_KEY, did);
                } else {
                    // Fallback to sessionStorage for iOS Safari Private Mode
                    sessionStorage.setItem(STORAGE_KEY, did);
                    console.log('[WindiDID] Using sessionStorage (private mode)');
                }
                console.log('[WindiDID] Set:', did.substring(0, 25) + '...');
            } catch (e) {
                console.warn('[WindiDID] Storage write error:', e.message);
                // Last resort: keep in memory only
            }
        } else {
            console.warn('[WindiDID] Invalid DID format, not saving');
        }
    }

    /**
     * Clear the DID from localStorage.
     */
    function clear() {
        try {
            localStorage.removeItem(STORAGE_KEY);
            sessionStorage.removeItem(STORAGE_KEY);
            console.log('[WindiDID] Cleared');
        } catch (e) {
            console.warn('[WindiDID] Storage clear error:', e.message);
        }
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
     * §173 — Cleans both localStorage AND sessionStorage.
     */
    function migrateFromLegacy() {
        const legacyLocalKeys = [
            'windi_desktop_wallet',
            'windi_enterprise_did',
            'windi_law_did',
            'windi_travel_did',
            'windi_wallet',
            'windi_vdcut_wallet'
        ];

        const legacySessionKeys = [
            'windi_enterprise_did',
            'windi_law_did',
            'windi_travel_did',
            'windi_law_wallet',
            'windi_travel_wallet',
            'windi_law_fingerprint',
            'windi_travel_fingerprint'
        ];

        let migrated = false;
        const currentDid = get();

        if (!currentDid) {
            // Try to find a DID in legacy localStorage keys
            for (const key of legacyLocalKeys) {
                const value = localStorage.getItem(key);
                if (value && value.startsWith('did:windi:')) {
                    set(value);
                    console.log('[WindiDID] Migrated from localStorage:', key);
                    migrated = true;
                    break;
                }
            }
            // Also check sessionStorage
            if (!migrated) {
                for (const key of legacySessionKeys) {
                    const value = sessionStorage.getItem(key);
                    if (value && value.startsWith('did:windi:')) {
                        set(value);
                        console.log('[WindiDID] Migrated from sessionStorage:', key);
                        migrated = true;
                        break;
                    }
                }
            }
        }

        // Clean up localStorage legacy keys
        for (const key of legacyLocalKeys) {
            if (localStorage.getItem(key)) {
                localStorage.removeItem(key);
                console.log('[WindiDID] Removed localStorage:', key);
            }
        }

        // Clean up sessionStorage legacy keys
        for (const key of legacySessionKeys) {
            if (sessionStorage.getItem(key)) {
                sessionStorage.removeItem(key);
                console.log('[WindiDID] Removed sessionStorage:', key);
            }
        }

        return migrated;
    }

    // ═══════════════════════════════════════════════════════════════════════
    // SESSION SYNC — §194 Identity Bridge
    // ═══════════════════════════════════════════════════════════════════════

    const SESSION_ME_ENDPOINT = '/api/genesis/me';

    /**
     * §194 — Sync localStorage from authenticated session (cookie).
     *
     * SECURITY PRINCIPLE:
     * "Frontend never invents identity — only reflects the backend."
     *
     * This fetches the DID from the secure cookie-authenticated endpoint
     * and populates localStorage for frontend use.
     *
     * @returns {Promise<Object>} Session info or error
     */
    async function sync() {
        try {
            const response = await fetch(SESSION_ME_ENDPOINT, {
                credentials: 'include'  // Include cookies
            });

            if (!response.ok) {
                // Not authenticated or session expired
                if (response.status === 401) {
                    console.log('[WindiDID] No active session');
                    return { synced: false, reason: 'not_authenticated' };
                }
                return { synced: false, reason: 'error', status: response.status };
            }

            const data = await response.json();

            if (data.did) {
                set(data.did);
                console.log('[WindiDID] Synced from session:', data.did.substring(0, 25) + '...');
                return {
                    synced: true,
                    did: data.did,
                    display_name: data.display_name,
                    tier: data.tier,
                    tier_emoji: data.tier_emoji
                };
            }

            return { synced: false, reason: 'no_did_in_response' };
        } catch (error) {
            console.warn('[WindiDID] Sync error:', error.message);
            return { synced: false, reason: 'network_error', error: error.message };
        }
    }

    /**
     * §194 — Check if localStorage DID matches session DID.
     * Useful for detecting stale localStorage after logout elsewhere.
     *
     * @returns {Promise<Object>} Match status
     */
    async function verifySync() {
        const localDid = get();
        const session = await sync();

        if (!session.synced) {
            // No session — clear local if exists
            if (localDid) {
                console.log('[WindiDID] Session expired, clearing local');
                clear();
            }
            return { valid: false, reason: session.reason };
        }

        if (localDid !== session.did) {
            console.log('[WindiDID] Mismatch detected, updating local');
            set(session.did);
        }

        return { valid: true, did: session.did, tier: session.tier };
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

        // Session Sync (§194)
        sync,
        verifySync,

        // Constants
        STORAGE_KEY,
        VERSION: '1.1.0'  // §194 Session Sync
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
