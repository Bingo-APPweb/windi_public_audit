# Schema Versioning Policy — WINDI-HIOS Kernel

```
STATUS:         DRAFT-SKELETON
NOT SEALED
NOT CANONICAL
PENDING GUARDIAN REVIEW
```

---

## Purpose

Define how schemas evolve without breaking the Kernel.

---

## Versioning Format

**Semantic Versioning:** `MAJOR.MINOR.PATCH`

| Component | Meaning | Compatibility |
|-----------|---------|---------------|
| MAJOR | Breaking changes | NOT backwards compatible |
| MINOR | New features | Backwards compatible |
| PATCH | Bug fixes | Backwards compatible |

---

## Sealed Schema Policy

**Sealed schemas are IMMUTABLE.**

Once a schema is sealed (part of a sealed §):
- Content cannot change
- Hash is permanent
- New version required for any change

---

## Version Lifecycle

```
1. DRAFT     → Schema in development
2. REVIEW    → Guardian reviewing
3. APPROVED  → Human Dragon approved
4. SEALED    → Part of sealed § (immutable)
5. DEPRECATED → Superseded by newer version
6. ARCHIVED  → No longer in active use
```

---

## Migration Requirements

### MAJOR Version Bump

Required when:
- Removing required fields
- Changing field types
- Changing enum values

Migration must include:
- Migration script (or manual procedure)
- Backwards compatibility period (if any)
- Deadline for old version deprecation
- Human Dragon approval

### MINOR Version Bump

Required when:
- Adding optional fields
- Adding enum values
- Extending functionality

Migration:
- No migration required
- Old data remains valid

### PATCH Version Bump

Required when:
- Fixing validation bugs
- Improving descriptions
- Non-functional changes

Migration:
- None required

---

## Schema Hash Verification

Each schema has canonical hash:

```
sha256(schema_content) → schema_hash
```

Verification at runtime:
1. Load schema from disk
2. Compute hash
3. Compare against known-good hash
4. If mismatch → schema corruption detected

---

## §264 CBP-JSON Schema v0.3

This policy prepares for §264:
- CBP schema will follow this versioning
- Migration from v0.2 to v0.3 documented
- Backwards compatibility maintained

---

## Open Questions (Versioning)

- Q26: Schema registry location?
- Q27: Automated migration tooling?
- Q28: Multi-version coexistence period?

---

*Schema Versioning Policy · DRAFT-SKELETON*
*Liga IA+H · Kempten, Bavaria · 2026*
