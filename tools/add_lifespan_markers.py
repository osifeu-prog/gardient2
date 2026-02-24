from pathlib import Path
import re

p = Path("bot/server.py")
s = p.read_text(encoding="utf-8").replace("\r\n","\n")

# insert prints inside lifespan
s = s.replace("await ptb_app.initialize()", 'print("LIFESPAN: before initialize", flush=True)\n    await ptb_app.initialize()\n    print("LIFESPAN: after initialize", flush=True)', 1)
s = s.replace("await ptb_app.start()", 'await ptb_app.start()\n    print("LIFESPAN: after start", flush=True)', 1)
s = s.replace("await ptb_app.stop()", 'print("LIFESPAN: shutting down", flush=True)\n        await ptb_app.stop()', 1)

p.write_text(s, encoding="utf-8")
print("OK: added lifespan markers")
