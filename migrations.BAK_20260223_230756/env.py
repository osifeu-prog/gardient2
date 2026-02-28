import os
from alembic import context
from sqlalchemy import engine_from_config, pool

# Import your metadata
from app.db.database import Base
from app.models.core import (
    User, AuditLog, RewardLedger,
    ExpertCategory, ExpertCandidate, ExpertVote,
    P2POrder, ManagedGroup
)

config = context.config
target_metadata = Base.metadata

def _to_sync_url(url: str) -> str:
    if url.startswith('postgres://'):
        url = url.replace('postgres://', 'postgresql://', 1)
    if url.startswith('postgresql+asyncpg://'):
        url = url.replace('postgresql+asyncpg://', 'postgresql://', 1)
    return url

def get_url() -> str:
    db = os.getenv('DATABASE_URL', '')
    if not db:
        raise RuntimeError('DATABASE_URL missing for alembic')
    return _to_sync_url(db)

def run_migrations_offline() -> None:
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
        dialect_opts={'paramstyle': 'named'},
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    configuration = config.get_section(config.config_ini_section) or {}
    configuration['sqlalchemy.url'] = get_url()

    connectable = engine_from_config(
        configuration,
        prefix='sqlalchemy.',
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
