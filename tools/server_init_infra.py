from pathlib import Path

p = Path("bot/server.py")
s = p.read_text(encoding="utf-8").replace("\r\n","\n")

needle = 'from bot.app_factory import build_application'
if needle in s and 'init_infrastructure' not in s:
    s = s.replace(
        needle,
        needle + '\nfrom bot.infrastructure import init_infrastructure',
        1
    )

# Insert await init_infrastructure() at start of lifespan
s = s.replace(
    'print("LIFESPAN: before initialize", flush=True)\n    await ptb_app.initialize()',
    'print("LIFESPAN: before init_infrastructure", flush=True)\n    await init_infrastructure()\n    print("LIFESPAN: after init_infrastructure", flush=True)\n    print("LIFESPAN: before initialize", flush=True)\n    await ptb_app.initialize()',
    1
)

p.write_text(s, encoding="utf-8")
print("OK: server lifespan now initializes infrastructure")
