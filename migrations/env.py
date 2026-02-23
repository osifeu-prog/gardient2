# Alembic env.py
from logging.config import fileConfig
from sqlalchemy import engine_from_config
from alembic import context

config = context.config
fileConfig(config.config_file_name)
target_metadata = None
