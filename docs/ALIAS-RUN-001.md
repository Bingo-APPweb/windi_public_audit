# ALIAS-RUN-001

**Status:** MEASURED
**Generated at:** 2026-06-13T09:03:48+00:00
**Rule:** ALIAS-RESOLUTION-001 v0.1
**Authority Gate:** ACTION-0-WITNESS-ADMISSIBILITY-001

## 1. Summary

- Target actors measured: 10
- Receipts covered by target actors: 53
- Automatic resolved actors: 1
- Pending review actors: 5
- System executor actors: 4
- Unresolved actors: 0

## 2. Collapsed Receipts by Canonical DID

- `did:windi:dragon-001`: 6 receipts

## 3. Actor Resolution Table

| actor_original | receipts | resolution_status | resolution_class | canonical_did | admissibility_level | evidence |
|---|---:|---|---|---|---|---|
| `dragon@windi-domain.com` | 11 | `pending_review` | `STRONG_CANDIDATE` | `null` | `LEVEL 2 REQUIRED if mapped to founder DID` | dragon/human-dragon textual pattern without formal alias |
| `hios-forge-001` | 10 | `system_executor` | `SYSTEM_EXECUTOR` | `null` | `N/A` | system/lab/forge/production actor pattern |
| `windi-hd-001` | 7 | `pending_review` | `STRONG_CANDIDATE` | `null` | `LEVEL 2 REQUIRED if mapped to founder DID` | dragon/human-dragon textual pattern without formal alias |
| `dragon-001` | 6 | `resolved` | `SOVEREIGN_NAME_MATCH` | `did:windi:dragon-001` | `LEVEL 1` | identities.sovereign_name exact active match |
| `windi:hd:human-dragon` | 6 | `pending_review` | `STRONG_CANDIDATE` | `null` | `LEVEL 2 REQUIRED if mapped to founder DID` | dragon/human-dragon textual pattern without formal alias |
| `W-HUMANDRAGON-001` | 4 | `pending_review` | `STRONG_CANDIDATE` | `null` | `LEVEL 2 REQUIRED if mapped to founder DID` | dragon/human-dragon textual pattern without formal alias |
| `hios-cinema-production` | 4 | `system_executor` | `SYSTEM_EXECUTOR` | `null` | `N/A` | system/lab/forge/production actor pattern |
| `WINDI-SYSTEM` | 2 | `system_executor` | `SYSTEM_EXECUTOR` | `null` | `N/A` | system/lab/forge/production actor pattern |
| `windi-hios-cinema-lab` | 2 | `system_executor` | `SYSTEM_EXECUTOR` | `null` | `N/A` | system/lab/forge/production actor pattern |
| `HD-DRAGON-001` | 1 | `pending_review` | `STRONG_CANDIDATE` | `null` | `LEVEL 2 REQUIRED if mapped to founder DID` | dragon/human-dragon textual pattern without formal alias |

## 4. Findings

1. Only rules already formalized in DID Genesis resolve automatically.
2. `dragon-001` resolves via `SOVEREIGN_NAME_MATCH`, but remains marked review-required.
3. Strong Human Dragon candidates remain pending until formal aliases are approved.
4. System/lab/forge/production actors remain Activity actors, not Contribution actors by default.
5. `dragon@windi-domain.com` remains Priority Alias Candidate #1 because it has the largest pending Human Dragon-like receipt count.

## 5. Guard

> Um run de medicao sem identidade resolvida nao e ainda uma atribuicao.
