from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command


from config import ADMIN_IDS

from database import (
    add_source,
    get_all_sources,
    delete_source,
    set_source_active
)


router = Router()



def check_admin(
    user_id
):

    return user_id in ADMIN_IDS





@router.message(Command("channels"))
async def channels(
    message: Message
):

    if not check_admin(
        message.from_user.id
    ):
        return



    sources = await get_all_sources()


    if not sources:

        await message.answer(
            "منبعی وجود ندارد."
        )

        return



    text="منابع:\n\n"


    for s in sources:

        text += (
            f"{s[0]} - {s[1]}\n"
        )


    await message.answer(text)





@router.message(Command("addchannel"))
async def add_channel(
    message: Message
):

    if not check_admin(message.from_user.id):
        return


    args = message.text.split(maxsplit=2)


    if len(args)<3:
        await message.answer(
            "/addchannel name url"
        )
        return



    await add_source(
        args[1],
        "telegram",
        args[2]
    )


    await message.answer(
        "منبع اضافه شد."
    )