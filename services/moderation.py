from database import (
    update_status,
    get_post
)

from services.publisher import publish_post





async def approve_post(
    post_id
):

    post = await get_post(
        post_id
    )


    if not post:
        return False



    message_id = await publish_post(
        post
    )


    await update_status(
        post_id,
        "published"
    )


    return message_id





async def reject_post(
    post_id
):

    await update_status(
        post_id,
        "rejected"
    )


    return True