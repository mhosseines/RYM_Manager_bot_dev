from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

from database import (
    add_post,
    is_user_blocked,
    check_rate_limit,
    log_action,
    record_submission
)

from services.notifier import notify_post_to_admins
from utils.text import trim_text


router = Router()



@router.message(Command("start"))
async def start_handler(
    message: Message
):

    await message.answer(
        "سلام 👋\n"
        "خبر یا محتوای خود را ارسال کنید."
    )





@router.message()
async def receive_text(
    message: Message
):

    user_id = message.from_user.id


    if await is_user_blocked(user_id):

        await message.answer(
            "شما اجازه ارسال محتوا ندارید."
        )

        return



    if check_rate_limit(user_id) > 0:

        await message.answer(
            "تعداد ارسال‌ها زیاد است."
        )

        return



    text = message.text


    if not text:
        return



    text = trim_text(text)



    post_id = await add_post(
        content_type="text",
        text=text,
        user_id=user_id,
        source_type="user"
    )

    await log_action(post_id, "submitted")
    record_submission(user_id)
    await notify_post_to_admins(post_id)



    await message.answer(
        f"✅ دریافت شد\n"
        f"شماره پیگیری: {post_id}"
    )