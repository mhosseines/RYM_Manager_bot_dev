from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

from config import ADMIN_IDS

from database import (
    get_stats,
    get_pending_posts,
    block_user,
    unblock_user
)

router = Router()



def is_admin(
    user_id
):

    return user_id in ADMIN_IDS





@router.message(Command("admin"))
async def admin_panel(
    message: Message
):

    if not is_admin(
        message.from_user.id
    ):
        return



    await message.answer(
        """
پنل مدیریت:

/status
/pending
/block USER_ID
/unblock USER_ID

"""
    )





@router.message(Command("status"))
async def status(
    message: Message
):

    if not is_admin(message.from_user.id):
        return


    stats = await get_stats()


    await message.answer(
        f"""
📊 وضعیت:

در انتظار:
{stats['pending']}

انتشار امروز:
{stats['published_today']}

رد شده امروز:
{stats['rejected_today']}
"""
    )





@router.message(Command("pending"))
async def pending(
    message: Message
):

    if not is_admin(message.from_user.id):
        return


    posts = await get_pending_posts()


    if not posts:

        await message.answer(
            "موردی نیست."
        )

        return



    text = "لیست انتظار:\n\n"


    for p in posts:

        text += (
            f"#{p[0]}\n"
            f"{(p['text'] or '')[:100]}\n\n"
        )


    await message.answer(text)





@router.message(Command("block"))
async def block(
    message: Message
):

    if not is_admin(message.from_user.id):
        return


    args = message.text.split()


    if len(args) < 2:
        return



    await block_user(
        int(args[1])
    )


    await message.answer(
        "کاربر بلاک شد."
    )





@router.message(Command("unblock"))
async def unblock(
    message: Message
):

    if not is_admin(message.from_user.id):
        return


    args = message.text.split()


    if len(args)<2:
        return



    await unblock_user(
        int(args[1])
    )


    await message.answer(
        "کاربر آزاد شد."
    )