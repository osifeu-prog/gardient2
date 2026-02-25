from pathlib import Path
import re

p = Path("bot/app_factory.py")
s = p.read_text(encoding="utf-8").replace("\r\n","\n")

# Find menu_cmd block
m = re.search(r"(?m)^async def menu_cmd\([^\)]*\):\n([\s\S]*?)(?=^\S)", s)
if not m:
    raise SystemExit("ERROR: menu_cmd not found")

block = m.group(0)

# Replace the default lines list to include new commands
block2 = re.sub(
    r'lines\s*=\s*\[[^\]]*\]',
    'lines = ["Commands:", "/start", "/status", "/menu", "/whoami", "/health", "/donate", "/admins", "/grant_admin", "/revoke_admin", "/dm", "/broadcast_admins"]',
    block,
    count=1
)

if block2 == block:
    # if pattern didn't match, just append additions after existing lines definition
    block2 = block.replace('"/health"', '"/health", "/donate", "/admins", "/grant_admin", "/revoke_admin", "/dm", "/broadcast_admins"')

s = s.replace(block, block2, 1)
p.write_text(s, encoding="utf-8")
print("OK: patched menu_cmd commands list")
