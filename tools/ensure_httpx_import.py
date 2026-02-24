from pathlib import Path

p = Path("bot/app_factory.py")
s = p.read_text(encoding="utf-8").replace("\r\n","\n")

if "import httpx" not in s:
    # Put it near other top-level imports
    lines = s.splitlines(True)
    insert_at = 0
    for i, ln in enumerate(lines):
        # insert after last "import ..." line at the top block
        if ln.startswith("import ") or ln.startswith("from "):
            insert_at = i + 1
        else:
            # stop at first non-import line after imports start
            if i > 0:
                break
    lines.insert(insert_at, "import httpx\n")
    s = "".join(lines)

p.write_text(s, encoding="utf-8")
print("OK: ensured import httpx")
