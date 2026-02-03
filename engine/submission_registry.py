"""
WINDI Submission Registry v1.0
Heritage: IPFS anchor -> audit registry. Queryable submission storage.
AI processes. Human decides. WINDI guarantees.
"""
import json, os
from datetime import datetime, timezone

class SubmissionRegistry:
    def __init__(self, storage_dir):
        self.storage_dir = storage_dir
        self.file = os.path.join(storage_dir, "registry.json")
        os.makedirs(storage_dir, exist_ok=True)

    def _load(self):
        if os.path.exists(self.file):
            with open(self.file) as f:
                return json.load(f)
        return {"entries": [], "stats": {"total": 0, "by_level": {}, "by_entity": {}}}

    def _save(self, data):
        data["last_updated"] = datetime.now(timezone.utc).isoformat()
        with open(self.file, "w") as f:
            json.dump(data, f, indent=2, default=str)

    def register(self, submission_id, audit_record, document_id=None):
        data = self._load()
        meta = audit_record.get("metadata", {})
        entry = {
            "submission_id": submission_id,
            "document_id": document_id,
            "registered_at": datetime.now(timezone.utc).isoformat(),
            "governance_level": audit_record.get("governance_level", ""),
            "policy_version": audit_record.get("policy_version", ""),
            "config_hash": audit_record.get("config_hash", ""),
            "integrity_hash": audit_record.get("integrity_hash", ""),
            "reporting_entity": meta.get("reporting_entity", ""),
            "reference_period": meta.get("reference_period", ""),
            "validation_status": meta.get("validation_status", ""),
        }
        data["entries"].append(entry)
        # Stats
        data["stats"]["total"] = len(data["entries"])
        lv = entry["governance_level"]
        data["stats"]["by_level"][lv] = data["stats"]["by_level"].get(lv, 0) + 1
        ent = entry["reporting_entity"] or "unknown"
        data["stats"]["by_entity"][ent] = data["stats"]["by_entity"].get(ent, 0) + 1
        self._save(data)
        return entry

    def lookup(self, submission_id):
        for e in self._load()["entries"]:
            if e["submission_id"] == submission_id:
                return e
        return None

    def query(self, level=None, entity=None, after=None, before=None, limit=50):
        results = self._load()["entries"]
        if level:
            results = [e for e in results if e.get("governance_level") == level.upper()]
        if entity:
            el = entity.lower()
            results = [e for e in results if el in e.get("reporting_entity", "").lower()]
        if after:
            results = [e for e in results if e.get("registered_at", "") >= after]
        if before:
            results = [e for e in results if e.get("registered_at", "") <= before]
        results.sort(key=lambda e: e.get("registered_at", ""), reverse=True)
        return results[:limit]

    def get_stats(self):
        return self._load().get("stats", {})

    def export_audit(self, path=None):
        data = self._load()
        export = {
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "total": data["stats"]["total"],
            "stats": data["stats"],
            "entries": data["entries"],
        }
        if path:
            with open(path, "w") as f:
                json.dump(export, f, indent=2, default=str)
        return export

    def verify_chain(self):
        entries = self._load()["entries"]
        total = len(entries)
        sealed = sum(1 for e in entries if e.get("integrity_hash"))
        return sealed == total, {"total": total, "sealed": sealed, "complete": sealed == total}
