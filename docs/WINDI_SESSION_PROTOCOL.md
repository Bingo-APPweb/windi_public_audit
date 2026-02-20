# WINDI Session Close Protocol v1.0
## Trigger: "Irmão, fecha a sessão" or "encerra" or "session close"

---

## What Claude Does Automatically:

### Step 1 — Memory Update
Update relevant memory slots (30 max) with:
- New services, ports, file locations
- Key decisions and architecture changes
- Workstream status changes
- New skills or procedures created

### Step 2 — Playbook Generation
Generate updated `WINDI_PLAYBOOK.md` with:
- New entries in Build History
- Updated Roadmap
- New/changed file locations
- New skills or procedures
- Updated service status

### Step 3 — Deliver Files
Use `present_files` to provide:
- `WINDI_PLAYBOOK.md` (updated)
- Any session-specific outputs (commit logs, prompts, etc.)

### Step 4 — Human Clipboard
Provide ready-to-paste commands:

```bash
# → Servidor Strato
scp "PATH_TO_PLAYBOOK" windi@87.106.29.233:/opt/windi/docs/WINDI_PLAYBOOK.md

# → Google Drive: drag & drop the file
```

---

## What the Human Does (max 30 seconds):

1. **Download** the Playbook from Claude's output
2. **Paste** the SCP command in terminal
3. **Drag** the file to Google Drive WINDI folder

---

## Session Open Protocol
When starting a new session:

### Option A — Quick Start (memory only)
Just start talking. Claude reads memory (30 slots) automatically.

### Option B — Full Context
Say: "Irmão, busca o WINDI Playbook no Drive"
Claude uses `google_drive_search` → `google_drive_fetch` → full context loaded.

### Option C — Upload
Drag `WINDI_PLAYBOOK.md` into the chat. Instant full context.

---

## Memory Slot Strategy

The 30 memory slots should be used as **pointers**, not details:
- Slot format: `TOPIC DATE: key=value. key=value. Location. Status.`
- Max 200 chars per slot
- Prioritize: WHAT changed, WHERE it lives, WHAT STATUS
- Details go in the Playbook, not memory

### Protected Slots (never delete):
- Jober identity + communication style
- Three Dragons Protocol
- Server SSH + domain map
- Design system (Noir/Klar/fonts)
- Zero-Knowledge Architecture principle
- Debug Rule
- Business model + tiers

### Rotating Slots (update frequently):
- Phase/WS status
- Routes and file locations
- Recent service changes
- Active workstream details

---

*"AI processes. Human decides. WINDI guarantees."*
