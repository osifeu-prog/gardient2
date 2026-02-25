from pathlib import Path

p = Path("bot/config.py")
s = p.read_text(encoding="utf-8").replace("\r\n","\n")
if "DONATE_URL" not in s:
    s += "\n# Payments (MVP)\nDONATE_URL = os.getenv(\"DONATE_URL\")\n"
    p.write_text(s, encoding="utf-8")
    print("OK: added DONATE_URL to bot/config.py")
else:
    print("OK: DONATE_URL already present")
