# WINDI Communiqué Composer v1.1 — Deploy Package

## What This Does

1. **Relocates** Export Engine and JMPG Viewer to canonical paths (Location Matrix v1.0)
2. **Installs** Communiqué Composer v1.1 into Desktop (:8100)
3. **Creates** systemd services for :8103, :8104, :8105
4. **Updates** nginx routes for /export/ and /communique/
5. **Smoke tests** all ports and services

## Canonical Path Alignment

| Service          | Port  | OLD path (wrong)             | NEW path (canonical)        |
|------------------|-------|------------------------------|-----------------------------|
| Export Engine    | :8103 | /opt/windi/desktop/export/   | /opt/windi/export-engine/   |
| JMPG Viewer     | :8104 | /opt/windi/desktop/jmpg/     | /opt/windi/jmpg-viewer/     |
| Communiqué Eng.  | :8105 | (new)                        | /opt/windi/communique/      |
| Composer v1.1    | :8100 | (new)                        | /opt/windi/desktop/composer/ |

## Deploy

```bash
# 1. Upload from Windows
scp "D:\WINDI-LLM\composer-deploy\Composer-Deploy-v11.zip" windi@87.106.29.233:/opt/windi/

# 2. On Strato
cd /opt/windi
unzip -o Composer-Deploy-v11.zip -d composer-deploy
cd composer-deploy
bash deploy_composer_v11.sh
```

## v1.1 Patches (Architect + Guardian)

- ✔ Canonical JSON (sorted keys) — hash JS === hash Python
- ✔ schema_version + created_at + origin in payload
- ✔ Validation gate (title + author required)
- ✔ Strong irreversible publish confirmation
- ✔ Post-publish Viewer + Public Page buttons
- ✔ Wallet Ed25519 placeholder (:8099)
- ✔ Media dropzone placeholder
- ✔ Autosave indicator

## Pipeline

```
Composer (Desktop :8100)
    ├── ◆ Publish → Communiqué Engine (:8105) → Ledger (:8101)
    └── 📰 Export  → Export Engine (:8103) → .jmpg → Viewer (:8104)
```

"AI processes. Human decides. WINDI guarantees."
