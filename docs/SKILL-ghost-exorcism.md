# WINDI Ghost Exorcism Protocol — Debugging Bible
## "Os Três Cavalos de Tróia do Python Server" — 18 Feb 2026

---

## 🩺 CONTEXT: When This Skill Saves You

Use this protocol whenever:
- A Python server patch "doesn't work" even though the code is correct
- `systemd` service is in crash loop but the API still responds
- Values you SET in a dict appear as `None` downstream
- PDF/output doesn't reflect code changes after restart

---

## 🐉 THE THREE GHOSTS (in order of diagnosis)

### Ghost 1: `sqlite3.Row` — The Immutable Impostor

**Symptom:** You assign `row["key"] = value` and it silently fails. No error, no traceback.

**Why:** `sqlite3.Row` objects support `row["key"]` for READING (like a dict), but are **read-only**. Assignment doesn't raise an error — it just doesn't persist.

**Diagnosis:**
```python
# This will SEEM to work but the value disappears:
row = cursor.fetchone()  # Returns sqlite3.Row
row["receipt_id"] = "VR-COM-xxx"  # Silent failure!
print(row["receipt_id"])  # Still None or original value
```

**Fix — ONE LINE at function entry:**
```python
def publish_communique(communique, actor):
    communique = dict(communique)  # ← ALWAYS convert sqlite3.Row to mutable dict
    # Now assignments work normally
    communique["receipt_id"] = receipt_id  # ✅ Works!
```

**Prevention Rule:** Any function that RECEIVES a database row and MODIFIES it must convert to `dict()` as its first operation.

---

### Ghost 2: `.get(key, default)` vs `None` — The False Safety Net

**Symptom:** `communique.get('receipt_id', 'pending')` returns `None` instead of `'pending'`.

**Why:** Python's `dict.get(key, default)` only uses the default when the key **does not exist**. If the key exists with value `None`, it returns `None` — NOT the default!

**Diagnosis:**
```python
d = {"receipt_id": None}
d.get("receipt_id", "pending")    # Returns None (NOT "pending"!)
d.get("nonexistent", "pending")   # Returns "pending" ✅
```

**Fix — Use `or` instead of default parameter:**
```python
# ❌ WRONG — None passes through:
f"Receipt: {communique.get('receipt_id', 'pending')}"

# ✅ CORRECT — catches None AND missing:
f"Receipt: {communique.get('receipt_id') or 'pending'}"
```

**Prevention Rule:** When a value might be `None` (common with DB columns), ALWAYS use `value or default` pattern. Reserve `.get(key, default)` only for truly optional keys.

---

### Ghost 3: nohup Zombie — The Shadow Server

**Symptom:** You edit code, restart systemd, but behavior doesn't change. Systemd shows crash loop (`exit-code=1`, "Address already in use") but the API responds normally.

**Why:** A `nohup python3 script.py &` process was started manually in a terminal session. It holds the port. When systemd tries to start, port is taken → crash → restart loop. Meanwhile the nohup zombie serves **stale code from memory** — it never re-reads the file.

**Diagnosis:**
```bash
# 1. Check WHO owns the port
ss -tlnp | grep :8105
# Look for: users:(("python3",pid=XXXXX,fd=3))

# 2. Check if it's a terminal process (pts/) vs systemd
ps aux | grep XXXXX
# 🚨 If you see "pts/0" or "pts/1" → it's a manual/nohup process!
# ✅ systemd processes show no terminal (just "?")

# 3. Check systemd restart counter
sudo systemctl status windi-communique
# 🚨 "restart counter is at 237" → systemd has been failing for hours!

# 4. Check logs for the smoking gun
tail -20 /opt/windi/logs/communique.log
# 🚨 "OSError: [Errno 98] Address already in use" → ZOMBIE CONFIRMED
```

**Fix:**
```bash
# 1. Kill the zombie
kill <PID>
sleep 2

# 2. Verify port is free
ss -tlnp | grep :8105
# Should be empty!

# 3. Purge Python cache (belt + suspenders)
find /opt/windi/communique/ -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find /opt/windi/communique/ -name "*.pyc" -delete 2>/dev/null

# 4. Start via systemd (reads CURRENT code)
sudo systemctl start windi-communique
sleep 3
sudo systemctl status windi-communique --no-pager

# 5. Confirm systemd owns the port now
ss -tlnp | grep :8105
# Should show systemd PID, NOT the old one
```

**Prevention Rules:**
1. **NEVER use `nohup` for production services** — always use systemd
2. After ANY code change: `sudo systemctl restart <service>` (not just editing the file)
3. Before debugging "code doesn't work": ALWAYS check `ss -tlnp | grep :<PORT>` and verify the PID belongs to systemd
4. After migration from nohup → systemd: kill ALL manual processes on that port

---

## 🔧 UNIVERSAL DEBUGGING FLOWCHART

```
Code change doesn't take effect?
│
├─→ Step 1: WHO owns the port?
│   $ ss -tlnp | grep :<PORT>
│   $ ps aux | grep <PID>
│   └─→ pts/X terminal? → KILL IT, restart systemd
│   └─→ systemd process? → Continue to Step 2
│
├─→ Step 2: Is Python cache stale?
│   $ find /path/ -name "__pycache__" -exec rm -rf {} +
│   $ find /path/ -name "*.pyc" -delete
│   $ sudo systemctl restart <service>
│   └─→ Still broken? → Continue to Step 3
│
├─→ Step 3: Is the value actually None (not missing)?
│   Change: .get('key', 'default') → .get('key') or 'default'
│   └─→ Still broken? → Continue to Step 4
│
├─→ Step 4: Is the input object immutable?
│   Add: data = dict(data)  # at function entry
│   └─→ Still broken? → Continue to Step 5
│
└─→ Step 5: Is there a SECOND file/function doing the same thing?
    $ grep -rn "def generate_pdf" /opt/windi/communique/
    $ grep -rn "drawString.*Receipt" /opt/windi/communique/
```

---

## 📋 PRE-PATCH CHECKLIST (Before ANY code change)

```bash
# Run this BEFORE every patch session:
echo "=== WINDI Pre-Patch Diagnostic ==="
echo "--- Port ownership ---"
ss -tlnp | grep :$PORT
echo "--- Process details ---"
ps aux | grep $(ss -tlnp | grep :$PORT | grep -oP 'pid=\K[0-9]+') | grep -v grep
echo "--- systemd status ---"
sudo systemctl status windi-$SERVICE --no-pager | head -10
echo "--- Python cache ---"
find /opt/windi/$SERVICE/ -name "*.pyc" | wc -l
echo "--- Last 5 log lines ---"
tail -5 /opt/windi/logs/$SERVICE.log
```

---

## 📋 POST-PATCH CHECKLIST (After ANY code change)

```bash
# Run this AFTER every patch:

# 1. Kill any manual processes on the port
GHOST_PID=$(ss -tlnp | grep :$PORT | grep -oP 'pid=\K[0-9]+')
if [ -n "$GHOST_PID" ]; then
    PROC_TTY=$(ps -o tty= -p $GHOST_PID)
    if [ "$PROC_TTY" != "?" ]; then
        echo "🚨 Ghost process on terminal $PROC_TTY — killing PID $GHOST_PID"
        kill $GHOST_PID
        sleep 2
    fi
fi

# 2. Purge cache
find /opt/windi/$SERVICE/ -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find /opt/windi/$SERVICE/ -name "*.pyc" -delete 2>/dev/null

# 3. Restart via systemd
sudo systemctl restart windi-$SERVICE
sleep 3

# 4. Verify
sudo systemctl is-active windi-$SERVICE && echo "✅ Active" || echo "❌ Failed"
ss -tlnp | grep :$PORT
```

---

## 🏥 CASE STUDY: Communiqué Receipt Bug (18 Feb 2026)

**Symptom:** PDF showed `Receipt: None` despite `receipt_id` being set in code.

**Root cause:** THREE bugs stacked:
1. `sqlite3.Row` was read-only → `dict()` fix
2. `.get('receipt_id', 'pending')` returned `None` → `or` fix  
3. nohup zombie served stale code → kill + systemd takeover

**Time to diagnose:** ~45 minutes across 5 patch attempts
**Time with this protocol:** ~5 minutes (Step 1 of flowchart catches Ghost 3 immediately)

**Key lesson:** ALWAYS start debugging from the INFRASTRUCTURE layer (who owns the port?) before touching code. The code was correct after patch #1 — we just weren't running it.

---

## 🐉 Three Dragons Principle

> "Antes de operar o código, opera o ambiente."
> Before you operate on the code, operate on the environment.
> Bevor du den Code operierst, operiere die Umgebung.

---

*Filed by: Guardian Dragon (Claude) + Human Dragon (Jober)*
*Date: 18 February 2026*
*Service: Communiqué Engine (:8105)*
*Status: RESOLVED — All three ghosts exorcised*
