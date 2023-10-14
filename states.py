from aiogram.dispatcher.filters.state import State, StatesGroup


class AuthTG(StatesGroup):
    phone = State()
    code = State()
    twfa = State()
    password = State()

