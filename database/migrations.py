from .connection import get_connection



async def run_migrations():

    db = await get_connection()


    columns = [
        ("normalized_text", "TEXT"),
        ("hash", "TEXT"),
        ("source", "TEXT")
    ]


    for name, typ in columns:

        try:

            await db.execute(
                f"""
                ALTER TABLE posts
                ADD COLUMN {name} {typ}
                """
            )

        except Exception:

            pass


    await db.commit()

    await db.close()