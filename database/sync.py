from .connection import get_connection



async def get_sync_state(
    key
):

    db = await get_connection()


    cursor = await db.execute(
        """
        SELECT value

        FROM sync_state

        WHERE key=?

        """,
        (key,)
    )


    row = await cursor.fetchone()


    await db.close()


    if row:
        return row[0]

    return None





async def set_sync_state(
    key,
    value
):

    db = await get_connection()


    await db.execute(
        """
        INSERT INTO sync_state
        (
            key,
            value
        )

        VALUES
        (?, ?)

        ON CONFLICT(key)

        DO UPDATE SET value=excluded.value

        """,
        (
            key,
            value
        )
    )


    await db.commit()

    await db.close()





async def is_mirrored_message(
    message_id
):

    db = await get_connection()


    cursor = await db.execute(
        """
        SELECT 1

        FROM mirrored_messages

        WHERE message_id=?

        """,
        (
            message_id,
        )
    )


    result = await cursor.fetchone()


    await db.close()


    return result is not None





async def mark_message_mirrored(
    message_id
):

    db = await get_connection()


    await db.execute(
        """
        INSERT OR IGNORE INTO mirrored_messages

        (
            message_id
        )

        VALUES
        (?)

        """,
        (
            message_id,
        )
    )


    await db.commit()

    await db.close()