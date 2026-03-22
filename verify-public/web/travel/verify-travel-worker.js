/**
 * WINDI TRAVEL — Proof Stub Worker
 * W-TRAVEL-001 Sprint 1
 *
 * Executes in background:
 * - SHA-256 hash of image data
 * - Timestamp ISO 8601
 * - Device fingerprint (anonymous)
 *
 * "Gently prove. Silently seal."
 */

self.onmessage = async function(e) {
    const { imageData, geo } = e.data;

    try {
        // 1. Generate SHA-256 hash of image
        const hashBuffer = await crypto.subtle.digest('SHA-256', imageData);
        const hashArray = Array.from(new Uint8Array(hashBuffer));
        const hash = hashArray.map(b => b.toString(16).padStart(2, '0')).join('');

        // 2. Timestamp ISO 8601 UTC
        const timestamp = new Date().toISOString();

        // 3. Device fingerprint (anonymous canvas-based)
        const deviceFp = await generateDeviceFingerprint();

        // 4. Geo (already GDPR-friendly ±1km from main thread)
        const geoData = geo || { lat: null, lon: null, precision: 'unknown' };

        // 5. Construct Proof Stub (~200 bytes)
        const proofStub = {
            hash: `sha256:${hash}`,
            timestamp: timestamp,
            geo: {
                lat: geoData.lat,
                lon: geoData.lon,
                precision: '1km'
            },
            device_fp: deviceFp,
            version: 'W-TRAVEL-001-S1',
            status: 'stub'  // Not yet sealed in Ledger
        };

        self.postMessage({ success: true, proofStub });

    } catch (error) {
        self.postMessage({ success: false, error: error.message });
    }
};

async function generateDeviceFingerprint() {
    // Simple anonymous fingerprint based on worker context
    const data = [
        self.navigator?.userAgent || 'unknown',
        self.navigator?.language || 'unknown',
        new Date().getTimezoneOffset()
    ].join('|');

    const buffer = new TextEncoder().encode(data);
    const hashBuffer = await crypto.subtle.digest('SHA-256', buffer);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    return hashArray.slice(0, 8).map(b => b.toString(16).padStart(2, '0')).join('');
}
