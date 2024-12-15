import asyncio
import random
import sqlite3
import logging
import requests
import sys
import os
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv

# Загрузка переменных из .env
load_dotenv()

# Получение API токенов
TOKEN = os.getenv("TELEGRAM_TOKEN")

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)
logger.info("Бот запущен.")

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

logging.basicConfig(level=logging.INFO)

# Кнопки меню
button_registr = KeyboardButton(text="Регистрация в телеграм боте")
button_exchange_rates = KeyboardButton(text="Курс валют")
button_tips = KeyboardButton(text="Советы по экономии")
button_finances = KeyboardButton(text="Личные финансы")
button_view_finances = KeyboardButton(text="Просмотр финансов")
button_edit_finances = KeyboardButton(text="Редактирование финансов")

keyboards = ReplyKeyboardMarkup(
    keyboard=[
        [button_registr, button_exchange_rates],
        [button_tips, button_finances],
        [button_view_finances, button_edit_finances]
    ],
    resize_keyboard=True
)

# Соединение с базой данных
conn = sqlite3.connect('user_fin.db')
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
   id INTEGER PRIMARY KEY,
   telegram_id INTEGER UNIQUE,
   name TEXT,
   age INTEGER,
   category1 TEXT,
   category2 TEXT,
   category3 TEXT,
   expenses1 REAL,
   expenses2 REAL,
   expenses3 REAL
)
''')

conn.commit()

# Состояния для машины состояний
class FinancesForm(StatesGroup):
    category1 = State()
    expenses1 = State()
    category2 = State()
    expenses2 = State()
    category3 = State()
    expenses3 = State()

class EditFinancesForm(StatesGroup):
    select_category = State()
    new_expense = State()

class RegistrationForm(StatesGroup):
    name = State()
    age = State()

# Обработчики команд и сообщений
@dp.message(Command('start'))
async def send_start(message: Message):
    await message.answer(
        f"*Приветствую, {message.from_user.first_name}!*\nЯ Ваш личный финансовый помощник. "
        f"Выбери одну из опций в меню:",
        reply_markup=keyboards, parse_mode="Markdown"
    )

@dp.message(F.text == "Регистрация в телеграм боте")
async def registration_start(message: Message, state: FSMContext):
    telegram_id = message.from_user.id
    cursor.execute('SELECT * FROM users WHERE telegram_id = ?', (telegram_id,))
    user = cursor.fetchone()
    if user:
        await message.answer("Вы уже зарегистрированы!")
    else:
        await state.set_state(RegistrationForm.name)
        await message.answer("Пожалуйста, введите своё имя:")

@dp.message(RegistrationForm.name)
async def registration_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(RegistrationForm.age)
    await message.answer("Введите свой возраст `(сколько Вам лет числом)`:",
                         parse_mode="Markdown")

@dp.message(RegistrationForm.age)
async def registration_age(message: Message, state: FSMContext):
    try:
        age = int(message.text)
        data = await state.get_data()
        name = data['name']
        telegram_id = message.from_user.id
        cursor.execute(
            'INSERT INTO users (telegram_id, name, age) VALUES (?, ?, ?)',
            (telegram_id, name, age)
        )
        conn.commit()
        await state.clear()
        await message.answer("Вы успешно зарегистрированы!")
    except ValueError:
        await message.answer("Пожалуйста, *введите корректно возраст (число)*",
                             parse_mode="Markdown")

@dp.message(F.text == "Курс валют")
async def exchange_rates(message: Message):
    url = "https://v6.exchangerate-api.com/v6/09edf8b2bb246e1f801cbfba/latest/USD"
    try:
        response = requests.get(url)
        data = response.json()
        if response.status_code != 200:
            await message.answer("`Не удалось получить данные о курсе валют!`",
                                 parse_mode="Markdown")
            return
        usd_to_rub = data['conversion_rates']['RUB']
        eur_to_usd = data['conversion_rates']['EUR']
        cny_to_usd = data['conversion_rates']['CNY']
        euro_to_rub = usd_to_rub/eur_to_usd
        cny_to_rub = usd_to_rub/cny_to_usd
        await message.answer(
            f"1 USD - *{usd_to_rub:.2f} RUB*\n"
            f"1 EUR - *{euro_to_rub:.2f} RUB*\n"
            f"1 CNY - *{cny_to_rub:.2f} RUB*",
        parse_mode="Markdown")
    except:
        await message.answer("`Произошла ошибка при получении курса валют`",
                             parse_mode="Markdown")

@dp.message(F.text == "Советы по экономии")
async def send_tips(message: Message):
    tips = [
        "`Совет 1:` **Составьте бюджет**: Начните с создания подробного бюджета, чтобы понять, куда уходят ваши деньги, и определить области для сокращения затрат.",
        "`Совет 2:` **Установите финансовые цели**: Определите краткосрочные и долгосрочные цели, такие как покупка дома или создание резервного фонда, которые будут мотивировать вас откладывать деньги.",
        "`Совет 3:` **Контролируйте расходы**: Регулярно отслеживайте свои траты с помощью приложений или таблиц, чтобы не выходить за рамки бюджета.",
        "`Совет 4:` **Сократите ненужные подписки**: Пересмотрите свои подписки и откажитесь от тех, которые вы не используете или которые можно заменить более дешевыми альтернативами.",
        "`Совет 5:` **Планируйте питание**: Готовьте дома и планируйте меню на неделю, чтобы сократить расходы на ресторан или заказ еды.",
        "`Совет 6:` **Покупайте по списку**: Всегда составляйте список покупок перед походом в магазин, чтобы избежать импульсивных покупок.",
        "`Совет 7:` **Используйте кэшбэк и скидки**: Воспользуйтесь программами кэшбэка и скидками на товары, чтобы сэкономить на повседневных покупках.",
        "`Совет 8:` **Сравнивайте цены**: Перед покупкой сравните цены в разных магазинах и онлайн-платформах, чтобы найти лучшие предложения.",
        "`Совет 9:` **Создайте резервный фонд**: Регулярно откладывайте деньги в резервный фонд на случай непредвиденных расходов.",
        "`Совет 10:` **Изучите основные навыки ремонта**: Это поможет сэкономить на вызове специалистов для мелкого ремонта в доме.",
        "`Совет 11:` **Покупайте подержанные вещи**: Рассмотрите возможность покупки б/у товаров, таких как мебель или электроника, которые могут быть значительно дешевле.",
        "`Совет 12:` **Автоматизируйте сбережения**: Настройте автоматический перевод части зарплаты на сберегательный счет, чтобы делать накопления без усилий."
    ]
    tip = random.choice(tips)
    await message.answer(tip, parse_mode="Markdown")

@dp.message(F.text == "Личные финансы")
async def finances(message: Message, state: FSMContext):
    await state.set_state(FinancesForm.category1)
    await message.reply("Введите *первую категорию* расходов:", parse_mode="Markdown")

@dp.message(FinancesForm.category1)
async def finances_category1(message: Message, state: FSMContext):
    await state.update_data(category1=message.text)
    await state.set_state(FinancesForm.expenses1)
    await message.reply("Введите расходы для *первой категории* (в рублях числом):", parse_mode="Markdown")

@dp.message(FinancesForm.expenses1)
async def finances_expenses1(message: Message, state: FSMContext):
    try:
        expenses1 = float(message.text)
        await state.update_data(expenses1=expenses1)
        await state.set_state(FinancesForm.category2)
        await message.reply("Введите вторую категорию расходов:", parse_mode="Markdown")
    except ValueError:
        await message.reply("Пожалуйста, введите *корректно* сумму расходов (число) "
                            "для *первой категории*.", parse_mode="Markdown")

@dp.message(FinancesForm.category2)
async def finances_category2(message: Message, state: FSMContext):
    await state.update_data(category2=message.text)
    await state.set_state(FinancesForm.expenses2)
    await message.reply("Введите расходы для *второй категории* (в рублях числом):", parse_mode="Markdown")

@dp.message(FinancesForm.expenses2)
async def finances_expenses2(message: Message, state: FSMContext):
    try:
        expenses2 = float(message.text)
        await state.update_data(expenses2=expenses2)
        await state.set_state(FinancesForm.category3)
        await message.reply("Введите *третью категорию* расходов:", parse_mode="Markdown")
    except ValueError:
        await message.reply("Пожалуйста, введите *корректно* сумму расходов "
                            "для *второй категории* (в рублях числом).", parse_mode="Markdown")

@dp.message(FinancesForm.category3)
async def finances_category3(message: Message, state: FSMContext):
    await state.update_data(category3=message.text)
    await state.set_state(FinancesForm.expenses3)
    await message.reply("Введите расходы для *третьей категории* (в рублях числом):", parse_mode="Markdown")

@dp.message(FinancesForm.expenses3)
async def finances_expenses3(message: Message, state: FSMContext):
    try:
        expenses3 = float(message.text)
        data = await state.get_data()
        telegram_id = message.from_user.id
        cursor.execute('''
            UPDATE users
            SET category1 = ?, expenses1 = ?, category2 = ?, expenses2 = ?, category3 = ?, expenses3 = ?
            WHERE telegram_id = ?
        ''', (
            data['category1'], data['expenses1'],
            data['category2'], data['expenses2'],
            data['category3'], expenses3,
            telegram_id
        ))
        conn.commit()
        await state.clear()
        await message.answer("Категории и расходы *сохранены*!", reply_markup=keyboards, parse_mode="Markdown")
    except ValueError:
        await message.reply("Пожалуйста, введите *корректно* сумму расходов (в рублях числом)"
                            " для *третьей категории*.", parse_mode="Markdown")

# Функция для просмотра финансов
@dp.message(F.text == "Просмотр финансов")
async def view_finances(message: Message):
    telegram_id = message.from_user.id
    cursor.execute('''
        SELECT category1, expenses1, category2, expenses2, category3, expenses3
        FROM users WHERE telegram_id = ?
    ''', (telegram_id,))
    user_finances = cursor.fetchone()
    if user_finances:
        category1, expenses1, category2, expenses2, category3, expenses3 = user_finances
        if category1 and expenses1 is not None:
            response = "`Ваши категории расходов:`\n"
            response += f"*{category1}*: {expenses1} руб.\n"
            response += f"*{category2}*: {expenses2} руб.\n"
            response += f"*{category3}*: {expenses3} руб."
            await message.answer(response, parse_mode="Markdown")
        else:
            await message.answer(
                "У Вас *не имеется* сохраненных финансовых данных. "
                "Пожалуйста, *введите их в разделе 'Личные финансы'*."
            , reply_markup=keyboards, parse_mode="Markdown")
    else:
        await message.answer("*Вы еще не зарегистрированы!* Пожалуйста, сначала зарегистрируйтесь.",
                              reply_markup=keyboards, parse_mode="Markdown")

# Функция для редактирования финансов
@dp.message(F.text == "Редактирование финансов")
async def edit_finances_start(message: Message, state: FSMContext):
    telegram_id = message.from_user.id
    cursor.execute('SELECT category1, category2, category3 FROM users WHERE telegram_id = ?', (telegram_id,))
    user_finances = cursor.fetchone()
    if user_finances:
        categories = [cat for cat in user_finances if cat]
        if categories:
            # Создаем кнопки для выбора категории
            buttons = [KeyboardButton(text=cat) for cat in categories]
            categories_keyboard = ReplyKeyboardMarkup(
                keyboard=[buttons],
                resize_keyboard=True
            )
            await state.set_state(EditFinancesForm.select_category)
            await message.answer(
                "*Выберите категорию*, которую хотите *изменить*:",
                reply_markup=categories_keyboard, parse_mode="Markdown"
            )
        else:
            await message.answer("У Вас *не имеется* сохраненных финансовых данных для редактирования.", reply_markup=keyboards,
                                 parse_mode="Markdown")
    else:
        await message.answer("*Вы еще не зарегистрированы!* Пожалуйста, сначала зарегистрируйтесь.", reply_markup=keyboards,
                             parse_mode="Markdown")

@dp.message(EditFinancesForm.select_category)
async def edit_finances_select_category(message: Message, state: FSMContext):
    selected_category = message.text
    await state.update_data(selected_category=selected_category)
    # Добавляем кнопку "Отмена"
    cancel_button = KeyboardButton(text="Отмена")
    cancel_keyboard = ReplyKeyboardMarkup(
        keyboard=[[cancel_button]],
        resize_keyboard=True
    )
    await state.set_state(EditFinancesForm.new_expense)
    await message.answer(
        f"Введите *новую сумму расходов* (в рублях числом) для категории `'{selected_category}'`:",
        reply_markup=cancel_keyboard, parse_mode="Markdown"
    )

@dp.message(EditFinancesForm.new_expense)
async def edit_finances_new_expense(message: Message, state: FSMContext):
    if message.text.lower() == "отмена":
        await state.clear()
        await message.answer("Редактирование *отменено*.", reply_markup=keyboards,
                             parse_mode="Markdown")
        return
    try:
        new_expense = float(message.text)
        data = await state.get_data()
        selected_category = data['selected_category']
        telegram_id = message.from_user.id
        # Обновляем нужное поле в базе данных
        cursor.execute('SELECT category1, category2, category3 FROM users WHERE telegram_id = ?', (telegram_id,))
        categories = cursor.fetchone()
        if selected_category == categories[0]:
            cursor.execute('UPDATE users SET expenses1 = ? WHERE telegram_id = ?', (new_expense, telegram_id))
        elif selected_category == categories[1]:
            cursor.execute('UPDATE users SET expenses2 = ? WHERE telegram_id = ?', (new_expense, telegram_id))
        elif selected_category == categories[2]:
            cursor.execute('UPDATE users SET expenses3 = ? WHERE telegram_id = ?', (new_expense, telegram_id))
        else:
            await message.answer("*Категория не найдена*.", reply_markup=keyboards,  parse_mode="Markdown")
            await state.clear()
            return
        conn.commit()
        await state.clear()
        await message.answer(
            f"Расходы для категории `'{selected_category}'` *обновлены на {new_expense} руб.*",
            reply_markup=keyboards, parse_mode="Markdown"
        )
    except ValueError:
        await message.reply("Пожалуйста, введите *корректно* сумму расходов (в рублях числом).",
                            parse_mode="Markdown")

# Запуск бота
async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    if sys.platform.startswith('win'):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())