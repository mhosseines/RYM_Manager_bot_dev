from aiogram.types import ReplyKeyboardMarkup
from aiogram.types import KeyboardButton





def user_keyboard():

    return ReplyKeyboardMarkup(
        keyboard=[

            [
                KeyboardButton(
                    text="ارسال خبر"
                )
            ]

        ],

        resize_keyboard=True
    )