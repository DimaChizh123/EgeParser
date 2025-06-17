from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

doc_choose = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Код регистрации", callback_data="code"),
     InlineKeyboardButton(text="Номер документа", callback_data="doc")]
])

checker = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Всё верно", callback_data="correct"),
     InlineKeyboardButton(text="Изменить", callback_data="incorrect")]
])

changer = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Фамилия", callback_data="surname"), InlineKeyboardButton(text="Имя", callback_data="name"), InlineKeyboardButton(text="Отчество", callback_data="patronymic")],
    [InlineKeyboardButton(text="Документ", callback_data="document"), InlineKeyboardButton(text="Регион", callback_data="region")]
])