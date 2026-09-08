from .connection import get_connection



async def log_action(
    action,
    user_id=None
):

    db = await get_connection()


    await db.execute(
        """
        INSERT INTO logs
        (
            action,
            user_id
        )

        VALUES
        (?, ?)

        """,
        (
            action,
            user_id
        )
    )


    await db.commit()

    await db.close()