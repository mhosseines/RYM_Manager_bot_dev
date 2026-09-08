from core.bot_instance import bot

from config import ADMIN_IDS
from database import get_post
from keyboards.admin import post_moderation_keyboard




async def notify_admins(
    text
):

    for admin_id in ADMIN_IDS:

        await bot.send_message(
            admin_id,
            text
        )





async def notify_user(
    user_id,
    text
):

    await bot.send_message(
        user_id,
        text
    )


async def notify_post_to_admins(post_id):
    post = await get_post(post_id)
    if not post:
        return

    text = post["text"] or "(بدون متن)"
    source = post["source_name"] or post["source_type"] or "user"
    message = f"پست جدید #{post_id}\nمنبع: {source}\n\n{text}"
    keyboard = post_moderation_keyboard(post_id)
    for admin_id in ADMIN_IDS:
        await bot.send_message(
            admin_id,
            message,
            reply_markup=keyboard,
        )