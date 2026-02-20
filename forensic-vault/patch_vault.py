import re

f = "/opt/windi/forensic-vault/forensic_vault.py"
with open(f, "r") as fh:
    code = fh.read()

# 1. Fix DB path
code = code.replace("forensic_ledger.db", "forensic_ledger.sqlite3")

# 2. Fix column names in SQL queries
code = code.replace("receipt_id", "id")
code = code.replace("'title'", "'doc_name'")
code = code.replace('"title"', '"doc_name"')
code = code.replace("r['title']", "r['doc_name']")
code = code.replace("r[\"title\"]", "r[\"doc_name\"]")

print("Patched:", f)
print("Changes: .db->.sqlite3, receipt_id->id, title->doc_name")

with open(f, "w") as fh:
    fh.write(code)
