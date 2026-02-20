#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════╗
║     WINDI CHAIN BREAK FORENSIC DIAGNOSTIC v1.0               ║
║                                                              ║
║     "AI processes. Human decides. WINDI guarantees."         ║
║     Three Dragons Protocol — Guardian Module                 ║
╚══════════════════════════════════════════════════════════════╝

Investigates the 8 chain breaks detected by Governance Guard.
Analyzes governance_audit AND document_audit tables.
Classifies each break by severity and probable cause.
"""

import sqlite3
import json
import os
from datetime import datetime, timezone
from collections import defaultdict

# ─────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────

BABEL_DB = os.environ.get("BABEL_DB", "/opt/windi/data/babel_documents.db")
VIRTUE_DB = os.environ.get("VIRTUE_DB", "/opt/windi/data/virtue_history.db")
GUARD_DB = os.environ.get("GUARD_DB", "/opt/windi/data/guard/governance_guard.db")

# Severity thresholds (in seconds)
THRESHOLD_TRIVIAL = 2          # < 2s = clock drift / formatting
THRESHOLD_MINOR = 60           # < 1min = minor reordering
THRESHOLD_MODERATE = 3600      # < 1hr = session overlap
THRESHOLD_SERIOUS = 86400      # < 24hr = retroactive edit same day
# > 24hr = CRITICAL — potential integrity violation


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────

def parse_ts(ts_raw):
    """Parse various timestamp formats to datetime."""
    if ts_raw is None:
        return None
    ts = str(ts_raw).strip()
    
    formats = [
        "%Y-%m-%dT%H:%M:%S.%f%z",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%S.%fZ",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S.%f",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
    ]
    
    # Try fromisoformat first (handles most cases)
    try:
        clean = ts.replace("Z", "+00:00")
        return datetime.fromisoformat(clean)
    except (ValueError, TypeError):
        pass
    
    # Fallback to strptime
    for fmt in formats:
        try:
            dt = datetime.strptime(ts, fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except ValueError:
            continue
    
    return None


def classify_severity(seconds_back):
    """Classify the severity of a temporal break."""
    if seconds_back <= THRESHOLD_TRIVIAL:
        return "🟢 TRIVIAL", "Clock drift or sub-second reordering"
    elif seconds_back <= THRESHOLD_MINOR:
        return "🟡 MINOR", "Minor timestamp reordering (< 1 min)"
    elif seconds_back <= THRESHOLD_MODERATE:
        return "🟠 MODERATE", "Session overlap or batch processing"
    elif seconds_back <= THRESHOLD_SERIOUS:
        return "🔴 SERIOUS", "Retroactive edit within same day"
    else:
        days = seconds_back / 86400
        return "⚫ CRITICAL", f"Temporal violation: {days:.1f} days backwards"


def format_duration(seconds):
    """Human-readable duration."""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        return f"{seconds/60:.1f}min"
    elif seconds < 86400:
        return f"{seconds/3600:.1f}hr"
    else:
        return f"{seconds/86400:.1f}days"


# ─────────────────────────────────────────────
# ANALYZERS
# ─────────────────────────────────────────────

def analyze_table(db_path, table_name, id_col="id", ts_col="timestamp"):
    """Analyze a single audit table for chain breaks."""
    if not os.path.exists(db_path):
        print(f"  ⚠️  Database not found: {db_path}")
        return [], 0

    conn = sqlite3.connect(db_path, timeout=30)
    c = conn.cursor()

    # Check if table exists
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
    if not c.fetchone():
        print(f"  ⚠️  Table '{table_name}' not found")
        conn.close()
        return [], 0

    # Get column names
    c.execute(f"PRAGMA table_info([{table_name}])")
    columns = [col[1] for col in c.fetchall()]
    
    # Find the best timestamp column
    ts_candidates = [ts_col, "timestamp", "created_at", "updated_at", "date", "ts"]
    actual_ts_col = None
    for candidate in ts_candidates:
        if candidate in columns:
            actual_ts_col = candidate
            break
    
    if actual_ts_col is None:
        print(f"  ⚠️  No timestamp column found in {table_name}. Columns: {columns}")
        conn.close()
        return [], 0

    # Find the best ID column
    id_candidates = [id_col, "id", "rowid"]
    actual_id_col = None
    for candidate in id_candidates:
        if candidate in columns:
            actual_id_col = candidate
            break
    if actual_id_col is None:
        actual_id_col = "rowid"

    # Fetch all records ordered by ID
    try:
        c.execute(f"SELECT [{actual_id_col}], [{actual_ts_col}] FROM [{table_name}] ORDER BY [{actual_id_col}] ASC")
    except Exception:
        c.execute(f"SELECT rowid, [{actual_ts_col}] FROM [{table_name}] ORDER BY rowid ASC")
    
    rows = c.fetchall()
    total = len(rows)

    if total == 0:
        conn.close()
        return [], 0

    breaks = []
    prev_id, prev_ts_raw = rows[0]
    prev_ts = parse_ts(prev_ts_raw)

    for row_id, ts_raw in rows[1:]:
        current_ts = parse_ts(ts_raw)
        
        if prev_ts and current_ts and current_ts < prev_ts:
            delta_seconds = (prev_ts - current_ts).total_seconds()
            severity, cause = classify_severity(delta_seconds)
            
            breaks.append({
                "table": table_name,
                "prev_id": prev_id,
                "prev_ts": str(prev_ts_raw),
                "current_id": row_id,
                "current_ts": str(ts_raw),
                "seconds_back": delta_seconds,
                "duration_str": format_duration(delta_seconds),
                "severity": severity,
                "probable_cause": cause,
            })
        
        prev_id, prev_ts_raw, prev_ts = row_id, ts_raw, current_ts

    # Also fetch context for break records (what action, document, etc.)
    context_cols = [c for c in columns if c in (
        "action", "event", "type", "document_id", "doc_id",
        "user", "user_id", "description", "details", "operation"
    )]
    
    if context_cols and breaks:
        select_cols = ", ".join(f"[{c}]" for c in context_cols)
        for brk in breaks:
            try:
                c.execute(
                    f"SELECT {select_cols} FROM [{table_name}] WHERE [{actual_id_col}] = ?",
                    (brk["current_id"],)
                )
                row = c.fetchone()
                if row:
                    brk["context"] = dict(zip(context_cols, row))
            except Exception:
                pass

    conn.close()
    return breaks, total


def analyze_all_tables():
    """Analyze all known audit tables across WINDI databases."""
    print("=" * 65)
    print("  🔍 WINDI CHAIN BREAK FORENSIC DIAGNOSTIC")
    print("  Three Dragons Protocol — Guardian Module")
    print("  \"AI processes. Human decides. WINDI guarantees.\"")
    print("=" * 65)
    print()

    all_breaks = []
    total_records = 0

    # 1. BABEL Database tables
    print("📦 Analyzing BABEL Database: %s" % BABEL_DB)
    print("-" * 50)

    if os.path.exists(BABEL_DB):
        conn = sqlite3.connect(BABEL_DB, timeout=30)
        c = conn.cursor()
        c.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in c.fetchall()]
        conn.close()
        print(f"  Found tables: {', '.join(tables)}")
        print()

        # Check audit tables
        audit_tables = [t for t in tables if "audit" in t.lower() or "log" in t.lower() or "history" in t.lower()]
        for table in audit_tables:
            print(f"  📋 Table: {table}")
            breaks, count = analyze_table(BABEL_DB, table)
            total_records += count
            all_breaks.extend(breaks)
            print(f"     Records: {count}, Breaks: {len(breaks)}")

        # Also check documents table for temporal consistency
        if "documents" in tables:
            print(f"  📋 Table: documents")
            breaks, count = analyze_table(BABEL_DB, "documents", ts_col="created_at")
            total_records += count
            all_breaks.extend(breaks)
            print(f"     Records: {count}, Breaks: {len(breaks)}")
    else:
        print("  ⚠️  BABEL DB not found")

    print()

    # 2. Virtue History Database
    print("📦 Analyzing Virtue History: %s" % VIRTUE_DB)
    print("-" * 50)

    if os.path.exists(VIRTUE_DB):
        conn = sqlite3.connect(VIRTUE_DB, timeout=30)
        c = conn.cursor()
        c.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in c.fetchall()]
        conn.close()
        print(f"  Found tables: {', '.join(tables)}")
        print()

        for table in tables:
            if table.startswith("sqlite_"):
                continue
            print(f"  📋 Table: {table}")
            breaks, count = analyze_table(VIRTUE_DB, table)
            total_records += count
            all_breaks.extend(breaks)
            print(f"     Records: {count}, Breaks: {len(breaks)}")
    else:
        print("  ⚠️  Virtue DB not found")

    print()

    # 3. Guard Database (self-check)
    if os.path.exists(GUARD_DB):
        print("📦 Analyzing Guard Database: %s" % GUARD_DB)
        print("-" * 50)
        conn = sqlite3.connect(GUARD_DB, timeout=30)
        c = conn.cursor()
        c.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in c.fetchall()]
        conn.close()
        
        for table in tables:
            if table.startswith("sqlite_"):
                continue
            breaks, count = analyze_table(GUARD_DB, table)
            if breaks:
                total_records += count
                all_breaks.extend(breaks)
                print(f"  📋 {table}: {count} records, {len(breaks)} breaks")
        print()

    # ─────────────────────────────────────────
    # REPORT
    # ─────────────────────────────────────────
    
    print("=" * 65)
    print("  📊 FORENSIC REPORT")
    print("=" * 65)
    print(f"\n  Total records analyzed: {total_records}")
    print(f"  Total chain breaks found: {len(all_breaks)}")
    print()

    if not all_breaks:
        print("  ✅ NO CHAIN BREAKS DETECTED")
        print("  🛡️  WINDI VERIFIED — Chain Integrity INTACT")
        return all_breaks

    # Sort by severity (most critical first)
    severity_order = {"⚫ CRITICAL": 0, "🔴 SERIOUS": 1, "🟠 MODERATE": 2, "🟡 MINOR": 3, "🟢 TRIVIAL": 4}
    all_breaks.sort(key=lambda b: severity_order.get(b["severity"], 5))

    # Group by severity
    by_severity = defaultdict(list)
    for brk in all_breaks:
        by_severity[brk["severity"]].append(brk)

    print("  SEVERITY DISTRIBUTION:")
    for sev, items in by_severity.items():
        print(f"    {sev}: {len(items)} breaks")
    print()

    # Detailed break listing
    print("  DETAILED BREAK ANALYSIS:")
    print("  " + "-" * 60)

    for i, brk in enumerate(all_breaks, 1):
        print(f"\n  Break #{i} — {brk['severity']}")
        print(f"  Table: {brk['table']}")
        print(f"  Record ID {brk['current_id']} timestamp: {brk['current_ts']}")
        print(f"  Previous ID {brk['prev_id']} timestamp: {brk['prev_ts']}")
        print(f"  ↳ Goes BACK by: {brk['duration_str']} ({brk['seconds_back']:.1f}s)")
        print(f"  ↳ Probable cause: {brk['probable_cause']}")
        
        if "context" in brk and brk["context"]:
            ctx = brk["context"]
            ctx_str = ", ".join(f"{k}={v}" for k, v in ctx.items() if v is not None)
            if ctx_str:
                print(f"  ↳ Context: {ctx_str}")

    # ─────────────────────────────────────────
    # RECOMMENDATIONS
    # ─────────────────────────────────────────
    
    print("\n" + "=" * 65)
    print("  🎯 RECOMMENDATIONS")
    print("=" * 65)

    critical_count = len(by_severity.get("⚫ CRITICAL", []))
    serious_count = len(by_severity.get("🔴 SERIOUS", []))
    trivial_count = len(by_severity.get("🟢 TRIVIAL", [])) + len(by_severity.get("🟡 MINOR", []))

    if critical_count > 0:
        print(f"\n  🚨 {critical_count} CRITICAL breaks require immediate investigation!")
        print("     → These indicate potential data integrity violations")
        print("     → Audit who/what modified these records")
        print("     → Consider restoring from backup if tampering confirmed")

    if serious_count > 0:
        print(f"\n  ⚠️  {serious_count} SERIOUS breaks need review")
        print("     → Likely retroactive edits — check if authorized")
        print("     → Implement write-once policy for audit records")

    if trivial_count > 0 and critical_count == 0 and serious_count == 0:
        print(f"\n  ✅ All {trivial_count} breaks are TRIVIAL/MINOR")
        print("     → Likely clock drift or batch processing artifacts")
        print("     → Consider normalizing all timestamps to UTC on write")
        print("     → These do NOT compromise governance integrity")

    if trivial_count > 0 and (critical_count > 0 or serious_count > 0):
        print(f"\n  ℹ️  {trivial_count} additional trivial/minor breaks (clock drift)")

    # Final verdict
    print("\n" + "=" * 65)
    if critical_count == 0 and serious_count == 0:
        print("  🛡️  VERDICT: Chain integrity PRESERVED")
        print("     Minor temporal inconsistencies do not affect governance validity")
        print("     ✅ WINDI VERIFIED (with advisory notes)")
    elif critical_count == 0:
        print("  ⚠️  VERDICT: Chain integrity CONDITIONAL")
        print("     Serious breaks require human review before verification")
        print("     🟡 WINDI VERIFICATION PENDING — Human Decision Required")
    else:
        print("  🔴 VERDICT: Chain integrity COMPROMISED")
        print("     Critical breaks detected — investigation required")
        print("     ❌ WINDI NOT VERIFIED — Action Required")
    print("=" * 65)
    print()
    print("  \"AI processes. Human decides. WINDI guarantees.\"")
    print()

    return all_breaks


# ─────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────

if __name__ == "__main__":
    breaks = analyze_all_tables()
    
    # Save results to JSON for Guard integration
    output_path = os.path.join(
        os.path.dirname(GUARD_DB) if os.path.exists(os.path.dirname(GUARD_DB)) else "/tmp",
        "chain_forensic_report.json"
    )
    try:
        with open(output_path, "w") as f:
            json.dump({
                "analyzed_at": datetime.utcnow().isoformat() + "Z",
                "total_breaks": len(breaks),
                "breaks": breaks
            }, f, indent=2, default=str)
        print(f"  📄 Full report saved: {output_path}")
    except Exception as e:
        print(f"  ⚠️  Could not save report: {e}")
