from pathlib import Path

p = Path("migrations/versions")
targets = sorted(p.glob("admins_requests_*.py"))
if not targets:
    raise SystemExit("ERROR: no admins_requests_*.py found")

needle = "\\\"\\\"\\\""   # this is: \"\"\" literally (backslash before EACH quote)

for f in targets:
    s = f.read_text(encoding="utf-8", errors="ignore").replace("\r\n","\n")
    if needle not in s:
        print("WARN: needle not found in", f.name)
    s2 = s.replace(needle, '"""')
    if s2 != s:
        f.write_text(s2, encoding="utf-8")
        print("OK: fixed", f.name)
    else:
        print("OK: no change", f.name)
