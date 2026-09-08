from .connection import get_connection



async def add_post(
    user_id,
    text,
    source="user",
    hash_value=None,
    normalized_text=None
):

    db = await get_connection()


    cursor = await db.execute(
        """
        INSERT INTO posts
        (
            user_id,
            text,
            source,
            hash,
            normalized_text,
            status,
            created_at
        )

        VALUES
        (?, ?, ?, ?, ?, 'pending', CURRENT_TIMESTAMP)

        """,
        (
            user_id,
            text,
            source,
            hash_value,
            normalized_text
        )
    )


    await db.commit()


    post_id = cursor.lastrowid


    await db.close()


    return post_id




async def get_post(post_id):

    db = await get_connection()


    cursor = await db.execute(
        """
        SELECT id, user_id, text, status, source, hash, normalized_text, created_at
        FROM posts
        WHERE id=?
        """,
        (post_id,)
    )


    row = await cursor.fetchone()


    await db.close()


    return row




async def update_status(
    post_id,
    status
):

    db = await get_connection()


    await db.execute(
        """
        UPDATE posts

        SET status=?

        WHERE id=?

        """,
        (
            status,
            post_id
        )
    )


    await db.commit()

    await db.close()





async def claim_pending_post():

    db = await get_connection()


    cursor = await db.execute(
        """
        SELECT id
        FROM posts
        WHERE status='pending'
        ORDER BY id ASC
        LIMIT 1

        """
    )


    row = await cursor.fetchone()


    if not row:

        await db.close()

        return None



    post_id = row[0]


    await db.execute(
        """
        UPDATE posts

        SET status='processing'

        WHERE id=?

        """,
        (post_id,)
    )


    await db.commit()

    await db.close()


    return post_id




async def reject_pending_post(
    post_id
):

    await update_status(
        post_id,
        "rejected"
    )





async def update_pending_post_text(
    post_id,
    text
):

    db = await get_connection()


    await db.execute(
        """
        UPDATE posts

        SET text=?

        WHERE id=?

        """,
        (
            text,
            post_id
        )
    )


    await db.commit()

    await db.close()





async def save_channel_msg_id(
    post_id,
    msg_id
):

    db = await get_connection()


    await db.execute(
        """
        UPDATE posts

        SET channel_msg_id=?

        WHERE id=?

        """,
        (
            msg_id,
            post_id
        )
    )


    await db.commit()

    await db.close()