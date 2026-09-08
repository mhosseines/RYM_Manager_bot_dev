import asyncio


from database import (
    get_sync_state,
    set_sync_state,
    mark_message_mirrored,
    is_mirrored_message
)





async def initialize_bale_offset():

    offset = await get_sync_state(
        "bale_offset"
    )


    if offset is None:

        await set_sync_state(
            "bale_offset",
            "0"
        )





async def handle_bale_message(
    message
):

    source_chat_id = str(message.chat.id)
    message_id = str(message.id)


    if await is_mirrored_message(
        source_chat_id,
        message_id
    ):
        return



    # اینجا بعداً انتقال Bale -> Telegram انجام می‌شود


    await mark_message_mirrored(
        source_chat_id,
        message_id,
        None
    )





async def bale_listener():

    await initialize_bale_offset()


    while True:

        # دریافت پیام‌های جدید Bale

        await asyncio.sleep(
            10
        )