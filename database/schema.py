from .connection import get_connection


async def create_tables():

    db = await get_connection()


    await db.execute("""
    CREATE TABLE IF NOT EXISTS posts (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        user_id INTEGER,

        text TEXT,

        status TEXT DEFAULT 'pending',

        source TEXT,

        hash TEXT,

        normalized_text TEXT,

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

    )
    """)



    await db.execute("""
    CREATE TABLE IF NOT EXISTS sources (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        name TEXT,

        type TEXT,

        url TEXT,

        active INTEGER DEFAULT 1

    )
    """)



    await db.execute("""
    CREATE TABLE IF NOT EXISTS blocked_users (

        user_id INTEGER PRIMARY KEY

    )
    """)



    await db.execute("""
    CREATE TABLE IF NOT EXISTS logs (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        action TEXT,

        user_id INTEGER,

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

    )
    """)



    await db.commit()

    await db.close()