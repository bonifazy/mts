from aiogram import Bot, Router, flags
from aiogram.types import Message, User, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove
from aiogram.types.callback_query import CallbackQuery
from aiogram.client.session.aiohttp import ClientSession
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import logging
import json
import smtplib
from pathlib import Path

from db import register_user, register_incident
from settings import LOG_FILE, DATA_DIR, API_URL, FROM_SMTP, TO_SMTP


router = Router()
logging.basicConfig(filename=LOG_FILE,
                    level=logging.INFO,
                    filemode='a',
                    datefmt='%Y-%m-%d, %H:%M',
                    format='%(asctime)s: %(name)s: %(levelname)s: %(message)s')
log = logging.getLogger('Handlers')


class Incident(StatesGroup):
    theme = State()
    description = State()
    contact = State()
    file = State()


@router.message(Command('start'))
async def start(msg: Message):
    user_id = msg.from_user.id
    first_name = msg.from_user.first_name
    user_name = msg.from_user.username
    text = f'Привет, {first_name}\n\nБот формирует запрос на сервис поддержки для регистрации инцидента.\n\n' \
           f'/api - отправить запрос по API\n/smtp - отправить запрос по SMTP'

    await msg.answer(text=text)
    register_user(user_id=user_id, firstname=first_name, username=user_name)
    log.info(f'@{user_name}: id {user_id} starts chat with bot.')


@router.message(Command('api'))
async def api(msg: Message, state: FSMContext):
    user_id = msg.from_user.id
    user_name = msg.from_user.username

    await msg.answer(text='Для отправки обращения через API сервиса введите тему обращения, опишите ситуацию, '
                          'оставьте контакты для обратной связи и отправьте файл для детального ознакомления.')
    await msg.answer(text='Введите тему обращения:')
    await state.update_data(from_command='api')
    await state.set_state(Incident.theme)
    log.info(f'@{user_name}: id {user_id} push /api button.')


@router.message(Command('smtp'))
async def smtp(msg: Message, state: FSMContext):
    user_id = msg.from_user.id
    user_name = msg.from_user.username

    await msg.answer(text='Для отправки обращения через SMTP сервиса введите тему обращения, опишите ситуацию, '
                          'оставьте контакты для обратной связи и отправьте файл для детального ознакомления.')
    await msg.answer(text='Введите тему обращения:')
    await state.update_data(from_command='smtp')
    await state.set_state(Incident.theme)
    log.info(f'@{user_name}: id {user_id} push /smtp button.')


@router.message(Incident.theme)
async def incident_theme(msg: Message, state: FSMContext):
    await state.update_data(incident_theme=msg.text)
    await msg.answer(text='Опишите подробнее ситуацию:')
    await state.set_state(Incident.description)


@router.message(Incident.description)
async def incident_description(msg: Message, state: FSMContext):
    await state.update_data(incident_description=msg.text)
    send_claim = InlineKeyboardButton(text='Отправить обращение', callback_data='send_incident')
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[send_claim]])
    await msg.answer(text='Отправьте запрос анонимно, нажав на кнопку `Отправить обращение`', reply_markup=keyboard)
    await msg.answer(text='Либо оставьте контакт для обратной связи:', reply_markup=ReplyKeyboardRemove())
    await state.set_state(Incident.contact)


@router.message(Incident.contact)
async def incident_contact(msg: Message, state: FSMContext):
    await state.update_data(incident_contact=msg.text)
    send_claim = InlineKeyboardButton(text='Отправить обращение', callback_data='send_incident')
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[send_claim]])
    await msg.answer(text='Отправьте запрос, нажав на кнопку `Отправить обращение`', reply_markup=keyboard)
    await msg.answer(text='Либо прикрепите файл к сообщению для детального описания ситуации:',
                     reply_markup=ReplyKeyboardRemove())
    await state.set_state(Incident.file)


@router.message(Incident.file)
async def incident_file(msg: Message, bot: Bot, state: FSMContext):
    document = msg.document
    file_name = Path(DATA_DIR, msg.document.file_name)
    await bot.download(file=document, destination=file_name)
    if file_name.is_file():
        await state.update_data(incident_file=str(file_name.absolute()))
    await state.set_state(state=None)
    state_data = await state.get_data()
    theme = state_data.get('incident_theme', '')
    description = state_data.get('incident_description', '')
    contact = state_data.get('incident_contact', '')
    file = state_data.get('incident_file', '')
    from_command = state_data.get('from_command', '')
    data = {
        'theme': theme,
        'description': description,
        'contact': contact,
        'file': file
    }
    await send_incident(from_user=msg.from_user, message=msg, data=data, from_command=from_command)


@router.callback_query()
@flags.callback_answer(text='send_incident', cache_time=10)
async def prepare_to_send(call: CallbackQuery, state: FSMContext):
    await state.set_state(state=None)
    state_data = await state.get_data()
    theme = state_data.get('incident_theme', '')
    description = state_data.get('incident_description', '')
    contact = state_data.get('incident_contact', '')
    file = state_data.get('incident_file', '')

    from_command = state_data.get('from_command', '')
    data = {
        'theme': theme,
        'description': description,
        'contact': contact,
        'file': file
    }
    await send_incident(from_user=call.from_user, message=call.message, data=data, from_command=from_command)


async def send_incident(from_user: User, message: Message, data: dict, from_command: str):
    theme = data['theme']
    description = data['description']
    contact = data['contact']
    file = data['file']
    incident = {
        'incident': {
            'theme': theme,
            'description': description,
            'contact': contact,
            'file': file
        }
    }

    # write incident to database
    register_incident(user_id=from_user.id, theme=theme, description=description, contact=contact, file=file)
    await message.answer('Обращение зарегистрировано в базе данных.')
    #send incident info to REST API or send email with SMTP
    if from_command == 'api':
        json_data = json.dumps(obj=incident)
        async with ClientSession() as session:
            async with session.post(url=API_URL, data=json_data) as response:
                status = response.status
                if status == 200:
                    data_from_api = await response.json(encoding='utf-8')
        if data_from_api:
            incident_info = data_from_api['json']['incident']
            if 'theme' in incident_info and 'description' in incident_info:
                await message.answer('Обращение отправлено. 👌')
            else:
                await message.answer('Ошибка интеграции API.')
        else:
            await message.answer(text='Ошибка интеграции API.')
    elif from_command == 'smtp':
        text = 'Incident info:'
        if theme:
            text += theme
        if description:
            text += description
        if contact:
            text += contact
        if file:
            text += file
        try:
            server = smtplib.SMTP('localhost')

            # this methods depends by server settings
            # server.ehlo()
            # server.starttls()

            server.sendmail(from_addr=FROM_SMTP, to_addrs=TO_SMTP, msg=text)
            server.quit()
        except Exception as e:
            text = f'Ошибка интеграции SMTP.\n{e}'
            await message.answer(text=text)
