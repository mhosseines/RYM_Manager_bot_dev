from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)





def admin_keyboard():

    return ReplyKeyboardMarkup(
        keyboard=[

            [
                KeyboardButton(
                    text="/status"
                ),

                KeyboardButton(
                    text="/pending"
                )
            ],

            [
                KeyboardButton(
                    text="/channels"
                )
            ]

        ],

        resize_keyboard=True
    )


def post_moderation_keyboard(post_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ انتشار",
                    callback_data=f"approve:{post_id}",
                ),
                InlineKeyboardButton(
                    text="❌ رد",
                    callback_data=f"reject:{post_id}",
                ),
            ]
        ]
    )