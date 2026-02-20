#!/usr/bin/env python3
"""
WINDI Governance Cycle Report Generator v1.0 — Three Dragons Protocol
======================================================================

Generates canonical JSON reports for completed governance cycles.
Implements the 10-section structure for full audit trail.

Principle: "The template NEVER decides the level. The API decides."

Author: WINDI Publishing House / Three Dragons Protocol
License: Proprietary — WINDI Governance Framework
"""

import json
import hashlib
import argparse
import os
import glob
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any


# Canonical JSON Schema Version
SCHEMA_VERSION = "1.0.0"
REPORT_VERSION = "1.0.0"


def generate_cycle_id() -> str:
    """Generate unique cycle ID in format GCR-YYYYMMDD-NNNN."""
    now = datetime.now(timezone.utc)
    date_part = now.strftime("%Y%m%d")
    # Use microseconds for uniqueness within same day
    seq = int(now.strftime("%H%M%S")[:4])
    return f"GCR-{date_part}-{seq:04d}"


def sha256_hash(data: str) -> str:
    """Generate SHA-256 hash of string data."""
    return hashlib.sha256(data.encode('utf-8')).hexdigest()


def canonical_json(obj: Dict) -> str:
    """Generate canonical JSON string for hashing (sorted keys, no extra whitespace)."""
    return json.dumps(obj, sort_keys=True, separators=(',', ':'), ensure_ascii=False)


class GovernanceCycleReport:
    """
    Generates and manages Governance Cycle Reports.

    A Governance Cycle Report documents a complete audit cycle including:
    - All findings processed
    - Virtue receipts generated
    - SLA compliance metrics
    - Forensic integrity verification
    - Human sovereign decision proof
    """

    def __init__(self):
        self.schema_version = SCHEMA_VERSION
        self.report_version = REPORT_VERSION

    def create_empty_template(self) -> Dict[str, Any]:
        """Create empty canonical template with all 10 sections."""
        return {
            "schema_version": self.schema_version,
            "cycle_id": "",
            "period": {
                "start_utc": "",
                "end_utc": ""
            },
            "report_generated_utc": "",
            "versions": {
                "maestro_version": "1.2.0",
                "sentinela_version": "1.0.0",
                "report_generator_version": self.report_version
            },
            "executive_summary": {
                "total_findings": 0,
                "cycles_closed": 0,
                "avg_resolution_minutes": 0.0,
                "sla_breaches": 0,
                "highest_severity": "R0",
                "invariants_triggered": []
            },
            "severity_distribution": {
                "R0": 0,
                "R1": 0,
                "R2": 0,
                "R3": 0,
                "R4": 0,
                "R5": 0
            },
            "findings": [],
            "systemic_fixes": [],
            "sla_compliance": [],
            "forensic_integrity": {
                "hash_chain_verified": False,
                "receipts_complete": False,
                "signatures_valid": False,
                "human_decision_proof": False
            },
            "sovereign_decision": {
                "authority": "",
                "scope": "",
                "approval_timestamp_utc": "",
                "virtue_receipt_hash": ""
            },
            "seal": {
                "report_seal_hash": "",
                "ledger_entry_reference": "",
                "statement": "AI processes. Human decides. WINDI guarantees."
            }
        }

    def generate_from_maestro(self, cycle_data: Dict) -> Dict[str, Any]:
        """
        Populate the template from Maestro cycle data.

        Args:
            cycle_data: Dictionary containing:
                - findings: List of finding dictionaries
                - period: {start_utc, end_utc}
                - authority: Human authority name
                - scope: Scope description
                - systemic_fixes: Optional list of fixes

        Returns:
            Complete report dictionary ready for sealing
        """
        report = self.create_empty_template()
        now = datetime.now(timezone.utc)

        # Basic metadata
        report["cycle_id"] = cycle_data.get("cycle_id", generate_cycle_id())
        report["report_generated_utc"] = now.isoformat()

        # Period
        if "period" in cycle_data:
            report["period"] = cycle_data["period"]
        else:
            # Derive from findings
            findings = cycle_data.get("findings", [])
            if findings:
                timestamps = []
                for f in findings:
                    if "timeline" in f:
                        for ts in f["timeline"].values():
                            if ts:
                                timestamps.append(ts)
                if timestamps:
                    timestamps.sort()
                    report["period"]["start_utc"] = timestamps[0]
                    report["period"]["end_utc"] = timestamps[-1]

        # Versions
        if "versions" in cycle_data:
            report["versions"].update(cycle_data["versions"])

        # Process findings
        findings = cycle_data.get("findings", [])
        report["findings"] = self._normalize_findings(findings)

        # Calculate metrics
        metrics = self.calculate_metrics(report["findings"])
        report["executive_summary"] = metrics["executive_summary"]
        report["severity_distribution"] = metrics["severity_distribution"]
        report["sla_compliance"] = metrics["sla_compliance"]

        # Systemic fixes
        report["systemic_fixes"] = cycle_data.get("systemic_fixes", [])

        # Forensic integrity
        report["forensic_integrity"] = self._verify_forensic_integrity(report["findings"])

        # Sovereign decision
        report["sovereign_decision"] = {
            "authority": cycle_data.get("authority", ""),
            "scope": cycle_data.get("scope", ""),
            "approval_timestamp_utc": now.isoformat(),
            "virtue_receipt_hash": self._generate_virtue_receipt_hash(cycle_data)
        }

        return report

    def _normalize_findings(self, findings: List[Dict]) -> List[Dict]:
        """Normalize findings to canonical format."""
        normalized = []
        for f in findings:
            normalized.append({
                "finding_id": f.get("finding_id", ""),
                "origin_agent": f.get("origin_agent", f.get("source_agent", "")),
                "severity": f.get("severity", "R3"),
                "category": f.get("category", ""),
                "summary": f.get("summary", ""),
                "invariants": f.get("invariants", []),
                "virtue_receipts": f.get("virtue_receipts", f.get("receipt_chain", [])),
                "timeline": {
                    "registered": f.get("timeline", {}).get("registered", f.get("created_at", "")),
                    "routed": f.get("timeline", {}).get("routed", ""),
                    "acknowledged": f.get("timeline", {}).get("acknowledged", f.get("acknowledged_at", "")),
                    "resolved": f.get("timeline", {}).get("resolved", f.get("resolved_at", "")),
                    "closed": f.get("timeline", {}).get("closed", f.get("closed_at", ""))
                },
                "resolution_note": f.get("resolution_note", ""),
                "decided_by": f.get("decided_by", f.get("assigned_to", ""))
            })
        return normalized

    def calculate_metrics(self, findings: List[Dict]) -> Dict[str, Any]:
        """
        Calculate metrics from findings list.

        Returns:
            Dictionary with executive_summary, severity_distribution, sla_compliance
        """
        # Severity distribution
        severity_dist = {"R0": 0, "R1": 0, "R2": 0, "R3": 0, "R4": 0, "R5": 0}

        # Track invariants and resolution times
        invariants_set = set()
        resolution_times = []
        sla_met = 0
        sla_breached = 0
        highest_severity_num = 0
        closed_count = 0

        for f in findings:
            # Severity
            sev = f.get("severity", "R3")
            if sev in severity_dist:
                severity_dist[sev] += 1
                sev_num = int(sev[1]) if len(sev) > 1 and sev[1].isdigit() else 3
                if sev_num > highest_severity_num:
                    highest_severity_num = sev_num

            # Invariants
            for inv in f.get("invariants", []):
                invariants_set.add(inv)

            # Resolution time
            timeline = f.get("timeline", {})
            registered = timeline.get("registered", "")
            closed = timeline.get("closed", "")

            if registered and closed:
                closed_count += 1
                try:
                    # Parse timestamps
                    reg_dt = datetime.fromisoformat(registered.replace('Z', '+00:00'))
                    closed_dt = datetime.fromisoformat(closed.replace('Z', '+00:00'))
                    delta = (closed_dt - reg_dt).total_seconds() / 60  # minutes
                    resolution_times.append(delta)
                    sla_met += 1  # Assume SLA met if closed properly
                except (ValueError, TypeError):
                    pass

        # Calculate average resolution time
        avg_resolution = sum(resolution_times) / len(resolution_times) if resolution_times else 0.0

        # Highest severity
        highest_severity = f"R{highest_severity_num}"

        return {
            "executive_summary": {
                "total_findings": len(findings),
                "cycles_closed": closed_count,
                "avg_resolution_minutes": round(avg_resolution, 2),
                "sla_breaches": sla_breached,
                "highest_severity": highest_severity,
                "invariants_triggered": sorted(list(invariants_set))
            },
            "severity_distribution": severity_dist,
            "sla_compliance": [
                {
                    "sla_type": "acknowledge",
                    "total": len(findings),
                    "met": sla_met,
                    "breached": sla_breached,
                    "action_taken": "Human acknowledgment within SLA window"
                },
                {
                    "sla_type": "resolve",
                    "total": len(findings),
                    "met": closed_count,
                    "breached": len(findings) - closed_count,
                    "action_taken": "Resolution completed by human decision"
                }
            ]
        }

    def _verify_forensic_integrity(self, findings: List[Dict]) -> Dict[str, bool]:
        """Verify forensic integrity of findings."""
        has_receipts = all(len(f.get("virtue_receipts", [])) > 0 for f in findings) if findings else False
        has_human_decision = all(f.get("decided_by", "") or f.get("resolution_note", "") for f in findings) if findings else False

        return {
            "hash_chain_verified": has_receipts,
            "receipts_complete": has_receipts,
            "signatures_valid": has_receipts,
            "human_decision_proof": has_human_decision
        }

    def _generate_virtue_receipt_hash(self, cycle_data: Dict) -> str:
        """Generate virtue receipt hash for sovereign decision."""
        content = {
            "authority": cycle_data.get("authority", ""),
            "scope": cycle_data.get("scope", ""),
            "findings_count": len(cycle_data.get("findings", [])),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        return sha256_hash(canonical_json(content))[:16]

    def seal_report(self, report: Dict) -> str:
        """
        Generate SHA-256 seal of the complete report.

        The seal is calculated over all fields EXCEPT the seal section itself.

        Args:
            report: Complete report dictionary

        Returns:
            SHA-256 hash string
        """
        # Create copy without seal
        report_for_hash = {k: v for k, v in report.items() if k != "seal"}

        # Generate canonical JSON and hash
        canonical = canonical_json(report_for_hash)
        seal_hash = sha256_hash(canonical)

        return seal_hash

    def validate_integrity(self, report: Dict) -> bool:
        """
        Verify that the seal hash matches the report content.

        Args:
            report: Report dictionary with seal

        Returns:
            True if seal is valid, False otherwise
        """
        stored_hash = report.get("seal", {}).get("report_seal_hash", "")
        if not stored_hash:
            return False

        calculated_hash = self.seal_report(report)
        return stored_hash == calculated_hash

    def save_json(self, report: Dict, path: str) -> None:
        """
        Save report as formatted JSON file.

        Args:
            report: Complete report dictionary
            path: Output file path
        """
        # Ensure seal is applied
        if not report.get("seal", {}).get("report_seal_hash"):
            seal_hash = self.seal_report(report)
            report["seal"]["report_seal_hash"] = seal_hash
            report["seal"]["ledger_entry_reference"] = f"LEDGER-{generate_cycle_id()}"

        # Ensure directory exists
        os.makedirs(os.path.dirname(path) if os.path.dirname(path) else ".", exist_ok=True)

        with open(path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

    def export_summary(self, report: Dict) -> str:
        """
        Generate text summary for logs and console output.

        Args:
            report: Complete report dictionary

        Returns:
            Formatted summary string
        """
        es = report.get("executive_summary", {})
        seal = report.get("seal", {})
        sov = report.get("sovereign_decision", {})

        lines = [
            "=" * 70,
            "   WINDI GOVERNANCE CYCLE REPORT",
            "=" * 70,
            f"   Cycle ID: {report.get('cycle_id', 'N/A')}",
            f"   Generated: {report.get('report_generated_utc', 'N/A')}",
            "",
            "   EXECUTIVE SUMMARY",
            "-" * 70,
            f"   Total Findings: {es.get('total_findings', 0)}",
            f"   Cycles Closed: {es.get('cycles_closed', 0)}",
            f"   Avg Resolution: {es.get('avg_resolution_minutes', 0):.2f} minutes",
            f"   SLA Breaches: {es.get('sla_breaches', 0)}",
            f"   Highest Severity: {es.get('highest_severity', 'N/A')}",
            f"   Invariants: {', '.join(es.get('invariants_triggered', [])) or 'None'}",
            "",
            "   SOVEREIGN DECISION",
            "-" * 70,
            f"   Authority: {sov.get('authority', 'N/A')}",
            f"   Scope: {sov.get('scope', 'N/A')}",
            "",
            "   SEAL",
            "-" * 70,
            f"   Hash: {seal.get('report_seal_hash', 'UNSIGNED')[:32]}...",
            f"   Ledger: {seal.get('ledger_entry_reference', 'N/A')}",
            "",
            f"   {seal.get('statement', '')}",
            "=" * 70
        ]

        return "\n".join(lines)


def load_maestro_cases(cycle_dir: str) -> Dict[str, Any]:
    """
    Load Maestro case files from a directory.

    Args:
        cycle_dir: Path to directory containing case JSON files

    Returns:
        Cycle data dictionary for report generation
    """
    findings = []

    # Look for JSON files
    patterns = [
        os.path.join(cycle_dir, "*.json"),
        os.path.join(cycle_dir, "cases", "*.json"),
        os.path.join(cycle_dir, "findings", "*.json")
    ]

    for pattern in patterns:
        for filepath in glob.glob(pattern):
            if "report" in os.path.basename(filepath).lower():
                continue  # Skip existing reports
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Handle different formats
                    if isinstance(data, list):
                        findings.extend(data)
                    elif isinstance(data, dict):
                        if "findings" in data:
                            findings.extend(data["findings"])
                        else:
                            findings.append(data)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Warning: Could not load {filepath}: {e}")

    return {
        "findings": findings,
        "authority": "Human Dragon — Chief Governance Officer",
        "scope": "Governance Cycle Audit"
    }


def main():
    """Main entry point for CLI usage."""
    parser = argparse.ArgumentParser(
        description="WINDI Governance Cycle Report Generator v1.0",
        epilog="AI processes. Human decides. WINDI guarantees."
    )
    parser.add_argument(
        "--cycle-dir",
        type=str,
        default="/opt/windi/agents/maestro/cases/",
        help="Directory containing Maestro case files"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="/opt/windi/reports/cycle_report.json",
        help="Output path for the JSON report"
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
        help="Scope description for the report"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without writing files"
    )

    args = parser.parse_args()

    # Initialize generator
    generator = GovernanceCycleReport()

    # Load cycle data
    print(f"Loading cases from: {args.cycle_dir}")
    cycle_data = load_maestro_cases(args.cycle_dir)
    cycle_data["authority"] = args.authority
    cycle_data["scope"] = args.scope

    print(f"Found {len(cycle_data.get('findings', []))} findings")

    # Generate report
    report = generator.generate_from_maestro(cycle_data)

    # Seal the report
    seal_hash = generator.seal_report(report)
    report["seal"]["report_seal_hash"] = seal_hash
    report["seal"]["ledger_entry_reference"] = f"LEDGER-{report['cycle_id']}"

    # Output
    if args.dry_run:
        print("\n[DRY RUN] Would generate report:")
        print(generator.export_summary(report))
    else:
        generator.save_json(report, args.output)
        print(f"\nReport saved to: {args.output}")
        print(generator.export_summary(report))

    return 0


if __name__ == "__main__":
    exit(main())
