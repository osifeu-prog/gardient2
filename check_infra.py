import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine

DATABASE_URL = os.getenv('DATABASE_URL_ASYNC')
if not DATABASE_URL:
    raise RuntimeError('DATABASE_URL_ASYNC is not set!')

async def test_db_connection():
    print(f'Testing DB connection to: {DATABASE_URL}')
    try:
        engine = create_async_engine(DATABASE_URL, echo=True)
        async with engine.begin() as conn:
            await conn.run_sync(lambda conn: print('DB Connection Successful'))
        await engine.dispose()
        print('? DB check passed')
    except Exception as e:
        print(f'? DB check failed: {e}')

if __name__ == '__main__':
    asyncio.run(test_db_connection())
