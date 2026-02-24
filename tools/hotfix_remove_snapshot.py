from pathlib import Path
import re

p = Path("bot/app_factory.py")
s = p.read_text(encoding="utf-8").replace("\r\n","\n")

# 1) Remove snapshot_cmd function block if present
s = re.sub(r'\nasync def snapshot_cmd\([\s\S]*?\n(?=async def admin_cmd)', "\n", s, count=1)

# 2) Remove handler registration for snapshot if present
s = s.replace('app.add_handler(CommandHandler("snapshot", with_latency("snapshot", snapshot_cmd)))\n    ', '')

# 3) Remove /snapshot from start text and menu list (best effort)
s = s.replace('/snapshot  snapshot\\n', '')
s = s.replace(', "/snapshot"]', ']')
s = s.replace(', "/snapshot"', '')

p.write_text(s, encoding="utf-8")
print("OK: removed /snapshot from bot/app_factory.py")
