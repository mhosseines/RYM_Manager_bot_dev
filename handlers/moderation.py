from aiogram import Router
from aiogram.types import CallbackQuery


from database import (
    update_status,
    get_post
)


from services.publisher import publish_post



router = Router()





@router.callback_query(
    lambda c: c.data.startswith("approve:")
)
async def approve(
    callback: CallbackQuery
):

    post_id = int(
        callback.data.split(":")[1]
    )


    post = await get_post(
        post_id
    )


    await publish_post(
        post
    )


    await update_status(
        post_id,
        "published"
    )


    await callback.answer(
        "منتشر شد"
    )







@router.callback_query(
    lambda c:c.data.startswith("reject:")
)
async def reject(
    callback: CallbackQuery
):

    post_id=int(
        callback.data.split(":")[1]
    )


    await update_status(
        post_id,
        "rejected"
    )


    await callback.answer(
        "رد شد"
    )