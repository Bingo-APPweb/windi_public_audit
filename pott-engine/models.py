"""
═══════════════════════════════════════════════════════════════════════════════════
  POTT ENGINE — Database Models
  P3 Creator Governance Federation

  Constitutional Principles:
  - Data boundaries: audiência NUNCA cruza
  - Attribution 85/15: toda receita via Pott registada
  - Exit freedom: /leave leva conteúdo
  - Receipts: toda acção gera Virtue Receipt
═══════════════════════════════════════════════════════════════════════════════════
"""

import os
import aiosqlite
from datetime import datetime
from typing import Optional, List, Dict, Any
import json

DB_PATH = os.environ.get("POTT_DB_PATH", "/opt/windi/data/pott.db")

# ═══════════════════════════════════════════════════════════════════════════════════
# SCHEMA DEFINITIONS
# ═══════════════════════════════════════════════════════════════════════════════════

SCHEMA_SQL = """
-- Potts: Creator federations with 85/15 split
CREATE TABLE IF NOT EXISTS potts (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    vertical TEXT NOT NULL CHECK (vertical IN ('cooking', 'education', 'music', 'local', 'tech', 'art', 'fitness', 'business')),
    description TEXT DEFAULT '',
    curator_did TEXT NOT NULL,
    split_creator REAL DEFAULT 0.85,
    split_pott REAL DEFAULT 0.15,
    rules TEXT DEFAULT '{}',
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'paused', 'archived')),
    sealed_hash TEXT,
    ledger_receipt TEXT,
    member_count INTEGER DEFAULT 1,
    trigger_count INTEGER DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

-- Pott Members: Creators who joined a Pott
CREATE TABLE IF NOT EXISTS pott_members (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pott_id TEXT NOT NULL REFERENCES potts(id),
    creator_did TEXT NOT NULL,
    role TEXT DEFAULT 'member' CHECK (role IN ('curator', 'moderator', 'member')),
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'left', 'removed')),
    triggers_submitted INTEGER DEFAULT 0,
    revenue_share REAL DEFAULT 0.0,
    joined_at TEXT NOT NULL,
    left_at TEXT,
    ledger_receipt TEXT,
    UNIQUE(pott_id, creator_did)
);

-- Pott Featured: Curated triggers in feed
CREATE TABLE IF NOT EXISTS pott_featured (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pott_id TEXT NOT NULL REFERENCES potts(id),
    trigger_id TEXT NOT NULL,
    trigger_seal TEXT,
    creator_did TEXT NOT NULL,
    curator_did TEXT NOT NULL,
    action TEXT DEFAULT 'featured' CHECK (action IN ('featured', 'removed', 'pinned')),
    position INTEGER DEFAULT 0,
    featured_at TEXT NOT NULL,
    expires_at TEXT,
    ledger_receipt TEXT,
    UNIQUE(pott_id, trigger_id)
);

-- Pott Metrics: Daily aggregated stats
CREATE TABLE IF NOT EXISTS pott_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pott_id TEXT NOT NULL REFERENCES potts(id),
    date TEXT NOT NULL,
    views INTEGER DEFAULT 0,
    unique_viewers INTEGER DEFAULT 0,
    triggers_added INTEGER DEFAULT 0,
    members_joined INTEGER DEFAULT 0,
    revenue_total REAL DEFAULT 0.0,
    revenue_creators REAL DEFAULT 0.0,
    revenue_pott REAL DEFAULT 0.0,
    UNIQUE(pott_id, date)
);

-- Revenue Events: Every transaction tracked
CREATE TABLE IF NOT EXISTS pott_revenue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pott_id TEXT NOT NULL REFERENCES potts(id),
    trigger_id TEXT NOT NULL,
    creator_did TEXT NOT NULL,
    amount_total REAL NOT NULL,
    amount_creator REAL NOT NULL,
    amount_pott REAL NOT NULL,
    source TEXT DEFAULT 'direct',
    ledger_receipt TEXT,
    created_at TEXT NOT NULL
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_members_pott ON pott_members(pott_id);
CREATE INDEX IF NOT EXISTS idx_members_creator ON pott_members(creator_did);
CREATE INDEX IF NOT EXISTS idx_featured_pott ON pott_featured(pott_id);
CREATE INDEX IF NOT EXISTS idx_metrics_pott_date ON pott_metrics(pott_id, date);
CREATE INDEX IF NOT EXISTS idx_potts_vertical ON potts(vertical);
CREATE INDEX IF NOT EXISTS idx_potts_status ON potts(status);
"""

# ═══════════════════════════════════════════════════════════════════════════════════
# DATABASE OPERATIONS
# ═══════════════════════════════════════════════════════════════════════════════════

async def init_db():
    """Initialize database with schema."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript(SCHEMA_SQL)
        await db.commit()
    return True


async def get_db():
    """Get database connection."""
    db = await aiosqlite.connect(DB_PATH)
    db.row_factory = aiosqlite.Row
    return db


# ═══════════════════════════════════════════════════════════════════════════════════
# POTT CRUD OPERATIONS
# ═══════════════════════════════════════════════════════════════════════════════════

async def create_pott(
    pott_id: str,
    name: str,
    vertical: str,
    curator_did: str,
    description: str = "",
    split_creator: float = 0.85,
    split_pott: float = 0.15,
    rules: Dict = None,
    ledger_receipt: str = None
) -> Dict:
    """Create a new Pott federation."""
    now = datetime.utcnow().isoformat()
    rules_json = json.dumps(rules or {})

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO potts (id, name, vertical, description, curator_did,
                             split_creator, split_pott, rules, ledger_receipt,
                             created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (pott_id, name, vertical, description, curator_did,
              split_creator, split_pott, rules_json, ledger_receipt, now, now))

        # Curator is automatically first member
        await db.execute("""
            INSERT INTO pott_members (pott_id, creator_did, role, joined_at, ledger_receipt)
            VALUES (?, ?, 'curator', ?, ?)
        """, (pott_id, curator_did, now, ledger_receipt))

        await db.commit()

    return {
        "id": pott_id,
        "name": name,
        "vertical": vertical,
        "curator_did": curator_did,
        "split": {"creator": split_creator, "pott": split_pott},
        "created_at": now
    }


async def get_pott(pott_id: str) -> Optional[Dict]:
    """Get Pott details with members and stats."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        # Get pott
        cursor = await db.execute("SELECT * FROM potts WHERE id = ?", (pott_id,))
        row = await cursor.fetchone()
        if not row:
            return None

        pott = dict(row)
        pott["rules"] = json.loads(pott["rules"]) if pott["rules"] else {}

        # Get members
        cursor = await db.execute("""
            SELECT creator_did, role, status, triggers_submitted, joined_at
            FROM pott_members WHERE pott_id = ? AND status = 'active'
            ORDER BY joined_at
        """, (pott_id,))
        pott["members"] = [dict(r) for r in await cursor.fetchall()]

        # Get recent featured
        cursor = await db.execute("""
            SELECT trigger_id, trigger_seal, creator_did, action, featured_at
            FROM pott_featured WHERE pott_id = ? AND action IN ('featured', 'pinned')
            ORDER BY position, featured_at DESC LIMIT 20
        """, (pott_id,))
        pott["featured"] = [dict(r) for r in await cursor.fetchall()]

        return pott


async def list_potts(
    vertical: str = None,
    status: str = "active",
    limit: int = 50,
    offset: int = 0
) -> List[Dict]:
    """List Potts for discovery."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        query = "SELECT id, name, vertical, description, curator_did, member_count, trigger_count, status, created_at FROM potts WHERE status = ?"
        params = [status]

        if vertical:
            query += " AND vertical = ?"
            params.append(vertical)

        query += " ORDER BY member_count DESC, created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        cursor = await db.execute(query, params)
        return [dict(r) for r in await cursor.fetchall()]


# ═══════════════════════════════════════════════════════════════════════════════════
# MEMBERSHIP OPERATIONS
# ═══════════════════════════════════════════════════════════════════════════════════

async def join_pott(
    pott_id: str,
    creator_did: str,
    role: str = "member",
    ledger_receipt: str = None
) -> Dict:
    """Join a Pott federation."""
    now = datetime.utcnow().isoformat()

    async with aiosqlite.connect(DB_PATH) as db:
        # Check if already member
        cursor = await db.execute(
            "SELECT id, status FROM pott_members WHERE pott_id = ? AND creator_did = ?",
            (pott_id, creator_did)
        )
        existing = await cursor.fetchone()

        if existing:
            if existing[1] == "active":
                return {"error": "Already a member", "status": "already_member"}
            # Rejoin
            await db.execute("""
                UPDATE pott_members SET status = 'active', left_at = NULL, joined_at = ?
                WHERE pott_id = ? AND creator_did = ?
            """, (now, pott_id, creator_did))
        else:
            await db.execute("""
                INSERT INTO pott_members (pott_id, creator_did, role, joined_at, ledger_receipt)
                VALUES (?, ?, ?, ?, ?)
            """, (pott_id, creator_did, role, now, ledger_receipt))

        # Update member count
        await db.execute("""
            UPDATE potts SET member_count = (
                SELECT COUNT(*) FROM pott_members WHERE pott_id = ? AND status = 'active'
            ), updated_at = ? WHERE id = ?
        """, (pott_id, now, pott_id))

        await db.commit()

    return {
        "pott_id": pott_id,
        "creator_did": creator_did,
        "role": role,
        "joined_at": now,
        "status": "joined"
    }


async def leave_pott(
    pott_id: str,
    creator_did: str,
    ledger_receipt: str = None
) -> Dict:
    """Leave a Pott (exit freedom - content stays with creator)."""
    now = datetime.utcnow().isoformat()

    async with aiosqlite.connect(DB_PATH) as db:
        # Check if curator (cannot leave)
        cursor = await db.execute(
            "SELECT role FROM pott_members WHERE pott_id = ? AND creator_did = ?",
            (pott_id, creator_did)
        )
        member = await cursor.fetchone()

        if not member:
            return {"error": "Not a member", "status": "not_member"}

        if member[0] == "curator":
            return {"error": "Curator cannot leave. Transfer ownership first.", "status": "curator_cannot_leave"}

        # Mark as left
        await db.execute("""
            UPDATE pott_members SET status = 'left', left_at = ?
            WHERE pott_id = ? AND creator_did = ?
        """, (now, pott_id, creator_did))

        # Update member count
        await db.execute("""
            UPDATE potts SET member_count = (
                SELECT COUNT(*) FROM pott_members WHERE pott_id = ? AND status = 'active'
            ), updated_at = ? WHERE id = ?
        """, (pott_id, now, pott_id))

        await db.commit()

    return {
        "pott_id": pott_id,
        "creator_did": creator_did,
        "left_at": now,
        "status": "left",
        "content_retained": True  # Exit freedom: creator keeps content
    }


# ═══════════════════════════════════════════════════════════════════════════════════
# CURATION OPERATIONS
# ═══════════════════════════════════════════════════════════════════════════════════

async def curate_trigger(
    pott_id: str,
    trigger_id: str,
    trigger_seal: str,
    creator_did: str,
    curator_did: str,
    action: str = "featured",
    position: int = 0,
    ledger_receipt: str = None
) -> Dict:
    """Curate a trigger (feature, pin, remove)."""
    now = datetime.utcnow().isoformat()

    async with aiosqlite.connect(DB_PATH) as db:
        # Verify curator has permission
        cursor = await db.execute("""
            SELECT role FROM pott_members
            WHERE pott_id = ? AND creator_did = ? AND status = 'active'
        """, (pott_id, curator_did))
        curator = await cursor.fetchone()

        if not curator or curator[0] not in ("curator", "moderator"):
            return {"error": "Not authorized to curate", "status": "unauthorized"}

        # Upsert featured entry
        await db.execute("""
            INSERT INTO pott_featured (pott_id, trigger_id, trigger_seal, creator_did,
                                       curator_did, action, position, featured_at, ledger_receipt)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(pott_id, trigger_id) DO UPDATE SET
                action = excluded.action,
                position = excluded.position,
                curator_did = excluded.curator_did,
                featured_at = excluded.featured_at,
                ledger_receipt = excluded.ledger_receipt
        """, (pott_id, trigger_id, trigger_seal, creator_did, curator_did,
              action, position, now, ledger_receipt))

        # Update trigger count if featured
        if action in ("featured", "pinned"):
            await db.execute("""
                UPDATE potts SET trigger_count = (
                    SELECT COUNT(*) FROM pott_featured
                    WHERE pott_id = ? AND action IN ('featured', 'pinned')
                ), updated_at = ? WHERE id = ?
            """, (pott_id, now, pott_id))

        await db.commit()

    return {
        "pott_id": pott_id,
        "trigger_id": trigger_id,
        "action": action,
        "curated_by": curator_did,
        "curated_at": now,
        "status": "curated"
    }


async def get_feed(pott_id: str, limit: int = 20, offset: int = 0) -> List[Dict]:
    """Get curated feed for a Pott."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        cursor = await db.execute("""
            SELECT trigger_id, trigger_seal, creator_did, action, position, featured_at
            FROM pott_featured
            WHERE pott_id = ? AND action IN ('featured', 'pinned')
            ORDER BY
                CASE action WHEN 'pinned' THEN 0 ELSE 1 END,
                position,
                featured_at DESC
            LIMIT ? OFFSET ?
        """, (pott_id, limit, offset))

        return [dict(r) for r in await cursor.fetchall()]


# ═══════════════════════════════════════════════════════════════════════════════════
# METRICS & REVENUE
# ═══════════════════════════════════════════════════════════════════════════════════

async def record_revenue(
    pott_id: str,
    trigger_id: str,
    creator_did: str,
    amount_total: float,
    split_creator: float = 0.85,
    split_pott: float = 0.15,
    source: str = "direct",
    ledger_receipt: str = None
) -> Dict:
    """Record a revenue event with 85/15 split."""
    now = datetime.utcnow().isoformat()
    amount_creator = round(amount_total * split_creator, 2)
    amount_pott = round(amount_total * split_pott, 2)

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO pott_revenue (pott_id, trigger_id, creator_did,
                                     amount_total, amount_creator, amount_pott,
                                     source, ledger_receipt, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (pott_id, trigger_id, creator_did, amount_total,
              amount_creator, amount_pott, source, ledger_receipt, now))

        await db.commit()

    return {
        "pott_id": pott_id,
        "trigger_id": trigger_id,
        "amount": {
            "total": amount_total,
            "creator": amount_creator,
            "pott": amount_pott
        },
        "split": {"creator": split_creator, "pott": split_pott},
        "recorded_at": now
    }


async def get_metrics(pott_id: str, days: int = 30) -> Dict:
    """Get aggregated metrics for a Pott."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        # Get pott info
        cursor = await db.execute(
            "SELECT name, member_count, trigger_count, status FROM potts WHERE id = ?",
            (pott_id,)
        )
        pott = await cursor.fetchone()
        if not pott:
            return None

        # Get revenue totals
        cursor = await db.execute("""
            SELECT
                COALESCE(SUM(amount_total), 0) as total_revenue,
                COALESCE(SUM(amount_creator), 0) as creator_revenue,
                COALESCE(SUM(amount_pott), 0) as pott_revenue,
                COUNT(*) as transaction_count
            FROM pott_revenue
            WHERE pott_id = ? AND created_at >= datetime('now', ?)
        """, (pott_id, f"-{days} days"))
        revenue = dict(await cursor.fetchone())

        # Get daily metrics
        cursor = await db.execute("""
            SELECT date, views, unique_viewers, triggers_added, members_joined
            FROM pott_metrics
            WHERE pott_id = ?
            ORDER BY date DESC LIMIT ?
        """, (pott_id, days))
        daily = [dict(r) for r in await cursor.fetchall()]

        return {
            "pott_id": pott_id,
            "name": pott["name"],
            "member_count": pott["member_count"],
            "trigger_count": pott["trigger_count"],
            "status": pott["status"],
            "period_days": days,
            "revenue": revenue,
            "daily": daily
        }
