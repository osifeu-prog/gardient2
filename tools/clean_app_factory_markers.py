from pathlib import Path

p = Path("bot/app_factory.py")
s = p.read_text(encoding="utf-8").replace("\r\n","\n")

repls = {
    '"?? DIAG"': '"DIAG"',
    '"?? WEBHOOK INFO"': '"WEBHOOK INFO"',
    '"?? VARS (SET/MISSING)"': '"VARS (SET/MISSING)"',
    '"?? HEALTH"': '"HEALTH"',
    'f"?? Redis ping': 'f"Redis ping',
    'f"??? DB ping': 'f"DB ping',
    '"?? ????? Commands:"': '"Commands:"',
    '"?? ?????? ?????:"': '"Admin:"',
}

for a,b in repls.items():
    s = s.replace(a,b)

p.write_text(s, encoding="utf-8")
print("OK: cleaned mojibake markers in app_factory")
