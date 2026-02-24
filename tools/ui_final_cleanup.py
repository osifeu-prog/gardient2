from pathlib import Path

p = Path("bot/app_factory.py")
s = p.read_text(encoding="utf-8").replace("\r\n","\n")

# Fix title dash
s = s.replace("SLH Guardian ? Security + Ops Control", "SLH Guardian ? Security + Ops Control")

# Fix admin header
s = s.replace("?? BOOT/ADMIN REPORT", "BOOT/ADMIN REPORT")

p.write_text(s, encoding="utf-8")
print("OK: UI final cleanup")
