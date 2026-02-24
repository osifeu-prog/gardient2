import os, sys
from pathlib import Path
from alembic.config import Config
from alembic.script import ScriptDirectory

print("CWD =", os.getcwd())
print("sys.executable =", sys.executable)

ini = Path("alembic.ini").resolve()
print("ini.exists =", ini.exists())
print("ini.path   =", ini)

cfg = Config(str(ini))
print("cfg.config_file_name =", cfg.config_file_name)
print("script_location(opt) =", cfg.get_main_option("script_location"))

sd = ScriptDirectory.from_config(cfg)
print("sd.dir      =", sd.dir)
print("sd.versions =", sd.versions)

v = Path(sd.versions)
files = sorted(v.glob("*.py")) if v.exists() else []
print("versions exists =", v.exists(), "count =", len(files))
for p in files[:30]:
    print(" -", p.name)

print("heads =", sd.get_heads())
