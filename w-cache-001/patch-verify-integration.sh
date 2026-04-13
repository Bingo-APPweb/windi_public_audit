#!/bin/bash
# ═══════════════════════════════════════════════
# W-CACHE-001 · VERIFY-PUBLIC INTEGRATION PATCH
# Replaces simple cache with Verifiable Cache Layer
# ═══════════════════════════════════════════════

set -e

VERIFY_MAIN="/opt/windi/verify-public/app/main.py"
BACKUP_DIR="/opt/windi/w-cache-001"

echo "🔧 Patching verify-public for W-CACHE-001 integration..."

# 1. Backup
BACKUP_FILE="$BACKUP_DIR/verify-main-backup-$(date +%Y%m%d_%H%M%S).py"
cp "$VERIFY_MAIN" "$BACKUP_FILE"
echo "✅ Backup created: $BACKUP_FILE"

# 2. Check if already patched
if grep -q "wcache_integration" "$VERIFY_MAIN"; then
    echo "⚠️  Already patched. Skipping."
    exit 0
fi

# 3. Create patched version
# Add import after existing imports
sed -i '/^from verify_engine import/a\
# W-CACHE-001 Integration (Verifiable Cache Layer)\
try:\
    from wcache_integration import cache_get, cache_set, wcache_health\
    WCACHE_ENABLED = True\
except ImportError:\
    WCACHE_ENABLED = False\
    # Fallback to simple cache if W-CACHE-001 not available\
    _cache = {}\
    def cache_get(key):\
        e = _cache.get(key)\
        if e and time.time() < e[1]:\
            return e[0]\
        return None\
    def cache_set(key, value):\
        _cache[key] = (value, time.time() + 60)\
        if len(_cache) > 1000:\
            now = time.time()\
            for k in [k for k, v in list(_cache.items()) if now >= v[1]]:\
                del _cache[k]' "$VERIFY_MAIN"

# 4. Remove old cache functions (they're now imported or defined in the try block)
# This is tricky - we'll comment them out instead
sed -i 's/^CACHE_TTL     = 60$/# CACHE_TTL = 60  # Moved to wcache_integration/' "$VERIFY_MAIN"
sed -i 's/^_cache: dict  = {}$/# _cache: dict = {}  # Moved to wcache_integration/' "$VERIFY_MAIN"

# Comment out old cache_get
sed -i '/^def cache_get(key):$/,/^    return None$/s/^/# W-CACHE-REPLACED: /' "$VERIFY_MAIN"

# Comment out old cache_set
sed -i '/^def cache_set(key, value):$/,/^            del _cache\[k\]$/s/^/# W-CACHE-REPLACED: /' "$VERIFY_MAIN"

echo "✅ Patch applied"

# 5. Test import
echo "🧪 Testing import..."
cd /opt/windi/verify-public/app
python3 -c "from main import app; print('✅ Import OK')" 2>/dev/null || {
    echo "❌ Import failed. Restoring backup..."
    cp "$BACKUP_FILE" "$VERIFY_MAIN"
    exit 1
}

echo ""
echo "✅ verify-public patched for W-CACHE-001!"
echo ""
echo "To activate, restart verify-public:"
echo "  kill \$(pgrep -f 'verify-public.*main.py') && nohup python3 main.py &"
echo ""
echo "Monitor cache hits:"
echo "  curl http://localhost:8160/api/cache/v1/metrics"
