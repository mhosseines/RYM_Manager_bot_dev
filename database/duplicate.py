import hashlib
import re



from .connection import get_connection





def normalize_text(
    text
):

    text = text.lower()


    text = re.sub(
        r"\s+",
        " ",
        text
    )


    text = re.sub(
        r"[^\w\s]",
        "",
        text
    )


    return text.strip()





def make_hash(
    text
):

    normalized = normalize_text(
        text
    )


    return hashlib.sha256(
        normalized.encode()
    ).hexdigest()





def compute_similarity(
    text1,
    text2
):

    a = set(
        normalize_text(text1).split()
    )

    b = set(
        normalize_text(text2).split()
    )


    if not a or not b:
        return 0


    return len(
        a.intersection(b)
    ) / len(
        a.union(b)
    )





async def hash_already_seen(
    hash_value
):

    db = await get_connection()


    cursor = await db.execute(
        """
        SELECT id

        FROM posts

        WHERE hash=?

        """,
        (
            hash_value,
        )
    )


    row = await cursor.fetchone()


    await db.close()


    return row is not None





async def check_duplicate(
    text
):

    hash_value = make_hash(
        text
    )


    if await hash_already_seen(
        hash_value
    ):
        return True


    return False