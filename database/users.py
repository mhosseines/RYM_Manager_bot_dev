import time

from .connection import get_connection



async def block_user(user_id):

    db = await get_connection()


    await db.execute(
        """
        INSERT OR IGNORE INTO blocked_users
        (user_id)

        VALUES(?)

        """,
        (user_id,)
    )


    await db.commit()

    await db.close()





async def unblock_user(user_id):

    db = await get_connection()


    await db.execute(
        """
        DELETE FROM blocked_users

        WHERE user_id=?

        """,
        (user_id,)
    )


    await db.commit()

    await db.close()





async def is_user_blocked(user_id):

    db = await get_connection()


    cursor = await db.execute(
        """
        SELECT 1

        FROM blocked_users

        WHERE user_id=?

        """,
        (user_id,)
    )


    result = await cursor.fetchone()


    await db.close()


    return result is not None





async def check_rate_limit(
    user_id,
    limit=5,
    period=60
):

    db = await get_connection()


    cursor = await db.execute(
        """
        SELECT COUNT(*)

        FROM posts

        WHERE user_id=?

        AND created_at > datetime('now', ?)

        """,
        (
            user_id,
            f"-{period} seconds"
        )
    )


    count = await cursor.fetchone()


    await db.close()


    return count[0] < limit





async def record_submission(user_id):

    return True