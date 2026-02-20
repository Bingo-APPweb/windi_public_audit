#!/usr/bin/env python3
"""
WINDI Communiqué Engine — Multimedia Integration Patcher
Patches communique_engine.py to add evidence endpoints.
Run on Strato: python3 /opt/windi/communique/patch_multimedia.py
"""

import os
import shutil
from datetime import datetime

ENGINE = "/opt/windi/communique/communique_engine.py"
BACKUP_DIR = "/opt/windi/communique/backups"

def main():
    print()
    print("  🐉 WINDI Multimedia Integration Patcher")
    print("  " + "─" * 45)
    print()

    if not os.path.exists(ENGINE):
        print(f"  ✗ Engine not found: {ENGINE}")
        return

    # Backup
    os.makedirs(BACKUP_DIR, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = os.path.join(BACKUP_DIR, f"communique_engine.py.bak-multimedia-{ts}")
    shutil.copy2(ENGINE, backup)
    print(f"  ✓ Backup: {backup}")

    with open(ENGINE, "r") as f:
        code = f.read()

    # Safety check
    if "HAS_MULTIMEDIA" in code:
        print("  ⚠ Already patched! Multimedia extension detected.")
        print("  Skipping to avoid duplicate patches.")
        return

    lines = code.split("\n")
    new_lines = []
    patched = {"import": False, "version": False, "routes": False, "handlers": False, "docs": False}

    i = 0
    while i < len(lines):
        line = lines[i]

        # ── PATCH 1: Import (after line 43) ──
        if not patched["import"] and line.strip().startswith("from communique_renderer import"):
            new_lines.append(line)
            new_lines.append("")
            new_lines.append("# Multimedia Evidence Extension")
            new_lines.append("try:")
            new_lines.append("    from communique_multimedia import load_evidence_manifest, verify_evidence_package, generate_evidence_gallery_html")
            new_lines.append("    HAS_MULTIMEDIA = True")
            new_lines.append("except ImportError:")
            new_lines.append("    HAS_MULTIMEDIA = False")
            patched["import"] = True
            print("  ✓ Patch 1/5: Multimedia import added (after line 43)")
            i += 1
            continue

        # ── PATCH 2: Version (line 46) ──
        if not patched["version"] and 'VERSION = "1.0.0"' in line:
            new_lines.append('VERSION = "1.1.0-multimedia"')
            patched["version"] = True
            print("  ✓ Patch 2/5: Version → 1.1.0-multimedia")
            i += 1
            continue

        # ── PATCH 3: Routes (before line 131 "# Public PDF download") ──
        if not patched["routes"] and "# Public PDF download" in line:
            new_lines.append("        # ── MULTIMEDIA EVIDENCE ROUTES ──────────────────────")
            new_lines.append("")
            new_lines.append("        # Evidence gallery page")
            new_lines.append('        m = re.match(r"^/communique/(COM-\\d{8}-\\d{4})/evidence$", path)')
            new_lines.append("        if m:")
            new_lines.append("            return self._handle_evidence_gallery(m.group(1))")
            new_lines.append("")
            new_lines.append("        # Evidence verification (package-level)")
            new_lines.append('        m = re.match(r"^/communique/(COM-\\d{8}-\\d{4})/evidence/verify$", path)')
            new_lines.append("        if m:")
            new_lines.append("            return self._handle_evidence_verify(m.group(1))")
            new_lines.append("")
            new_lines.append("        # Evidence manifest")
            new_lines.append('        m = re.match(r"^/communique/(COM-\\d{8}-\\d{4})/evidence/manifest$", path)')
            new_lines.append("        if m:")
            new_lines.append("            return self._handle_evidence_manifest(m.group(1))")
            new_lines.append("")
            new_lines.append(line)  # Keep original "# Public PDF download"
            patched["routes"] = True
            print("  ✓ Patch 3/5: Evidence routes added (before PDF route)")
            i += 1
            continue

        # ── PATCH 4: Handlers (before _handle_feed_html, line 416) ──
        if not patched["handlers"] and "def _handle_feed_html(self):" in line:
            new_lines.append("    # ─── MULTIMEDIA EVIDENCE HANDLERS ─────────────────────")
            new_lines.append("")
            new_lines.append("    def _handle_evidence_gallery(self, com_id):")
            new_lines.append('        """Evidence gallery page for multimedia communiqué."""')
            new_lines.append("        if not HAS_MULTIMEDIA:")
            new_lines.append('            return self.send_json({"error": "Multimedia extension not available"}, 501)')
            new_lines.append("        manifest, jmpg_path = load_evidence_manifest(com_id)")
            new_lines.append("        if manifest is None:")
            new_lines.append('            return self.send_json({"error": "No evidence package found", "communique_id": com_id}, 404)')
            new_lines.append("        html = generate_evidence_gallery_html(com_id, manifest)")
            new_lines.append("        self.send_html(html)")
            new_lines.append("")
            new_lines.append("    def _handle_evidence_verify(self, com_id):")
            new_lines.append('        """Verify evidence package for a communiqué."""')
            new_lines.append("        if not HAS_MULTIMEDIA:")
            new_lines.append('            return self.send_json({"error": "Multimedia extension not available"}, 501)')
            new_lines.append("        result = verify_evidence_package(com_id)")
            new_lines.append("        self.send_json(result)")
            new_lines.append("")
            new_lines.append("    def _handle_evidence_manifest(self, com_id):")
            new_lines.append('        """Return evidence package manifest.json."""')
            new_lines.append("        if not HAS_MULTIMEDIA:")
            new_lines.append('            return self.send_json({"error": "Multimedia extension not available"}, 501)')
            new_lines.append("        manifest, _ = load_evidence_manifest(com_id)")
            new_lines.append("        if manifest is None:")
            new_lines.append('            return self.send_json({"error": "No evidence package found"}, 404)')
            new_lines.append("        self.send_json(manifest)")
            new_lines.append("")
            new_lines.append(line)  # Keep original _handle_feed_html
            patched["handlers"] = True
            print("  ✓ Patch 4/5: Evidence handler methods added")
            i += 1
            continue

        # ── PATCH 5: Docstring (after "GET  /communique/feed.json" line 26) ──
        if not patched["docs"] and "GET  /communique/feed.json" in line:
            new_lines.append(line)
            new_lines.append("")
            new_lines.append("    MULTIMEDIA:")
            new_lines.append("      GET  /communique/{id}/evidence          → Evidence gallery page")
            new_lines.append("      GET  /communique/{id}/evidence/verify   → Evidence package verification")
            new_lines.append("      GET  /communique/{id}/evidence/manifest → Evidence manifest JSON")
            patched["docs"] = True
            print("  ✓ Patch 5/5: Docstring updated with multimedia endpoints")
            i += 1
            continue

        new_lines.append(line)
        i += 1

    # Write
    with open(ENGINE, "w") as f:
        f.write("\n".join(new_lines))

    # Summary
    print()
    print("  " + "─" * 45)
    total = sum(1 for v in patched.values() if v)
    if total == 5:
        print(f"  ✓ ALL {total}/5 PATCHES APPLIED SUCCESSFULLY")
    else:
        failed = [k for k, v in patched.items() if not v]
        print(f"  ⚠ {total}/5 patches applied. Missing: {failed}")

    print()
    print("  Next:")
    print('    python3 -c "import py_compile; py_compile.compile(\'/opt/windi/communique/communique_engine.py\', doraise=True)"')
    print("    sudo systemctl restart windi-communique")
    print("    curl -s http://localhost:8105/health | python3 -m json.tool")
    print()

if __name__ == "__main__":
    main()
