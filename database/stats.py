from .connection import get_connection




async def get_stats():

    db = await get_connection()


    cursor = await db.execute(
        """
        SELECT

        COUNT(*),

        SUM(
            CASE
            WHEN status='pending'
            THEN 1
            ELSE 0
            END
        ),

        SUM(
            CASE
            WHEN status='published'
            THEN 1
            ELSE 0
            END
        )

        FROM posts

        """
    )


    row = await cursor.fetchone()


    await db.close()


    return {

        "total": row[0] or 0,

        "pending": row[1] or 0,

        "published": row[2] or 0

    }






async def get_pending_posts(
    limit=20
):

    db = await get_connection()


    cursor = await db.execute(
        """
        SELECT id, user_id, text, status, source, hash, normalized_text, created_at

        FROM posts

        WHERE status='pending'

        ORDER BY id DESC

        LIMIT ?

        """,
        (
            limit,
        )
    )


    rows = await cursor.fetchall()


    await db.close()


    return rows