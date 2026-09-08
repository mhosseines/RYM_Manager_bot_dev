import aiosqlite

from config import DATABASE_NAME


async def get_connection():

    return await aiosqlite.connect(
        DATABASE_NAME
    )


async def init_db():

    db = await get_connection()

    await db.execute(
        "PRAGMA journal_mode=WAL;"
    )

    await db.commit()

    await db.close()