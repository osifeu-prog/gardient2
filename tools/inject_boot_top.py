from pathlib import Path

p = Path("bot/server.py")
s = p.read_text(encoding="utf-8").replace("\r\n", "\n")

marker = 'print("FASTAPI_BOOT_TOP", flush=True)\n'
if not s.startswith('print("FASTAPI_BOOT_TOP"'):
    s = marker + s
    p.write_text(s, encoding="utf-8")
    print("OK: injected FASTAPI_BOOT_TOP at file start")
else:
    print("OK: FASTAPI_BOOT_TOP already present")
