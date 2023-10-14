from aiogram.types import InlineKeyboardButton as B
from aiogram.types import InlineKeyboardMarkup as M

from aiogram.types import ReplyKeyboardMarkup as RM
from aiogram.types import KeyboardButton as RB

start_kb = M(
    inline_keyboard=[
        [
            B(
                text='✅ Начать', callback_data='start'
            )
        ]
    ]
)

start2_kb = RM(keyboard=[
    [
        RB(
            text='Отправить',
            request_contact=True
        )
    ]
],
    resize_keyboard=True)


num = M(
    inline_keyboard=[
        [

            B(text='1️⃣', callback_data='write_1'),
            B(text='2️⃣', callback_data='write_2'),
            B(text='3️⃣', callback_data='write_3'),
        ],
        [
            B(text='4️⃣', callback_data='write_4'),
            B(text='5️⃣', callback_data='write_5'),
            B(text='6️⃣', callback_data='write_6'),
        ],
        [
            B(text='7️⃣', callback_data='write_7'),
            B(text='8️⃣', callback_data='write_8'),
            B(text='9️⃣', callback_data='write_9'),
        ],
        [
            B(text='⬅️', callback_data='remove'),
            B(text='0️⃣', callback_data='write_0'),
            B(text='✅', callback_data='ready'),
        ]
    ]
)
