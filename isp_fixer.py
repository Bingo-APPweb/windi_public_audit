#!/usr/bin/env python3
"""
WINDI ISP Fixer v1.0
Fixes Mustache/Jinja2 template conflicts detected by isp_scanner.py

Usage:
    python3 isp_fixer.py --dry-run    # Preview changes without applying
    python3 isp_fixer.py --fix        # Apply fixes with backup
    python3 isp_fixer.py --restore    # Restore from latest backup
"""

import os
import re
import sys
import shutil
import argparse
from datetime import datetime
from pathlib import Path

# Configuration
ISP_DIR = "/opt/windi/isp"
BACKUP_DIR = "/opt/windi/backups/isp_fixer"
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

# Terminal colors
class C:
    OK = "\033[92m"
    WARN = "\033[93m"
    FAIL = "\033[91m"
    INFO = "\033[94m"
    BOLD = "\033[1m"
    END = "\033[0m"

def log_ok(msg): print(f"{C.OK}[OK]{C.END} {msg}")
def log_warn(msg): print(f"{C.WARN}[WARN]{C.END} {msg}")
def log_fail(msg): print(f"{C.FAIL}[FAIL]{C.END} {msg}")
def log_info(msg): print(f"{C.INFO}[INFO]{C.END} {msg}")


class MustacheJinjaFixer:
    """
    Fixes Mustache {{#section}}...{{/section}} blocks that conflict with Jinja2.

    Strategy: Wrap Mustache blocks in {% raw %}...{% endraw %}
    """

    # Mustache patterns that conflict with Jinja2
    MUSTACHE_SECTION_START = re.compile(r'\{\{#(\w+)\}\}')
    MUSTACHE_SECTION_END = re.compile(r'\{\{/(\w+)\}\}')
    MUSTACHE_INVERTED = re.compile(r'\{\{\^(\w+)\}\}')

    def __init__(self, dry_run=False):
        self.dry_run = dry_run
        self.fixes_applied = []
        self.files_modified = []

    def find_mustache_sections(self, content):
        """Find all Mustache section blocks in content."""
        sections = []

        # Find all section starts
        for match in self.MUSTACHE_SECTION_START.finditer(content):
            section_name = match.group(1)
            start_pos = match.start()

            # Find corresponding end tag
            end_pattern = re.compile(rf'\{{\{{\/{section_name}\}}\}}')
            end_match = end_pattern.search(content, start_pos)

            if end_match:
                sections.append({
                    'name': section_name,
                    'start': start_pos,
                    'end': end_match.end(),
                    'content': content[start_pos:end_match.end()]
                })

        return sections

    def is_already_wrapped(self, content, pos):
        """Check if position is already inside a {% raw %} block."""
        # Look backwards for {% raw %}
        before = content[:pos]
        raw_starts = len(re.findall(r'\{% raw %\}', before))
        raw_ends = len(re.findall(r'\{% endraw %\}', before))
        return raw_starts > raw_ends

    def fix_file(self, filepath):
        """Fix Mustache/Jinja2 conflicts in a single file."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                original = f.read()
        except Exception as e:
            log_fail(f"Cannot read {filepath}: {e}")
            return None

        content = original
        sections = self.find_mustache_sections(content)

        if not sections:
            return None  # No changes needed

        # Check which sections need wrapping
        fixes = []
        for section in sections:
            if not self.is_already_wrapped(content, section['start']):
                fixes.append(section)

        if not fixes:
            log_info(f"{filepath}: Mustache sections already wrapped")
            return None

        # Apply fixes (from end to start to preserve positions)
        fixes.sort(key=lambda x: x['start'], reverse=True)

        for fix in fixes:
            # Wrap the entire section in {% raw %}...{% endraw %}
            wrapped = f"{{% raw %}}{fix['content']}{{% endraw %}}"
            content = content[:fix['start']] + wrapped + content[fix['end']:]

            self.fixes_applied.append({
                'file': filepath,
                'section': fix['name'],
                'action': 'wrapped in {% raw %}...{% endraw %}'
            })

        if content != original:
            self.files_modified.append(filepath)
            return content

        return None

    def backup_file(self, filepath):
        """Create backup of file before modification."""
        backup_path = Path(BACKUP_DIR) / TIMESTAMP / Path(filepath).relative_to(ISP_DIR)
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(filepath, backup_path)
        return backup_path

    def process_directory(self, directory):
        """Process all HTML files in directory."""
        html_files = list(Path(directory).rglob("*.html"))

        log_info(f"Scanning {len(html_files)} HTML files in {directory}")
        print()

        for filepath in html_files:
            filepath_str = str(filepath)
            rel_path = filepath.relative_to(ISP_DIR)

            fixed_content = self.fix_file(filepath_str)

            if fixed_content:
                if self.dry_run:
                    log_warn(f"{rel_path}: Would fix {len([f for f in self.fixes_applied if f['file'] == filepath_str])} Mustache sections")
                else:
                    # Backup and write
                    backup = self.backup_file(filepath_str)
                    with open(filepath_str, 'w', encoding='utf-8') as f:
                        f.write(fixed_content)
                    log_ok(f"{rel_path}: Fixed, backup at {backup}")

    def report(self):
        """Print summary report."""
        print()
        print(f"{C.BOLD}{'='*60}{C.END}")
        print(f"{C.BOLD}  ISP FIXER REPORT{C.END}")
        print(f"{'='*60}")
        print(f"  Mode:          {'DRY RUN' if self.dry_run else 'APPLIED'}")
        print(f"  Files scanned: {len(list(Path(ISP_DIR).rglob('*.html')))}")
        print(f"  Files modified: {len(self.files_modified)}")
        print(f"  Fixes applied: {len(self.fixes_applied)}")

        if self.fixes_applied:
            print()
            print(f"{C.BOLD}  Fixes:{C.END}")
            for fix in self.fixes_applied:
                rel = Path(fix['file']).relative_to(ISP_DIR)
                print(f"    - {rel}: {{{{#{fix['section']}}}}} {fix['action']}")

        if not self.dry_run and self.files_modified:
            print()
            print(f"{C.INFO}  Backups saved to: {BACKUP_DIR}/{TIMESTAMP}/{C.END}")

        print(f"{'='*60}")

        if self.dry_run and self.fixes_applied:
            print(f"\n{C.WARN}Run with --fix to apply these changes{C.END}")


def restore_backup():
    """Restore from the latest backup."""
    backup_base = Path(BACKUP_DIR)
    if not backup_base.exists():
        log_fail("No backups found")
        return False

    # Find latest backup
    backups = sorted([d for d in backup_base.iterdir() if d.is_dir()], reverse=True)
    if not backups:
        log_fail("No backup directories found")
        return False

    latest = backups[0]
    log_info(f"Restoring from backup: {latest}")

    for backup_file in latest.rglob("*.html"):
        rel_path = backup_file.relative_to(latest)
        target = Path(ISP_DIR) / rel_path
        shutil.copy2(backup_file, target)
        log_ok(f"Restored: {rel_path}")

    return True


def main():
    parser = argparse.ArgumentParser(
        description="WINDI ISP Fixer - Fix Mustache/Jinja2 template conflicts",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 isp_fixer.py --dry-run    # Preview changes
  python3 isp_fixer.py --fix        # Apply fixes
  python3 isp_fixer.py --restore    # Restore from backup
        """
    )
    parser.add_argument('--dry-run', action='store_true', help='Preview changes without applying')
    parser.add_argument('--fix', action='store_true', help='Apply fixes with backup')
    parser.add_argument('--restore', action='store_true', help='Restore from latest backup')
    parser.add_argument('--dir', default=ISP_DIR, help=f'ISP directory (default: {ISP_DIR})')

    args = parser.parse_args()

    if not any([args.dry_run, args.fix, args.restore]):
        parser.print_help()
        sys.exit(1)

    print(f"""
{C.BOLD}{C.INFO}
╔══════════════════════════════════════════════════════════════╗
║              WINDI ISP FIXER v1.0                            ║
║     Mustache/Jinja2 Conflict Resolution                      ║
╚══════════════════════════════════════════════════════════════╝
{C.END}""")

    if args.restore:
        success = restore_backup()
        sys.exit(0 if success else 1)

    # Run fixer
    fixer = MustacheJinjaFixer(dry_run=args.dry_run)
    fixer.process_directory(args.dir)
    fixer.report()

    sys.exit(0 if not fixer.fixes_applied or not args.dry_run else 0)


if __name__ == "__main__":
    main()
