#!/usr/bin/env python3
"""
WINDI Cycle Report Generator v1.0 — Three Dragons Protocol
============================================================

Integrates JSON report generation with HTML template rendering
and PDF export for complete governance cycle documentation.

Principle: "The template NEVER decides the level. The API decides."

Author: WINDI Publishing House / Three Dragons Protocol
License: Proprietary — WINDI Governance Framework
"""

import json
import os
import subprocess
import argparse
import glob
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

try:
    from jinja2 import Template, Environment, FileSystemLoader
    JINJA2_AVAILABLE = True
except ImportError:
    JINJA2_AVAILABLE = False
    print("Warning: jinja2 not available. Install with: pip install jinja2")

# Import the report generator
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from governance_cycle_report import GovernanceCycleReport, generate_cycle_id, sha256_hash


class CycleReportGenerator:
    """
    Generates complete governance cycle reports in multiple formats.

    Integrates:
    - GovernanceCycleReport for canonical JSON generation
    - Jinja2 template for HTML rendering
    - wkhtmltopdf for PDF conversion
    """

    def __init__(self, template_dir: str = '/opt/windi/engine/templates/'):
        """
        Initialize the generator.

        Args:
            template_dir: Directory containing Jinja2 templates
        """
        self.template_dir = template_dir
        self.report_generator = GovernanceCycleReport()

        if JINJA2_AVAILABLE:
            self.env = Environment(
                loader=FileSystemLoader(template_dir),
                autoescape=True
            )
        else:
            self.env = None

    def generate_html(self, report_dict: Dict) -> str:
        """
        Render the HTML template with report data.

        Args:
            report_dict: Complete report dictionary

        Returns:
            Rendered HTML string
        """
        if not JINJA2_AVAILABLE or not self.env:
            raise RuntimeError("jinja2 is required for HTML generation")

        template = self.env.get_template('governance_cycle_report.html')
        return template.render(report=report_dict)

    def generate_pdf(self, report_dict: Dict, output_path: str) -> str:
        """
        Generate PDF from report using wkhtmltopdf.

        Args:
            report_dict: Complete report dictionary
            output_path: Path for the output PDF

        Returns:
            Path to the generated PDF
        """
        # First generate HTML
        html_content = self.generate_html(report_dict)

        # Write temporary HTML file
        temp_html = output_path.replace('.pdf', '_temp.html')
        with open(temp_html, 'w', encoding='utf-8') as f:
            f.write(html_content)

        # Convert to PDF using wkhtmltopdf
        try:
            result = subprocess.run(
                [
                    'wkhtmltopdf',
                    '--quiet',
                    '--enable-local-file-access',
                    '--page-size', 'A4',
                    '--margin-top', '15mm',
                    '--margin-bottom', '15mm',
                    '--margin-left', '15mm',
                    '--margin-right', '15mm',
                    '--encoding', 'UTF-8',
                    temp_html,
                    output_path
                ],
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode != 0:
                print(f"Warning: wkhtmltopdf returned {result.returncode}")
                if result.stderr:
                    print(f"stderr: {result.stderr[:500]}")

        except FileNotFoundError:
            raise RuntimeError("wkhtmltopdf not found. Install with: apt-get install wkhtmltopdf")
        except subprocess.TimeoutExpired:
            raise RuntimeError("PDF generation timed out")
        finally:
            # Clean up temp file
            if os.path.exists(temp_html):
                os.remove(temp_html)

        return output_path

    def generate_full_report(self, cycle_dir: str, output_dir: str,
                            formats: List[str] = None,
                            authority: str = None,
                            scope: str = None) -> Dict[str, str]:
        """
        Generate complete report in all requested formats.

        Args:
            cycle_dir: Directory containing Maestro case files
            output_dir: Output directory for generated files
            formats: List of formats to generate ['json', 'html', 'pdf']
            authority: Human authority for sovereign decision
            scope: Scope description

        Returns:
            Dictionary mapping format to output file path
        """
        if formats is None:
            formats = ['json', 'html', 'pdf']

        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)

        # Load cases
        cycle_data = scan_maestro_cases(cycle_dir)
        if authority:
            cycle_data["authority"] = authority
        if scope:
            cycle_data["scope"] = scope

        # Generate canonical JSON report
        report = self.report_generator.generate_from_maestro(cycle_data)

        # Seal the report
        seal_hash = self.report_generator.seal_report(report)
        report["seal"]["report_seal_hash"] = seal_hash
        report["seal"]["ledger_entry_reference"] = f"LEDGER-{report['cycle_id']}"

        # Generate outputs
        outputs = {}
        base_name = f"governance_cycle_report_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"

        # JSON
        if 'json' in formats or 'all' in formats:
            json_path = os.path.join(output_dir, f"{base_name}.json")
            self.report_generator.save_json(report, json_path)
            outputs['json'] = json_path

        # HTML
        if 'html' in formats or 'all' in formats:
            html_path = os.path.join(output_dir, f"{base_name}.html")
            html_content = self.generate_html(report)
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            outputs['html'] = html_path

        # PDF
        if 'pdf' in formats or 'all' in formats:
            pdf_path = os.path.join(output_dir, f"{base_name}.pdf")
            try:
                self.generate_pdf(report, pdf_path)
                outputs['pdf'] = pdf_path
            except Exception as e:
                print(f"Warning: PDF generation failed: {e}")
                outputs['pdf_error'] = str(e)

        # Register in forensic ledger
        self._register_in_ledger(report)

        return outputs

    def _register_in_ledger(self, report: Dict) -> None:
        """Register report generation in forensic ledger."""
        ledger_path = '/opt/windi/data/forensic_ledger.json'

        # Load or create ledger
        if os.path.exists(ledger_path):
            with open(ledger_path, 'r', encoding='utf-8') as f:
                ledger = json.load(f)
        else:
            os.makedirs(os.path.dirname(ledger_path), exist_ok=True)
            ledger = {"entries": [], "version": "1.0.0"}

        # Add entry
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "cycle_id": report.get("cycle_id", ""),
            "report_hash": report.get("seal", {}).get("report_seal_hash", ""),
            "type": "GOVERNANCE_CYCLE_REPORT",
            "findings_count": report.get("executive_summary", {}).get("total_findings", 0),
            "authority": report.get("sovereign_decision", {}).get("authority", "")
        }
        ledger["entries"].append(entry)

        # Save ledger
        with open(ledger_path, 'w', encoding='utf-8') as f:
            json.dump(ledger, f, indent=2, ensure_ascii=False)


def scan_maestro_cases(cycle_dir: str) -> Dict[str, Any]:
    """
    Scan directory for Maestro case files and findings.

    Args:
        cycle_dir: Directory to scan

    Returns:
        Cycle data dictionary with findings list
    """
    findings = []

    # Check various possible locations
    search_paths = [
        cycle_dir,
        os.path.join(cycle_dir, "cases"),
        os.path.join(cycle_dir, "findings"),
        "/opt/windi/agents/maestro/cases",
        "/opt/windi/agents/maestro/reports"
    ]

    for search_path in search_paths:
        if not os.path.exists(search_path):
            continue

        for filepath in glob.glob(os.path.join(search_path, "*.json")):
            # Skip if it's already a report
            basename = os.path.basename(filepath).lower()
            if 'report' in basename or 'cycle_report' in basename:
                continue

            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # Handle different data formats
                if isinstance(data, list):
                    findings.extend(data)
                elif isinstance(data, dict):
                    if "findings" in data:
                        findings.extend(data["findings"])
                    elif "finding_id" in data:
                        findings.append(data)
                    elif "registered_details" in data:
                        # Maestro ingest output format
                        for detail in data["registered_details"]:
                            findings.append({
                                "finding_id": detail.get("finding_id", ""),
                                "severity": detail.get("severity", "R3"),
                                "source_agent": "maestro",
                                "timeline": {
                                    "registered": detail.get("sla_acknowledge", ""),
                                    "routed": detail.get("routed_to", ""),
                                }
                            })

            except (json.JSONDecodeError, IOError) as e:
                print(f"Warning: Could not load {filepath}: {e}")

    # Also try to load from Maestro SQLite state
    maestro_db = "/opt/windi/agents/maestro/state/maestro_state.db"
    if os.path.exists(maestro_db):
        try:
            import sqlite3
            conn = sqlite3.connect(maestro_db)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM governance_cycles
            """)

            for row in cursor.fetchall():
                row_dict = dict(row)
                findings.append({
                    "finding_id": row_dict.get("finding_id", ""),
                    "source_agent": row_dict.get("source_agent", ""),
                    "severity": row_dict.get("severity", "R3"),
                    "category": row_dict.get("category", ""),
                    "summary": row_dict.get("summary", ""),
                    "resolution_note": row_dict.get("resolution_note", ""),
                    "decided_by": row_dict.get("assigned_to", ""),
                    "virtue_receipts": json.loads(row_dict.get("receipt_chain", "[]")),
                    "timeline": {
                        "registered": row_dict.get("created_at", ""),
                        "routed": "",
                        "acknowledged": row_dict.get("acknowledged_at", ""),
                        "resolved": row_dict.get("resolved_at", ""),
                        "closed": row_dict.get("closed_at", "")
                    }
                })

            conn.close()

        except Exception as e:
            print(f"Warning: Could not read Maestro state DB: {e}")

    # Deduplicate by finding_id
    seen = set()
    unique_findings = []
    for f in findings:
        fid = f.get("finding_id", "")
        if fid and fid not in seen:
            seen.add(fid)
            unique_findings.append(f)

    return {
        "findings": unique_findings,
        "authority": "Human Dragon — Chief Governance Officer",
        "scope": "Governance Cycle Audit"
    }


def create_sample_data(output_dir: str) -> str:
    """
    Create sample cycle data for testing.

    Args:
        output_dir: Directory to create sample data in

    Returns:
        Path to created sample data file
    """
    os.makedirs(output_dir, exist_ok=True)

    sample_data = {
        "cycle_id": generate_cycle_id(),
        "findings": [
            {
                "finding_id": "ISP-alerts_20260208_085840",
                "origin_agent": "isp-manager",
                "severity": "R2",
                "category": "ISP-V003",
                "summary": "Missing required fields in ISP profile",
                "invariants": [],
                "virtue_receipts": [
                    "MAESTRO-20260208-185045-a50fb659",
                    "MAESTRO-20260208-185321-584b3332",
                    "MAESTRO-20260208-185411-b9b5af9f"
                ],
                "timeline": {
                    "registered": "2026-02-08T18:50:45.119431+00:00",
                    "routed": "2026-02-08T18:50:45.119431+00:00",
                    "acknowledged": "2026-02-08T18:53:21.683939+00:00",
                    "resolved": "2026-02-08T18:54:11.584849+00:00",
                    "closed": "2026-02-08T18:54:15.682285+00:00"
                },
                "resolution_note": "ISP-V003 systemic fix: missing fields added during ISP Manager v1.0.1 audit cycle",
                "decided_by": "Human Dragon"
            }
        ],
        "systemic_fixes": [
            {
                "fix_id": "FIX-20260208-001",
                "description": "ISP-V003 systemic fix: missing fields added during ISP Manager v1.0.1 audit cycle",
                "agent_affected": "isp-manager",
                "type": "processo",
                "human_decision_ref": "Human Dragon"
            }
        ],
        "authority": "Human Dragon — Chief Governance Officer, WINDI Publishing House",
        "scope": "Inaugural Governance Cycle — First Production Audit"
    }

    sample_path = os.path.join(output_dir, "sample_cycle_data.json")
    with open(sample_path, 'w', encoding='utf-8') as f:
        json.dump(sample_data, f, indent=2, ensure_ascii=False)

    return sample_path


def main():
    """Main entry point for CLI usage."""
    parser = argparse.ArgumentParser(
        description="WINDI Cycle Report Generator v1.0 — Three Dragons Protocol",
        epilog="AI processes. Human decides. WINDI guarantees."
    )
    parser.add_argument(
        "--cycle-dir",
        type=str,
        default="/opt/windi/agents/maestro/",
        help="Directory containing Maestro case files or state"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="/opt/windi/reports/",
        help="Output directory for generated reports"
    )
    parser.add_argument(
        "--format",
        type=str,
        default="all",
        choices=["json", "html", "pdf", "all"],
        help="Output format(s) to generate"
    )
    parser.add_argument(
        "--authority",
        type=str,
        default="Human Dragon — Chief Governance Officer",
        help="Authority name for sovereign decision"
    )
    parser.add_argument(
        "--scope",
        type=str,
        default="Governance Cycle Audit",
        help="Scope description"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without generating files"
    )
    parser.add_argument(
        "--create-sample",
        action="store_true",
        help="Create sample data for testing"
    )

    args = parser.parse_args()

    # Create sample data if requested
    if args.create_sample:
        sample_path = create_sample_data(args.output_dir)
        print(f"Sample data created: {sample_path}")
        return 0

    # Initialize generator
    generator = CycleReportGenerator()

    # Determine formats
    formats = [args.format] if args.format != 'all' else ['json', 'html', 'pdf']

    if args.dry_run:
        print(f"[DRY RUN] Would generate report:")
        print(f"  Cycle directory: {args.cycle_dir}")
        print(f"  Output directory: {args.output_dir}")
        print(f"  Formats: {', '.join(formats)}")
        print(f"  Authority: {args.authority}")
        print(f"  Scope: {args.scope}")

        # Still scan to show what would be included
        cycle_data = scan_maestro_cases(args.cycle_dir)
        print(f"  Findings found: {len(cycle_data.get('findings', []))}")
        return 0

    # Generate reports
    print(f"Generating governance cycle report...")
    print(f"  Source: {args.cycle_dir}")
    print(f"  Output: {args.output_dir}")

    try:
        outputs = generator.generate_full_report(
            cycle_dir=args.cycle_dir,
            output_dir=args.output_dir,
            formats=formats,
            authority=args.authority,
            scope=args.scope
        )

        print("\nGenerated files:")
        for fmt, path in outputs.items():
            if 'error' in fmt:
                print(f"  {fmt}: {path}")
            else:
                print(f"  {fmt.upper()}: {path}")

        # Show summary
        if 'json' in outputs:
            with open(outputs['json'], 'r') as f:
                report = json.load(f)
            summary = generator.report_generator.export_summary(report)
            print(summary)

    except Exception as e:
        print(f"Error generating report: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
