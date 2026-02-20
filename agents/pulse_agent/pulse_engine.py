#!/usr/bin/env python3
"""
WINDI Pulse Agent v1.0.0 — Three Dragons Protocol
==================================================

Predictive pattern analysis for institutional arrhythmia detection.
Advisory-only. Human-mediated. Zero-knowledge compliant.

"O Pulse ouve o batimento cardíaco do WINDI."

Author: WINDI Publishing House / Three Dragons Protocol
License: Proprietary — WINDI Governance Framework
"""

import json
import hashlib
import argparse
import os
import glob
import sqlite3
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
from collections import defaultdict


class PulseAgent:
    """
    WINDI Pulse Agent v1.0.0

    Predictive pattern analysis for institutional arrhythmia detection.
    Advisory-only. Human-mediated. Zero-knowledge compliant.

    Detection modes:
    1. Rhythm - Resolution time patterns by severity
    2. Frequency - Finding volume patterns
    3. Escalation - Severity trend detection
    4. Recurrence - Repeated finding detection
    5. Saturation - Queue capacity analysis
    """

    def __init__(self, config_path: str = '/opt/windi/agents/pulse_agent/manifest.json'):
        """
        Initialize the Pulse Agent.

        Args:
            config_path: Path to manifest.json
        """
        self.config_path = config_path
        self.base_path = os.path.dirname(config_path)

        # Load configuration
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                self.manifest = json.load(f)
        else:
            self.manifest = {"agent_id": "pulse-agent", "version": "1.0.0"}

        # Define paths
        self.reports_path = '/opt/windi/reports/'
        self.maestro_db = '/opt/windi/agents/maestro/state/maestro_state.db'
        self.baselines_path = os.path.join(self.base_path, 'baselines')
        self.patterns_path = os.path.join(self.base_path, 'patterns')
        self.alerts_path = os.path.join(self.base_path, 'alerts', 'pending')
        self.logs_path = os.path.join(self.base_path, 'logs')

        # Ensure directories exist
        for path in [self.baselines_path, self.patterns_path, self.alerts_path, self.logs_path]:
            os.makedirs(path, exist_ok=True)

        # Load current baseline if exists
        self.baseline = self._load_latest_baseline()

    def _load_latest_baseline(self) -> Optional[Dict]:
        """Load the most recent baseline file."""
        baselines = sorted(glob.glob(os.path.join(self.baselines_path, "BASELINE-*.json")), reverse=True)
        if baselines:
            try:
                with open(baselines[0], 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        return None

    def _load_governance_data(self, window_days: int) -> List[Dict]:
        """Load governance cycle data from Maestro database."""
        data = []

        if os.path.exists(self.maestro_db):
            try:
                conn = sqlite3.connect(self.maestro_db)
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                # Calculate cutoff date
                cutoff = (datetime.now(timezone.utc) - timedelta(days=window_days)).isoformat()

                cursor.execute("""
                    SELECT * FROM governance_cycles
                    WHERE created_at >= ?
                    ORDER BY created_at DESC
                """, (cutoff,))

                for row in cursor.fetchall():
                    data.append(dict(row))

                conn.close()
            except Exception as e:
                print(f"Warning: Could not load Maestro data: {e}")

        return data

    def analyze(self, window_days: int = 30) -> Dict[str, Any]:
        """
        Execute complete pattern analysis.

        Args:
            window_days: Number of days to analyze

        Returns:
            pulse_analysis dictionary
        """
        now = datetime.now(timezone.utc)
        analysis_id = f"PLS-{now.strftime('%Y%m%d-%H%M%S')}"

        analysis = {
            "analysis_id": analysis_id,
            "timestamp_utc": now.isoformat(),
            "window_days": window_days,
            "data_points_analyzed": 0,
            "patterns_detected": [],
            "rhythm_status": "NORMAL",
            "alerts": [],
            "confidence": "LOW",
            "recommendations": [],
            "analysis_hash": ""
        }

        # Load data
        governance_data = self._load_governance_data(window_days)
        analysis["data_points_analyzed"] = len(governance_data)

        if len(governance_data) < 3:
            analysis["rhythm_status"] = "INSUFFICIENT_DATA"
            analysis["recommendations"].append({
                "type": "data_collection",
                "suggestion": "Insufficient data for pattern analysis (< 3 data points)",
                "urgency": "LOW",
                "confidence": "N/A"
            })
            self._compute_confidence(analysis)
            self._generate_hash(analysis)
            return analysis

        # Run all analysis modes
        self._analyze_rhythm(analysis, governance_data)
        self._analyze_frequency(analysis, governance_data)
        self._analyze_escalation(analysis, governance_data)
        self._analyze_recurrence(analysis, governance_data)
        self._analyze_saturation(analysis, governance_data)

        # Compute overall confidence and recommendations
        self._compute_confidence(analysis)
        self._generate_recommendations(analysis)
        self._generate_hash(analysis)

        # Determine overall rhythm status
        self._determine_rhythm_status(analysis)

        # Generate alerts if needed
        for pattern in analysis["patterns_detected"]:
            if pattern.get("severity") in ["HIGH", "CRITICAL"]:
                self.alert_maestro(pattern)

        return analysis

    def _analyze_rhythm(self, analysis: Dict, data: List[Dict]) -> None:
        """
        RHYTHM: Average resolution time per severity level.
        Calculate moving average of resolution_time for each R-level.
        Deviation > 2x baseline → Pattern: RHYTHM_DEVIATION
        """
        resolution_times = defaultdict(list)

        for finding in data:
            severity = finding.get("severity", "R3")
            created = finding.get("created_at", "")
            closed = finding.get("closed_at", "")

            if created and closed:
                try:
                    start = datetime.fromisoformat(created.replace('Z', '+00:00'))
                    end = datetime.fromisoformat(closed.replace('Z', '+00:00'))
                    duration_minutes = (end - start).total_seconds() / 60
                    resolution_times[severity].append(duration_minutes)
                except (ValueError, TypeError):
                    pass

        # Calculate averages
        rhythm_metrics = {}
        for severity, times in resolution_times.items():
            if times:
                avg = sum(times) / len(times)
                rhythm_metrics[severity] = {
                    "avg_minutes": round(avg, 2),
                    "count": len(times),
                    "min": round(min(times), 2),
                    "max": round(max(times), 2)
                }

        # Compare to baseline if available
        if self.baseline and "rhythm" in self.baseline:
            for severity, metrics in rhythm_metrics.items():
                baseline_avg = self.baseline["rhythm"].get(severity, {}).get("avg_minutes", 0)
                if baseline_avg > 0:
                    ratio = metrics["avg_minutes"] / baseline_avg
                    if ratio > 2.0:
                        analysis["patterns_detected"].append({
                            "pattern_type": "RHYTHM_DEVIATION",
                            "severity": "HIGH",
                            "description": f"Resolution time for {severity} is {ratio:.1f}x baseline ({metrics['avg_minutes']:.1f}min vs {baseline_avg:.1f}min baseline)",
                            "affected": severity,
                            "metric": ratio,
                            "suggestion": "Possível fadiga de decisão ou complexidade aumentada"
                        })

        analysis["rhythm_metrics"] = rhythm_metrics

    def _analyze_frequency(self, analysis: Dict, data: List[Dict]) -> None:
        """
        FREQUENCY: Finding volume patterns.
        Compare findings/day vs historical average.
        Spike > 3x average → Pattern: FREQUENCY_SPIKE
        Drop > 50% → Pattern: FREQUENCY_DROP
        """
        # Group by day
        daily_counts = defaultdict(int)
        agent_counts = defaultdict(int)

        for finding in data:
            created = finding.get("created_at", "")
            agent = finding.get("source_agent", "unknown")

            if created:
                try:
                    dt = datetime.fromisoformat(created.replace('Z', '+00:00'))
                    day_key = dt.strftime("%Y-%m-%d")
                    daily_counts[day_key] += 1
                    agent_counts[agent] += 1
                except (ValueError, TypeError):
                    pass

        if daily_counts:
            counts = list(daily_counts.values())
            avg_daily = sum(counts) / len(counts)
            max_daily = max(counts)

            analysis["frequency_metrics"] = {
                "avg_daily": round(avg_daily, 2),
                "max_daily": max_daily,
                "total_days": len(daily_counts),
                "by_agent": dict(agent_counts)
            }

            # Check for spikes
            if max_daily > avg_daily * 3 and avg_daily > 0:
                analysis["patterns_detected"].append({
                    "pattern_type": "FREQUENCY_SPIKE",
                    "severity": "WARNING",
                    "description": f"Peak daily findings ({max_daily}) is {max_daily/avg_daily:.1f}x average ({avg_daily:.1f})",
                    "suggestion": "Considere investigar causa do pico"
                })

            # Check for agents with zero recent findings
            if self.baseline and "frequency" in self.baseline:
                for agent in self.baseline["frequency"].get("by_agent", {}).keys():
                    if agent not in agent_counts:
                        analysis["patterns_detected"].append({
                            "pattern_type": "FREQUENCY_DROP",
                            "severity": "WARNING",
                            "description": f"Agent '{agent}' had 0 findings in analysis window",
                            "affected": agent,
                            "suggestion": "Verificar se agente está ativo e funcionando"
                        })

    def _analyze_escalation(self, analysis: Dict, data: List[Dict]) -> None:
        """
        ESCALATION: Severity trend detection.
        Track if findings are trending toward higher severity.
        3 consecutive cycles with increasing severity → Pattern: ESCALATION_TREND
        """
        # Group by date and track severity
        severity_order = {"R0": 0, "R1": 1, "R2": 2, "R3": 3, "R4": 4, "R5": 5}
        daily_severity = defaultdict(list)

        for finding in data:
            created = finding.get("created_at", "")
            severity = finding.get("severity", "R3")

            if created:
                try:
                    dt = datetime.fromisoformat(created.replace('Z', '+00:00'))
                    day_key = dt.strftime("%Y-%m-%d")
                    daily_severity[day_key].append(severity_order.get(severity, 3))
                except (ValueError, TypeError):
                    pass

        if len(daily_severity) >= 3:
            # Calculate daily average severity
            daily_avgs = []
            for day in sorted(daily_severity.keys()):
                sevs = daily_severity[day]
                daily_avgs.append((day, sum(sevs) / len(sevs)))

            # Check for 3+ consecutive increases
            consecutive_increases = 0
            for i in range(1, len(daily_avgs)):
                if daily_avgs[i][1] > daily_avgs[i-1][1]:
                    consecutive_increases += 1
                    if consecutive_increases >= 2:
                        analysis["patterns_detected"].append({
                            "pattern_type": "ESCALATION_TREND",
                            "severity": "HIGH",
                            "description": f"Severity trending upward for {consecutive_increases + 1} consecutive periods",
                            "suggestion": "Tendência preocupante — considere revisão de processos"
                        })
                        break
                else:
                    consecutive_increases = 0

    def _analyze_recurrence(self, analysis: Dict, data: List[Dict]) -> None:
        """
        RECURRENCE: Repeated finding detection.
        Same type of finding in same ISP/agent > 2 times → Pattern: RECURRING_ISSUE
        """
        # Group by category/type
        category_counts = defaultdict(list)

        for finding in data:
            category = finding.get("category", "")
            agent = finding.get("source_agent", "unknown")

            if category:
                key = f"{agent}:{category}"
                category_counts[key].append(finding.get("finding_id", ""))

        # Find recurring issues
        for key, finding_ids in category_counts.items():
            if len(finding_ids) > 2:
                agent, category = key.split(":", 1) if ":" in key else (key, "unknown")
                analysis["patterns_detected"].append({
                    "pattern_type": "RECURRING_ISSUE",
                    "severity": "WARNING",
                    "description": f"Category '{category}' from '{agent}' recurred {len(finding_ids)} times",
                    "affected": key,
                    "count": len(finding_ids),
                    "suggestion": "Problema sistêmico possível — fix anterior pode ser insuficiente"
                })

    def _analyze_saturation(self, analysis: Dict, data: List[Dict]) -> None:
        """
        SATURATION: Queue capacity analysis.
        Calculate: pending_findings / avg_resolution_rate.
        If estimated time > SLA threshold → Pattern: QUEUE_SATURATION
        """
        # Count pending findings by severity
        pending = defaultdict(int)
        resolved = []

        for finding in data:
            status = finding.get("status", "")
            severity = finding.get("severity", "R3")

            if status in ["OPEN", "ACKNOWLEDGED", "ROUTED"]:
                pending[severity] += 1
            elif status == "CLOSED":
                created = finding.get("created_at", "")
                closed = finding.get("closed_at", "")
                if created and closed:
                    try:
                        start = datetime.fromisoformat(created.replace('Z', '+00:00'))
                        end = datetime.fromisoformat(closed.replace('Z', '+00:00'))
                        resolved.append((end - start).total_seconds() / 60)
                    except (ValueError, TypeError):
                        pass

        # Calculate average resolution rate
        avg_resolution_minutes = sum(resolved) / len(resolved) if resolved else 10

        # Check saturation
        total_pending = sum(pending.values())
        if total_pending > 0:
            estimated_clear_time = total_pending * avg_resolution_minutes

            analysis["saturation_metrics"] = {
                "pending_total": total_pending,
                "pending_by_severity": dict(pending),
                "avg_resolution_minutes": round(avg_resolution_minutes, 2),
                "estimated_clear_minutes": round(estimated_clear_time, 2)
            }

            # SLA warning thresholds (simplified)
            sla_thresholds = {"R4": 30, "R3": 120, "R2": 480}

            for sev, sla_min in sla_thresholds.items():
                if sev in pending and pending[sev] > 0:
                    est_time = pending[sev] * avg_resolution_minutes
                    if est_time > sla_min * 0.9:  # 90% of SLA
                        analysis["patterns_detected"].append({
                            "pattern_type": "QUEUE_SATURATION",
                            "severity": "HIGH",
                            "description": f"{pending[sev]} pending {sev} findings, estimated {est_time:.0f}min to clear (SLA: {sla_min}min)",
                            "affected": sev,
                            "suggestion": "Margem crítica — considere priorização"
                        })

    def _compute_confidence(self, analysis: Dict) -> None:
        """
        Calculate overall analysis confidence.
        LOW: < 10 data points or < 7 days
        MEDIUM: 10-50 data points and 7-30 days
        HIGH: > 50 data points and > 30 days
        """
        data_points = analysis.get("data_points_analyzed", 0)
        window_days = analysis.get("window_days", 0)

        if data_points < 10 or window_days < 7:
            analysis["confidence"] = "LOW"
        elif data_points <= 50 or window_days <= 30:
            analysis["confidence"] = "MEDIUM"
        else:
            analysis["confidence"] = "HIGH"

    def _generate_recommendations(self, analysis: Dict) -> None:
        """
        Generate recommendations based on detected patterns.
        Uses advisory language only — never imperative.
        """
        patterns = analysis.get("patterns_detected", [])

        for pattern in patterns:
            ptype = pattern.get("pattern_type", "")
            suggestion = pattern.get("suggestion", "")

            if ptype == "RHYTHM_DEVIATION":
                analysis["recommendations"].append({
                    "type": "rhythm",
                    "pattern": ptype,
                    "suggestion": f"Considere revisar carga de trabalho da equipe. {suggestion}",
                    "urgency": "MEDIUM",
                    "confidence": analysis["confidence"]
                })
            elif ptype == "ESCALATION_TREND":
                analysis["recommendations"].append({
                    "type": "escalation",
                    "pattern": ptype,
                    "suggestion": f"Padrão indica possível degradação. {suggestion}",
                    "urgency": "HIGH",
                    "confidence": analysis["confidence"]
                })
            elif ptype == "RECURRING_ISSUE":
                analysis["recommendations"].append({
                    "type": "recurrence",
                    "pattern": ptype,
                    "suggestion": f"Sugerimos investigar causa raiz. {suggestion}",
                    "urgency": "MEDIUM",
                    "confidence": analysis["confidence"]
                })
            elif ptype == "QUEUE_SATURATION":
                analysis["recommendations"].append({
                    "type": "saturation",
                    "pattern": ptype,
                    "suggestion": f"Fila aproximando capacidade. {suggestion}",
                    "urgency": "HIGH",
                    "confidence": analysis["confidence"]
                })

    def _determine_rhythm_status(self, analysis: Dict) -> None:
        """Determine overall rhythm status from patterns."""
        patterns = analysis.get("patterns_detected", [])

        critical_count = sum(1 for p in patterns if p.get("severity") == "CRITICAL")
        high_count = sum(1 for p in patterns if p.get("severity") == "HIGH")

        if critical_count > 0 or high_count >= 3:
            analysis["rhythm_status"] = "ARRHYTHMIC"
        elif high_count > 0 or len(patterns) >= 2:
            analysis["rhythm_status"] = "IRREGULAR"
        else:
            analysis["rhythm_status"] = "NORMAL"

    def _generate_hash(self, analysis: Dict) -> None:
        """Generate analysis hash for integrity."""
        analysis_copy = {k: v for k, v in analysis.items() if k != "analysis_hash"}
        content = json.dumps(analysis_copy, sort_keys=True, ensure_ascii=False)
        analysis["analysis_hash"] = hashlib.sha256(content.encode('utf-8')).hexdigest()

    def establish_baseline(self, window_days: int = 30) -> Dict:
        """
        Calculate and save baseline metrics for future comparison.

        Args:
            window_days: Window for baseline calculation

        Returns:
            Baseline dictionary
        """
        now = datetime.now(timezone.utc)
        data = self._load_governance_data(window_days)

        baseline = {
            "baseline_id": f"BASELINE-{now.strftime('%Y%m%d')}",
            "created_utc": now.isoformat(),
            "window_days": window_days,
            "data_points": len(data),
            "rhythm": {},
            "frequency": {
                "by_agent": defaultdict(int)
            }
        }

        # Calculate rhythm baseline
        resolution_times = defaultdict(list)
        for finding in data:
            severity = finding.get("severity", "R3")
            created = finding.get("created_at", "")
            closed = finding.get("closed_at", "")
            agent = finding.get("source_agent", "unknown")

            baseline["frequency"]["by_agent"][agent] = baseline["frequency"]["by_agent"].get(agent, 0) + 1

            if created and closed:
                try:
                    start = datetime.fromisoformat(created.replace('Z', '+00:00'))
                    end = datetime.fromisoformat(closed.replace('Z', '+00:00'))
                    duration = (end - start).total_seconds() / 60
                    resolution_times[severity].append(duration)
                except (ValueError, TypeError):
                    pass

        for severity, times in resolution_times.items():
            if times:
                baseline["rhythm"][severity] = {
                    "avg_minutes": round(sum(times) / len(times), 2),
                    "count": len(times)
                }

        baseline["frequency"]["by_agent"] = dict(baseline["frequency"]["by_agent"])

        # Save baseline
        baseline_path = os.path.join(self.baselines_path, f"{baseline['baseline_id']}.json")
        with open(baseline_path, 'w', encoding='utf-8') as f:
            json.dump(baseline, f, indent=2, ensure_ascii=False)

        self.baseline = baseline
        return baseline

    def save_analysis(self, analysis: Dict, path: str = None) -> str:
        """Save analysis to file."""
        if path is None:
            path = os.path.join(self.patterns_path, f"{analysis['analysis_id']}.json")

        with open(path, 'w', encoding='utf-8') as f:
            json.dump(analysis, f, indent=2, ensure_ascii=False)

        return path

    def alert_maestro(self, pattern: Dict) -> None:
        """Send predictive alert to Maestro."""
        alert = {
            "agent": "pulse-agent",
            "alert_type": "PREDICTION",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "pattern": pattern.get("pattern_type", ""),
            "severity": pattern.get("severity", "WARNING"),
            "description": pattern.get("description", ""),
            "suggestion": pattern.get("suggestion", ""),
            "action_required": "HUMAN_REVIEW_RECOMMENDED"
        }

        alert_file = os.path.join(
            self.alerts_path,
            f"pulse_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{pattern.get('pattern_type', 'unknown')}.json"
        )

        with open(alert_file, 'w', encoding='utf-8') as f:
            json.dump(alert, f, indent=2, ensure_ascii=False)

    def get_history(self, last_n: int = 10) -> List[Dict]:
        """Return last N analyses."""
        analyses = sorted(
            glob.glob(os.path.join(self.patterns_path, "PLS-*.json")),
            reverse=True
        )[:last_n]

        results = []
        for f in analyses:
            try:
                with open(f, 'r', encoding='utf-8') as rf:
                    results.append(json.load(rf))
            except (json.JSONDecodeError, IOError):
                pass

        return results


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="WINDI Pulse Agent v1.0.0 — Three Dragons Protocol",
        epilog="O Pulse ouve o batimento cardíaco do WINDI."
    )
    parser.add_argument("--analyze", action="store_true", help="Execute full pattern analysis")
    parser.add_argument("--window", type=int, default=30, help="Analysis window in days")
    parser.add_argument("--baseline", action="store_true", help="Establish new baseline")
    parser.add_argument("--compare", action="store_true", help="Compare current vs baseline")
    parser.add_argument("--history", type=int, metavar="N", help="Show last N analyses")
    parser.add_argument("--json", action="store_true", help="Output in JSON format")

    args = parser.parse_args()

    pulse = PulseAgent()

    if args.baseline:
        baseline = pulse.establish_baseline(args.window)
        if args.json:
            print(json.dumps(baseline, indent=2, ensure_ascii=False))
        else:
            print(f"Baseline established: {baseline['baseline_id']}")
            print(f"Data points: {baseline['data_points']}")
            print(f"Window: {baseline['window_days']} days")

    elif args.analyze:
        analysis = pulse.analyze(args.window)
        path = pulse.save_analysis(analysis)

        if args.json:
            print(json.dumps(analysis, indent=2, ensure_ascii=False))
        else:
            print("=" * 70)
            print("   WINDI PULSE AGENT — Pattern Analysis")
            print("=" * 70)
            print(f"   Analysis ID: {analysis['analysis_id']}")
            print(f"   Data Points: {analysis['data_points_analyzed']}")
            print(f"   Rhythm Status: {analysis['rhythm_status']}")
            print(f"   Confidence: {analysis['confidence']}")
            print()
            if analysis["patterns_detected"]:
                print("   PATTERNS DETECTED:")
                for p in analysis["patterns_detected"]:
                    print(f"     [{p['severity']}] {p['pattern_type']}: {p['description']}")
            else:
                print("   No concerning patterns detected.")
            print()
            if analysis["recommendations"]:
                print("   RECOMMENDATIONS:")
                for r in analysis["recommendations"]:
                    print(f"     • [{r['urgency']}] {r['suggestion']}")
            print()
            print(f"   Analysis saved: {path}")
            print("=" * 70)

    elif args.history:
        history = pulse.get_history(args.history)
        if args.json:
            print(json.dumps(history, indent=2, ensure_ascii=False))
        else:
            print(f"Last {len(history)} analyses:")
            for a in history:
                print(f"  {a['analysis_id']} | {a['rhythm_status']} | Patterns: {len(a.get('patterns_detected', []))}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
