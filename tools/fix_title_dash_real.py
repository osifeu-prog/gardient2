from pathlib import Path
p = Path("bot/app_factory.py")
s = p.read_text(encoding="utf-8").replace("\r\n","\n")
s = s.replace("SLH Guardian ? Security + Ops Control", "SLH Guardian ? Security + Ops Control")
p.write_text(s, encoding="utf-8")
print("OK: replaced ? with ? in title")
