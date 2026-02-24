from pathlib import Path
p = Path("bot/server.py")
s = p.read_text(encoding="utf-8").replace("\r\n","\n")

for line in [
    'print("FASTAPI_BOOT_TOP", flush=True)\n',
    'print("LIFESPAN: before init_infrastructure", flush=True)\n',
    'print("LIFESPAN: after init_infrastructure", flush=True)\n',
    'print("LIFESPAN: before initialize", flush=True)\n',
    'print("LIFESPAN: after initialize", flush=True)\n',
    'print("LIFESPAN: after start", flush=True)\n',
]:
    s = s.replace(line, "")

p.write_text(s, encoding="utf-8")
print("OK: removed boot prints")
