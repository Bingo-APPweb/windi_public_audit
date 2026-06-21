# SECURITY-INCIDENT-001 — DEEPEVAL API KEY EXPOSURE

**Status:** SEALED
**Date Discovered:** 2026-06-21
**Date Remediated:** 2026-06-21
**Discovered By:** CCode audit of dirty git tree
**Invariants:** I9 (irremediável), I11 (evidência)

---

## 1. Summary

During routine audit of untracked files (427 lines in git status), CCode discovered that `w-enterprise-001/.env.local` containing a DeepEval API key was committed to the public repository `windi_public_audit`. The key was live, had been exposed for ~57 days, but was never used by an attacker.

## 2. Exposed Secret

```
File: w-enterprise-001/.env.local
Key: DEEPEVAL_API_KEY="confident_us_xoL0g..." (redacted)
Repository: github.com/Bingo-APPweb/windi_public_audit (PUBLIC)
Visibility: HTTP 200 = publicly accessible
Exposure window: 57 days (25 Apr - 21 Jun 2026)
```

## 3. Timeline

| Timestamp | Event |
|-----------|-------|
| 2026-04-25 23:15 | Key created in DeepEval (account: WINDI Publishing House) |
| 2026-04-25 23:27:59 | File first committed (§204.4 DeepEval integration) |
| 2026-04-26 | File modified (§204.6 Langfuse layer) |
| 2026-06-21 ~10:30 | Discovery during git tree audit |
| 2026-06-21 ~10:45 | REST API tests inconclusive |
| 2026-06-21 10:38 | Key rotated in DeepEval dashboard (new: WINDI-HIOS) |
| 2026-06-21 10:43 | File removed from git tracking |
| 2026-06-21 10:45 | .gitignore hardened |
| 2026-06-21 10:47 | Backup created |
| 2026-06-21 10:49 | History cleaned (git filter-repo, 2647 commits rewritten) |
| 2026-06-21 10:51 | Force push to GitHub |
| 2026-06-21 10:52 | Receipt sealed |

## 4. Risk Assessment

| Factor | Status |
|--------|--------|
| Repository visibility | PUBLIC |
| Key validity at discovery | **LIVE** (confirmed via dashboard) |
| Account ownership | **WINDI Publishing House** (Human Dragon) |
| Other secrets in file | NONE (LANGFUSE keys were empty) |
| Last Used (per dashboard) | **NEVER** — no exploitation detected |

## 5. Verification Results

### 5.1 REST API Tests

```
Bearer token     → 401 "No API KEY provided"
X-API-KEY        → 401 "No API KEY provided"
Query param      → 401 "No API KEY provided"
Basic auth       → 401 "No API KEY provided"
```

**Interpretation:** DeepEval API requires CLI/SDK auth flow. REST tests inconclusive.

### 5.2 Dashboard Verification

**Status:** COMPLETE
**Verified by:** Human Dragon

- [x] Account exists (WINDI Publishing House)
- [x] Key visible in dashboard (Default Key, created Apr 25)
- [x] Key rotated (new key: WINDI-HIOS, created Jun 21 10:38)
- [x] Old key deleted from dashboard
- [x] Last Used: Never (no exploitation)

## 6. Remediation Executed

### 6.1 Key Rotation

- Old key: `confident_us_xoL0g...` — **REVOKED**
- New key: `confident_us_org_K3Uer...` — Active, stored in protected `.env.local`

### 6.2 Git Hardening

- `w-enterprise-001/.env.local` removed from tracking (`git rm --cached`)
- `.gitignore` hardened with patterns:
  ```
  .env.*
  .env.local
  **/.env
  **/.env.*
  **/.env.local
  ```

### 6.3 History Cleanup

- Backup: `_security-backup-20260621/repo-before-cleanup.bundle` (1GB)
- Tool: `python3 -m git_filter_repo --invert-paths --path w-enterprise-001/.env.local --force`
- Commits rewritten: 2647
- Duration: 97.34 seconds
- Force push: `main -> main (forced update)`

### 6.4 Prevention

- `.gitignore` patterns block future `.env.*` commits
- Audit discovered the gap — 427 untracked files were the symptom
- Pre-commit hook for secret detection: RECOMMENDED (future)

## 7. Lessons Learned

1. **The dirty tree was the symptom.** 427 untracked files masked the real problem.
2. **Audit found what gitignore missed.** The file was committed before gitignore existed for it.
3. **Public repo = immediate exposure.** No grace period for secrets in public history.
4. **"Last Used: Never" saved us.** The key was live but unexploited.
5. **Sequence matters:** Revoke first, clean history second. A live key during cleanup is still a live key.

## 8. Receipt

```
receipt_id: WINDI-SECURITY-INCIDENT-001-20260621105200
type: security_incident
severity: HIGH (key was live, public repo)
outcome: REMEDIATED
exposure_days: 57
exploitation: NONE
commits_rewritten: 2647
invariants: [I9, I11]
```

---

*Liga IA+H — Kempten, Bavaria · 2026-06-21*
*"O ferimento documentado, não escondido."*
