from pathlib import Path

p = Path("bot/app_factory.py")
s = p.read_text(encoding="utf-8").replace("\r\n","\n")

repls = {
    "SLH Guardian ? Security + Ops Control": "SLH Guardian ? Security + Ops Control",
    '"?? WHOAMI"': '"WHOAMI"',
    '"?? BOOT/ADMIN REPORT"': '"BOOT/ADMIN REPORT"',
}

for a,b in repls.items():
    s = s.replace(a,b)

p.write_text(s, encoding="utf-8")
print("OK: final UI cleanup")
