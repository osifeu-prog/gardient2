from pathlib import Path

needle = b"20260211_215612_manh_payments_v1"
root = Path(r"D:\")
hits = []

for p in root.rglob("*.py"):
    s = str(p).lower()
    if ("migrations" not in s) and ("alembic" not in s):
        continue
    try:
        b = p.read_bytes()
    except Exception:
        continue
    if needle in b:
        hits.append(str(p))

print("HITS:", len(hits))
for h in hits[:100]:
    print(h)
