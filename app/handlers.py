from aiogram import F, Router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from parser import register
from app.db import *
from sender import fetch_result

import app.keyboards as kb

router = Router()

class Reg(StatesGroup):
    surname = State()
    name = State()
    patronymic = State()
    doc_type = State()
    document = State()
    region = State()

@router.message(CommandStart())
async def start(message: Message):
    await message.answer("Привет!\n"
                         "Этот бот оповещает о наличии новых результатов на сайте checkege.rustest.ru\n"
                         "Также ты можешь в любой момент проверить текущие результаты командой /check\n"
                         "Если ты ещё не зарегистрирован, то введи команду /reg")

@router.message(Command("reg"))
async def reg(message: Message, state: FSMContext):
    await state.set_state(Reg.surname)
    await message.answer("Давай зарегистрируем тебя!")
    await message.answer("Введи фамилию")

@router.message(Reg.surname)
async def set_surname(message: Message, state: FSMContext):
    if (await state.get_data()).get("surname"):
        await state.update_data(surname=message.text.strip())
        await get_result(message, state)
    else:
        await state.update_data(surname=message.text.strip())
        await state.set_state(Reg.name)
        await message.answer("Введи имя")

@router.message(Reg.name)
async def set_name(message: Message, state: FSMContext):
    if (await state.get_data()).get("name"):
        await state.update_data(name=message.text.strip())
        await get_result(message, state)
    else:
        await state.update_data(name=message.text.strip())
        await state.set_state(Reg.patronymic)
        await message.answer("Введи отчество")

@router.message(Reg.patronymic)
async def set_patronymic(message: Message, state: FSMContext):
    if (await state.get_data()).get("patronymic"):
        await state.update_data(patronymic=message.text.strip())
        await get_result(message, state)
    else:
        await state.update_data(patronymic=message.text.strip())
        await state.set_state(Reg.doc_type)
        await state.set_state(Reg.document)
        await message.answer("Выбери, что будешь вводить далее", reply_markup=kb.doc_choose)

@router.callback_query(F.data == "code")
async def code(call: CallbackQuery, state: FSMContext):
    await call.message.delete()
    await state.update_data(doc_type="code")
    await call.message.answer("Введи код регистрации (12 цифр без тире)")

@router.callback_query(F.data == "doc")
async def document(call: CallbackQuery, state: FSMContext):
    await call.message.delete()
    await state.update_data(doc_type="num")
    await call.message.answer("Введи номер документа (без серии)")

@router.message(Reg.document)
async def set_document(message: Message, state: FSMContext):

    if (await state.get_data()).get("doc_type"):
        if (await state.get_data()).get("document"):
            await state.update_data(document=message.text.strip())
            await get_result(message, state)
        else:
            await state.update_data(document=message.text.strip())
            await state.set_state(Reg.region)
            await message.answer("Введи номер региона")
    else:
        await state.set_state(Reg.doc_type)
        await state.set_state(Reg.document)
        await message.answer("Выбери, что будешь вводить далее", reply_markup=kb.doc_choose)

@router.message(Reg.region)
async def set_region(message: Message, state: FSMContext):
    await state.update_data(region=message.text.strip())
    await get_result(message, state)

@router.callback_query(F.data == "correct")
async def correct(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text("Одну минутку...")
    data = await state.get_data()
    cookie = await register(**data)

    if cookie != "":
        await call.message.delete()
        await call.message.answer(f"Ура! Теперь ты можешь получать информацию!\n"
                                  f"Если потребуется изменить какие-то данные, ты всегда можешь ещё раз написать /reg\n")
        await add_to_database(call.from_user.id, cookie, await fetch_result(cookie))
        await state.clear()
    else:
        await call.message.delete()
        await call.message.answer("Ошибка! Проверь введённые данные или повтори ещё раз")
        await get_result(call.message, state)

@router.callback_query(F.data == "incorrect")
async def incorrect(call: CallbackQuery):
    await call.message.edit_text("Что нужно изменить?", reply_markup=kb.changer)

@router.callback_query(F.data == "surname")
async def change_surname(call: CallbackQuery, state: FSMContext):
    await call.message.delete()
    await state.set_state(Reg.surname)
    await call.message.answer("Введи фамилию")

@router.callback_query(F.data == "name")
async def change_name(call: CallbackQuery, state: FSMContext):
    await call.message.delete()
    await state.set_state(Reg.name)
    await call.message.answer("Введи имя")

@router.callback_query(F.data == "patronymic")
async def change_patronymic(call: CallbackQuery, state: FSMContext):
    await call.message.delete()
    await state.set_state(Reg.patronymic)
    await call.message.answer("Введи отчество")

@router.callback_query(F.data == "document")
async def change_document(call: CallbackQuery, state: FSMContext):
    await call.message.delete()
    await state.set_state(Reg.doc_type)
    await state.set_state(Reg.document)
    await call.message.answer("Выбери, что будешь вводить далее (или сразу введи изменённое значение, если не хочешь менять тип данных)", reply_markup=kb.doc_choose)

@router.callback_query(F.data == "region")
async def change_region(call: CallbackQuery, state: FSMContext):
    await call.message.delete()
    await state.set_state(Reg.region)
    await call.message.answer("Введи номер региона")

@router.message(Command("check"))
async def check_result(message: Message):
    cookie = await get_cookie_from_database(message.from_user.id)
    if cookie:
        result = await fetch_result(cookie)
        await add_to_database(message.from_user.id, cookie, result)
        result_pretty = "<b>Вот твои текущие результаты:</b>\n<pre>Предмет                  Результат\n\n"
        for exam in result["Result"]["Exams"]:
            if exam["HasResult"]:
                subject = exam["Subject"]
                if subject == "Сочинение":
                    mark =  "зачёт" if exam["TestMark"] == 1 else "незачёт"
                else:
                    mark = str(exam["TestMark"])
                result_pretty += f"{subject.ljust(24)}{mark.rjust(10)}\n"
        result_pretty += "</pre>"
        await message.answer(result_pretty, parse_mode="HTML")
    else:
        await message.answer("Для получения результата нужно зарегистрироваться")

async def get_result(message: Message, state: FSMContext):
    data = await state.get_data()
    doc = "Код регистрации" if data['doc_type'] == "code" else "Номер документа"
    await message.answer("Давай сверимся\n"
                         f"Фамилия: {data['surname']}\n"
                         f"Имя: {data['name']}\n"
                         f"Отчество: {data['patronymic']}\n"
                         f"{doc}: {data['document']}\n"
                         f"Регион: {data['region']}", reply_markup=kb.checker)
