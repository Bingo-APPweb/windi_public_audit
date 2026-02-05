"""
WINDI Audit Dashboard v1.0
Query interface for the submission registry. CLI + API.
AI processes. Human decides. WINDI guarantees.
"""
import json, sys
from datetime import datetime, timezone
from submission_registry import SubmissionRegistry

class AuditDashboard:
    def __init__(self, submissions_dir):
        self.registry = SubmissionRegistry(submissions_dir)

    def overview(self):
        stats = self.registry.get_stats()
        recent = self.registry.query(limit=5)
        ok, chain = self.registry.verify_chain()
        return {
            "dashboard": "WINDI Audit Dashboard v1.0",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "statistics": stats,
            "chain_integrity": chain,
            "recent": [
                {"id": e["submission_id"], "entity": e.get("reporting_entity",""),
                 "level": e["governance_level"], "at": e["registered_at"]}
                for e in recent
            ],
        }

    def lookup(self, sid):
        e = self.registry.lookup(sid)
        return {"found": True, "entry": e} if e else {"error": f"'{sid}' not found"}

    def search(self, level=None, entity=None, limit=20):
        r = self.registry.query(level=level, entity=entity, limit=limit)
        return {"count": len(r), "results": r}

    def entity_report(self, name):
        entries = self.registry.query(entity=name, limit=100)
        levels = {}; periods = set()
        for e in entries:
            lv = e.get("governance_level","")
            levels[lv] = levels.get(lv,0)+1
            if e.get("reference_period"): periods.add(e["reference_period"])
        return {
            "entity": name, "total": len(entries),
            "levels": levels, "periods": sorted(periods),
            "first": entries[-1]["registered_at"] if entries else None,
            "latest": entries[0]["registered_at"] if entries else None,
        }

    def integrity_check(self):
        ok, report = self.registry.verify_chain()
        return {"status": "INTACT" if ok else "ATTENTION", "report": report}

def main():
    d = AuditDashboard("/opt/windi/engine/submissions")
    if len(sys.argv) < 2:
        print(json.dumps(d.overview(), indent=2, default=str)); return
    cmd = sys.argv[1]
    if cmd == "lookup" and len(sys.argv)>2:
        print(json.dumps(d.lookup(sys.argv[2]), indent=2, default=str))
    elif cmd == "search":
        kw = {}; args = sys.argv[2:]; i=0
        while i<len(args):
            if args[i]=="--level" and i+1<len(args): kw["level"]=args[i+1]; i+=2
            elif args[i]=="--entity" and i+1<len(args): kw["entity"]=args[i+1]; i+=2
            else: i+=1
        print(json.dumps(d.search(**kw), indent=2, default=str))
    elif cmd == "entity" and len(sys.argv)>2:
        print(json.dumps(d.entity_report(sys.argv[2]), indent=2, default=str))
    elif cmd == "integrity":
        print(json.dumps(d.integrity_check(), indent=2, default=str))
    elif cmd == "export":
        out = sys.argv[2] if len(sys.argv)>2 else None
        r = d.registry.export_audit(out)
        print(f"Exported to {out}" if out else json.dumps(r, indent=2, default=str))
    else:
        print("Usage: overview | lookup ID | search --level X | entity NAME | integrity | export [file]")

if __name__ == "__main__": main()
