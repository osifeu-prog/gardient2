from pathlib import Path

p = Path("bot/server.py")
s = p.read_text(encoding="utf-8").replace("\r\n", "\n")

marker = 'print("FASTAPI_BOOT_OK", flush=True)\n'
if "FASTAPI_BOOT_OK" not in s:
    # inject right after 'import logging' (first occurrence)
    s = s.replace(
        "import logging\n",
        "import logging\nimport sys\n" + marker,
        1
    )
    p.write_text(s, encoding="utf-8")
    print("OK: injected FASTAPI_BOOT_OK")
else:
    print("OK: marker already present")
