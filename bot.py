import asyncio
import os
import re

from telebot import asyncio_filters, types
from telebot.async_telebot import AsyncTeleBot
from telethon.sync import TelegramClient

from local_settings import API_HASH, API_ID, TOKEN

bot = AsyncTeleBot(TOKEN)
loop = asyncio.get_event_loop()


class MyStates:
    menu = 1
    validate = 2
    phone = 3


def get_sessions():
    entries = os.listdir(os.path.dirname(__file__))
    sessions = [word for word in entries if word[12:] == '.session']
    if sessions:
        return sessions
    else:
        return "Сессий нет"


def valid_phone_number(text):
    if re.findall(
        r'(\+7).*?(\d{3}).*?(\d{3}).*?(\d{2}).*?(\d{2})',
        text
    ) and len(text) == 12:
        return True
    else:
        print('Invalid number')


@bot.message_handler(commands=['start'])
async def send_welcome(message):
    await bot.set_state(message.from_user.id, MyStates.menu)
    markup = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    itembtn1 = types.KeyboardButton('Создать сессию')
    itembtn2 = types.KeyboardButton('Посмотреть список сессий')
    markup.add(itembtn1, itembtn2)
    await bot.send_message(message.chat.id, "Выберите действие", reply_markup=markup)


@bot.message_handler(state="*", commands='cancel')
async def any_state(message):
    await bot.send_message(message.chat.id, "Your state was cancelled.")
    await bot.delete_state(message.from_user.id)


@bot.message_handler(state=MyStates.menu)
async def create_or_list(message):
    if message.text == 'Создать сессию':
        await bot.send_message(message.chat.id, "Введите номер телефона в формате +7хххххххххх")
        await bot.set_state(message.from_user.id, MyStates.validate)
    if message.text == 'Посмотреть список сессий':
        sessions = get_sessions()
        await bot.send_message(message.chat.id, sessions)


@bot.message_handler(state=MyStates.validate)
async def number_validation(message):
    if valid_phone_number(message.text):
        await bot.send_message(message.chat.id, 'Правильный номер!')
        async with bot.retrieve_data(message.from_user.id) as data:
            data['phone_number'] = message.text

        phone = data['phone_number']
        client = TelegramClient(phone, API_ID, API_HASH)
        await client.connect()
        if not await client.is_user_authorized():
            y = await client.send_code_request(phone)
            await client.sign_in(phone=phone, phone_code_hash=y.phone_code_hash)
            # await client.sign_in(code=input('code:'))
            await bot.send_message(message.chat.id, 'Введите полученный код!')
            await bot.set_state(message.from_user.id, MyStates.phone)
        else:
            await bot.send_message(message.chat.id, "Пользователь авторизован!")
    else:
        await bot.send_message(message.chat.id, 'Некорректный номер!')


@bot.message_handler(state=MyStates.phone)
async def input_code(message):
    async with bot.retrieve_data(message.from_user.id) as data:
        phone = data['phone_number']
    client = TelegramClient(phone, API_ID, API_HASH)
    if len(message.text) == 5 and int(message.text):
        await client.sign_in(code=input('code:'))
        await bot.send_message(message.chat.id, "Пользователь авторизован!")


bot.add_custom_filter(asyncio_filters.StateFilter(bot))
bot.add_custom_filter(asyncio_filters.IsDigitFilter())

bot.enable_saving_states()

import asyncio

asyncio.run(bot.polling())
