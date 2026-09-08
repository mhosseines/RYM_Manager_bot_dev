from core.bot_instance import bot

from config import CHANNEL_ID
from utils.formatter import format_for_channel




async def publish_post(
    post
):

    if not post:
        return None


    text = post["text"]

    if not text:
        return None


    message = await bot.send_message(
        CHANNEL_ID,
        format_for_channel(text)
    )


    return message.message_id