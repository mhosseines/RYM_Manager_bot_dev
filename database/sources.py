from .connection import get_connection



async def add_source(
    name,
    source_type,
    url
):

    db = await get_connection()


    await db.execute(
        """
        INSERT INTO sources
        (
            name,
            type,
            url
        )

        VALUES
        (?, ?, ?)

        """,
        (
            name,
            source_type,
            url
        )
    )


    await db.commit()

    await db.close()





async def get_active_sources():

    db = await get_connection()


    cursor = await db.execute(
        """
        SELECT *

        FROM sources

        WHERE active=1

        """
    )


    rows = await cursor.fetchall()


    await db.close()


    return rows





async def get_all_sources():

    db = await get_connection()


    cursor = await db.execute(
        """
        SELECT *

        FROM sources

        """
    )


    rows = await cursor.fetchall()


    await db.close()


    return rows





async def set_source_active(
    source_id,
    active
):

    db = await get_connection()


    await db.execute(
        """
        UPDATE sources

        SET active=?

        WHERE id=?

        """,
        (
            active,
            source_id
        )
    )


    await db.commit()

    await db.close()





async def delete_source(
    source_id
):

    db = await get_connection()


    await db.execute(
        """
        DELETE FROM sources

        WHERE id=?

        """,
        (source_id,)
    )


    await db.commit()

    await db.close()