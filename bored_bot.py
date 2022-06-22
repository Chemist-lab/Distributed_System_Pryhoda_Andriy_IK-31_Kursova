import logging # Імпорт бібліотеки для логування

import sqlite3 # Імпорт бібліотеки для роботи з базами даних

import html2text # Імпорт бібліотеки для перетворення html сторінки в текст

import requests # Імпорт бібліотеки для створення різного типу запитів

import string # Імпорт бібліотеки для роботи з рядками

# Імпорт бібліотек aiogram для роботи з Telegram Api
from aiogram import Bot, Dispatcher, executor, types
from aiogram.utils.exceptions import BotBlocked
from aiogram.dispatcher.filters import Text
from aiogram.utils import executor
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.types import BotCommand


con = sqlite3.connect('users.db') # під'єднуємося до бази даних
cur = con.cursor() # Створюємо курсор

# Настроюємо логування
logging.basicConfig(level=logging.INFO)
logging.basicConfig(level=logging.Handler)

# Оголошення змінної API_TOKEN і присвоєння їй значення ключа з бота телеграм
API_TOKEN = '' #Сюди потрібно вставити токен до бота.

# Ініціалізація бота
bot = Bot(token=API_TOKEN)

# Ініціалізація змінної для зберігання станів у пам'яті
storage = MemoryStorage()

# Ініціалізація диспетчера
dp = Dispatcher(bot, storage=storage)


# Функція "set_commands" створена для добавлення команд у меню швидкого вибору телеграм;
# Параметру "command" ми присвоюємо команду для швикого виклику, параметру "description" - короткий опис роботи команди
async def set_commands(bot: Bot):
    commands = [
        BotCommand(command="/start", description="Start or reload bot"),
        BotCommand(command="/lib", description="Open saved content library"),
        BotCommand(command="/gheavymetal", description="Our AI will write the lyrics of a heavy metal song"),
        BotCommand(command="/gavmontage", description="Create a video montage using footage from popular films:"),
        BotCommand(command="/gaiart", description="The paintings it makes do not already exist, they are computer generated art."),
        BotCommand(command="/ganimestory", description="Our AI thinks up anime story ideas and draws new waifu characters."),
        BotCommand(command="/neustyletransfer", description="Our AI was trained to create art using neural style transfer."),
        BotCommand(command="/sref", description="AI-Powered Photo Search Engine"),
        BotCommand(command="/photobl", description="Two beautiful photos blended together into a work of art, automatically created by computer"),
        BotCommand(command="/gslogan", description="Generate simple slogans with AI"),
        BotCommand(command="/gaipizza", description="Generate pizza with AI")
    ]
    await bot.set_my_commands(commands)


# Створюємо клас зі станами для поетапного виконнаня команди "/gslogan"
class GenerateSloganStates(StatesGroup):
    comp_name = State() # Змінній присвоєно стан, який буде викликатися після виклику команди "/gslogan" і буде очікувати ввід назви компанії(чи подібних організацій)
    comp_descr = State()# Змінній присвоєно стан, який буде викликатися після виконання попереднього стану "comp_name" і буде очікувати ввід короткого опису компанії(чи подібних організацій)

# Створюємо клас зі станами для поетапного виконнаня команди "/sref"
class SearchReferendeStates(StatesGroup):
    key_words = State() # Змінній присвоєно стан, який буде викликатися після виклику команди "/sref" і буде очікувати ввід ключового слова, чи слів для пошуку по фото

# Створюємо клас зі станами для навігацію по бібліотеці збережених речей користувача
class UserSavedLibraryManagerStates(StatesGroup):
    main_menu = State() # Стан головного меню
    Show_one = State()  # Стан для показу одного вибраного елементу з бібліотеки
    clear_one = State() # Стан для очищення одного вибраного елементу з бібліотеки

# Створюємо клас зі станами для навігацію по бібліотеці збережених речей користувача
class MovieMontageCreatorStates(StatesGroup):
    search_words = State() # Стан для очікуваання слів для пошуку моменту у фільмі


# Декоратор для обробника буде викликано, якщо повідомлення починається з команди "/start" і він запустить функцію "cmd_start"
@dp.message_handler(commands="start")
async def cmd_start(message: types.Message):  
    markup = types.ReplyKeyboardRemove() # Створення змінної, якій присвоюємо видалення всіх попережніх клавіатур
    await set_commands(bot)              # Очікування виконання функції "set_commands", яка створить швидке меню команд
    await message.reply("Sup!", reply_markup=markup) # Відповідь на команду старт

# Декоратор для обробника команди "/lib", який викликає функцію "openLibrary"
@dp.message_handler(commands="lib")
async def openLibrary(message: types.Message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)  # Створення клавіатури для навігації в меню
    buttons_menu = ['Show selected item', 'Show all items',     # Створення масиву кнопок для клавіатури
                    'Library load', 'Delete selected item', 
                    'Canсel'] 
    keyboard.add(*buttons_menu)                                 # Присвоєння клавіатурі кнопок
    await UserSavedLibraryManagerStates.main_menu.set()         # Запуск стану головного меню
    await message.reply('Select option', reply_markup=keyboard) # Відповідь на команду "/lib" і показ клавіатури


# Декоратор для обробника стану головного меню(UserSavedLibraryManagerStates.main_menu) і запуск фукції "openLibrary_mainMenu", яка приймає параметри "message" та "state"
@dp.message_handler(state=UserSavedLibraryManagerStates.main_menu)
async def openLibrary_mainMenu(message: types.Message, state: FSMContext):
    buttons_menu = ['Show selected item', 'Show all items',     # Створення масиву кнопок
                    'Library load', 'Delete selected item',
                    'Canсel']

    # Перевіряється, яка кнопка була вибрана
    if message.text == buttons_menu[0]:  # Кнопка 'Show selected item'
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)  # Створення клавіатури
        btns = []                                                   # Створення пустого масиву кнопок для подпльшого його заповнення
        cur.execute("SELECT saved_message_id, library_slot FROM global_user_data WHERE user_id = ? ORDER BY library_slot", (message.chat.id,)) # Запит в базу даних за всіма 
        _data = cur.fetchall() # Збір всіх даних в список                                                                                        елементами корстувача і сортування за їх порядковим номером    

        # Якщо даних немає, то видаляється клавіатура та виводиться повідомлення для корисутвача, що його бібліотека пуста та завершується машина станів                 
        if len(_data)==0:                        
            markup = types.ReplyKeyboardRemove()
            await state.finish()            
            await message.reply('You library is empty!', reply_markup=markup)
        # Якщо збережені дані користувача є:
        else:
            for row in _data:             # Запуск циклу, в якому заповнюється масив кнопок клавіатури взятих з базхи даних
                btns.append(str(row[1]))
            keyboard.add(*btns)           # Присвоєння клавіатурі кнопок з масиву
            await UserSavedLibraryManagerStates.Show_one.set() # Запуск стану, який буде очікувати вибір елементу з бібліотеки    
            await message.reply('Select item to show', reply_markup=keyboard) # Відповідь на повідомлення та показ клавіатури з можливітю вибрати збережений елемент

    if message.text == buttons_menu[1]:  # Кнопка 'Show all item'
        await state.finish() # Завершення стану

        await message.reply('Showing all items') # Відповідь на повідомлення з оповіщенням про показ всіх елементів

        user_id = message.chat.id  # Змінна, яка тримає в собі id кориснувача
    
        cur.execute("SELECT saved_message_id, library_slot FROM global_user_data WHERE user_id = ? ORDER BY library_slot", (user_id,)) # Запит в базу даних за всіма 
        _data = cur.fetchall() # Збір всіх даних з бази даних                                                                            елементами корстувача і сортування за їх порядковим номером 

        # Якщо даних немає, то видаляється клавіатура та виводиться повідомлення для корисутвача, що його бібліотека пуста та видаляється клавіатура швидких відповідей
        if len(_data)==0:
            markup = types.ReplyKeyboardRemove()
            await message.reply('You library is empty!', reply_markup=markup)
    
        # Якщо збережені дані користувача є:
        else:
            markup = types.ReplyKeyboardRemove() # Змінна видалення клавіатури
            for row in _data: # Запуск циклу для перебору всіх вираних рядків
                await bot.send_message(message.chat.id, f'***************\nLibrary slot - {row[1]}', reply_markup=markup) # Відсилання повідомлення для розмітки та нумерації
                await bot.copy_message(message.chat.id, message.chat.id, row[0]) # Копіювання повідомлення за допомогою збереженого в базі даних message_id
            return 

    if message.text == buttons_menu[2]: # Кнопка 'Library load'
        await state.finish() # Завершення стану

        user_id = message.chat.id  # Змінна, яка тримає в собі id кориснувача

        cur.execute("SELECT library_slot FROM global_user_data WHERE user_id = ? ORDER BY library_slot", (message.chat.id,)) # Запит в базу даних за всіма 
        _data = cur.fetchall() # Збір всіх даних з бази даних                                                                  елементами корстувача і сортування за їх порядковим номером 

        empty_emo = '✅' # Змінна, яка тримає в собі емоджі вільного слота
        load_emo = '✖️'  # Змінна, яка тримає в собі емоджі заповненого слота
        items_state = [empty_emo, empty_emo, empty_emo, empty_emo, empty_emo, # Масив елементів бібліотеки, які по замовчуванні пусті
                       empty_emo, empty_emo, empty_emo, empty_emo, empty_emo, 
                       empty_emo, empty_emo, empty_emo, empty_emo, empty_emo, 
                       empty_emo, empty_emo, empty_emo, empty_emo, empty_emo]
        
        items = list(range(1, 21))      # Масив стану елементів бібліотеки, які по замовчуванні пусті
        for i in range(0, len(items_state)): # Перебирання кожного елементу відображення слота в бібліотеці
            for row in _data:                # Перебирання кожного елементу бібліотеки в базі даних
                if row[0] == items[i]:       # Якщо стан відмінний від стандартного стану, то відображається емоджі заповненого слота
                    items_state[i] = load_emo

        markup = types.ReplyKeyboardRemove() # Змінна видалення клавіатури

        # Відповідь на повідомлення та відображеня всіх слотів 
        await message.reply(f'Library: \nFree slot - {empty_emo}\nFull slot - {load_emo}\n\n'+
                            f'{items_state[0]}  {items_state[1]}  {items_state[2]}  {items_state[3]}  {items_state[4]}\n'+
                            f'{items_state[5]}  {items_state[6]}  {items_state[7]}  {items_state[8]}  {items_state[9]}\n'+
                            f'{items_state[10]}  {items_state[11]}  {items_state[12]}  {items_state[13]}  {items_state[14]}\n'+
                            f'{items_state[15]}  {items_state[16]}  {items_state[17]}  {items_state[16]}  {items_state[19]}\n',
                            reply_markup=markup)
      
    if message.text == buttons_menu[3]: # Кнопка 'Delete selected item'
      await UserSavedLibraryManagerStates.clear_one.set() # Запуск стану, який буде очікувати вибір елементу з бібліотеки для подальшого видалення
      keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)    # Створення клавіатури
      btns = [] # Створення пустого масиву кнопок для подпльшого його заповнення

      cur.execute("SELECT saved_message_id, library_slot FROM global_user_data WHERE user_id = ? ORDER BY library_slot", (message.chat.id,))# Запит в базу даних за всіма 
      _data = cur.fetchall() # Збір всіх даних з бази даних                                                                                   елементами корстувача і сортування за їх порядковим номером 

      for row in _data: # Запуск циклу, в якому заповнюється масив кнопок клавіатури взятих з базхи даних
          btns.append(str(row[1])) 
      keyboard.add(*btns) # Присвоєння клавіатурі кнопок з масиву

      await message.reply('Select item to delete', reply_markup=keyboard) # Відповідь на повідомлення та показ клавіатури з можливітю вибрати та видалити збережений елемент

    if message.text == buttons_menu[4]: # Кнопка 'Canсel'
        await state.finish() # Завершення стану
        markup = types.ReplyKeyboardRemove() # Змінна, якій присвоюється видалення клавіатури
        await message.reply('Canceled', reply_markup=markup) # Відповідь на повідомлення з підтвердженням відміни та видаленням клавіатури швидких відповідей

# Декоратор для обробника стану для можливості перегляду збережених елементів в базі даних(UserSavedLibraryManagerStates.Show_one) і запуск фукції "show_in_lib_one", яка приймає параметри "message" та "state"
@dp.message_handler(state=UserSavedLibraryManagerStates.Show_one)
async def show_in_lib_one(message: types.Message, state: FSMContext):
    await state.finish()            # Завершення стану

    user_id = message.chat.id       # Змінна, яка тримає в собі id кориснувача
    library_slot = message.text     # Змінна, яка тримає в собі вибраний порядковий номер елемента в бази даних

    cur.execute('SELECT saved_message_id FROM global_user_data WHERE user_id = ? AND library_slot = ?', (user_id, library_slot)) # Пошук id повідомлення в базі даних за допомогою id корстувача та порядковим номером в бібліотеці
    _data=cur.fetchall() # Збір всіх даних з бази даних
    markup = types.ReplyKeyboardRemove() # Змінна, якій присвоюється видалення клавіатури
    await message.reply(f'Showing {library_slot} item', reply_markup=markup) # Відповідь на повідомлення 
    for row in _data:
            await bot.copy_message(message.chat.id, message.chat.id, row[0]) # Показ збереженого елементу
    await message.reply(f'Done', reply_markup=markup) # Видалення клавіатури

# Декоратор для обробника стану для можливості видалення збереженого елементту з бази даних(UserSavedLibraryManagerStates.clear_one) і запуск фукції "delete_from_lib_one", яка приймає параметри "message" та "state"
@dp.message_handler(state=UserSavedLibraryManagerStates.clear_one)
async def delete_from_lib_one(message: types.Message, state: FSMContext):
    await state.finish()            # Завершення стану

    user_id = message.chat.id       # Змінна, яка тримає в собі id кориснувача
    library_slot = message.text     # Змінна, яка тримає в собі вибраний порядковий номер елемента в бази даних

    cur.execute('DELETE FROM global_user_data WHERE library_slot=? AND user_id=?', (library_slot, user_id,)) # Видалення елемента з бази даних за допомогою id корстувача та порядковим номером в бібліотеці
    con.commit() # Комміт всіх дій до бази даних
    markup = types.ReplyKeyboardRemove()    # Змінна, якій присвоюється видалення клавіатури
    await message.reply(f'Slot {library_slot} deleted', reply_markup=markup) # Відповідь на повідомлення з підтвердженням видалення та видаленням клавіатури швидких відповідей


# Декоратор для обробника запитів зворотного виклику "save_to_lib", який викликає функцію "save_to_lib"
@dp.callback_query_handler(text="save_to_lib")
async def save_to_lib(call: types.CallbackQuery):
    cur.execute("SELECT library_slot FROM global_user_data WHERE user_id = ? ORDER BY library_slot", (call.message.chat.id,)) # Запит в базу даних за всіма 
    _data = cur.fetchall() # Збір всіх даних з бази даних                                                                       елементами користувача і сортування за їх порядковим номером

    max = 0 # Змінна, якій присвоюється максимальне значення заповненості бібліотеки користувача
    slots = list(range(1, 21)) # Створення масиву зі значеннями 1-20

    # Перебір елементів масиву: 
    #  - Якщо серед елементів бібілотеки (1-20) є вільні слоти - то max = першому вільному слоту
    #  - Якщо серед елементів бібілотеки (1-20) є заповнені по порядку і є вільні слоти - то max = максимальному номеру слота
    for row in range(0, len(_data)): 
        if (_data[row])[0] != slots[row]:
            max = (_data[row])[0]-2
            break
        if (_data[row])[0] >= max:
            max = (_data[row])[0]

    # Якщо max рівний 20 - виводиться повідомлення, що бібліотека заповнена
    if max >= 20:
        await bot.send_message(call.message.chat.id, "Your library is full")
        await call.answer(text="Your library is full", show_alert=True) # Сповіщення користувача про те, що бібліотека заповнена
    else: 
        new_max = max # Створюється змінна, якій присвоюється поточне максимальне значення і подальше добавляється +1, якщо new_max != 20
        if new_max != 20:
            new_max = new_max + 1

        cur.execute("SELECT user_id, library_slot FROM global_user_data WHERE user_id=? AND saved_message_id=?", (call.message.chat.id, call.message.message_id,)) # Запит в базу даних за всіма елементами корстувача
        data=cur.fetchall() # Збір всіх даних з бази даних

        if len(data)==0: # Якщо унікального id не найдено - зберігаємо в базу даних і виводимо повідомлення
            cur.execute(f"INSERT INTO global_user_data VALUES ({call.message.chat.id}, {call.message.message_id}, {new_max})")
            con.commit()
            await bot.send_message(call.message.chat.id, f"Message saved to library under slot - {new_max}")
            await call.answer(text=f"Message saved to library under slot - {new_max}", show_alert=True) # Сповіщення користувача про те, що повідомлення збережено
        else: # Якщо знайдено унікальний id - виводимо повідомлення, що такий елемент уже є
            await bot.send_message(call.message.chat.id, "This data already in library")
            await call.answer(text="This data already in library", show_alert=True) # Сповіщення користувача про те, що повідомлення вже в бібліотеці


# Декоратор для обробника команди "/gheavymetal", який викликає функцію "Generate_Heavy_Metal_Lyrics"
@dp.message_handler(commands="gheavymetal")
async def Generate_Heavy_Metal_Lyrics(message: types.Message):
    r = requests.post('https://boredhumans.com/api_metal_lyrics.php') # Створення пост-запиту на сервер сайту "boredhumans.com"
    text = html2text.html2text(r.text) # Конвертування відповіді пост-запиту в текст за допомогою модуля "html2text"
    keyboard = types.InlineKeyboardMarkup() # Створення змінної, якій присвоюється інлайн клавіатура
    keyboard.add(types.InlineKeyboardButton(text="Save to library", callback_data="save_to_lib")) # Добавлення кнопки "Save to library" до інлайн клавіатури
    await message.reply(text, reply_markup=keyboard) # Відповідь на повідомлення та показ інлайн клавіатури


# Декоратор для обробника команди "/gaiart", який викликає функцію "Generate_art"
@dp.message_handler(commands="gaiart")
async def Generate_art(message: types.Message):
    r = requests.post('https://boredhumans.com/api_art.php') # Створення пост-запиту на сервер сайту "boredhumans.com"
    text = html2text.html2text(r.text) # Конвертування відповіді пост-запиту в текст за допомогою модуля "html2text"
    url = text[text.find('htt'):text.find(')')] # Пошук  посилання на картинку
    keyboard = types.InlineKeyboardMarkup() # Створення змінної, якій присвоюється інлайн клавіатура
    keyboard.add(types.InlineKeyboardButton(text="Save to library", callback_data="save_to_lib")) # Добавлення кнопки "Save to library" до інлайн клавіатури
    await message.reply_photo(url, reply_markup=keyboard) # Відповідь на повідомлення та показ інлайн клавіатури


# Декоратор для обробника команди "/photobl", який викликає функцію "ai_photoblend"
@dp.message_handler(commands="photobl")
async def Ai_photoblend(message: types.Message):
    r = requests.post('https://boredhumans.com/api_photo_blender.php') # Створення пост-запиту на сервер сайту "boredhumans.com"
    text = html2text.html2text(r.text) # Конвертування відповіді пост-запиту в текст за допомогою модуля "html2text"
    photo_url = text[text.find('htt'):text.find(')')] # Пошук  посилання на картинку
    
    keyboard = types.InlineKeyboardMarkup() # Створення змінної, якій присвоюється інлайн клавіатура 
    keyboard.add(types.InlineKeyboardButton(text="Save to library", callback_data="save_to_lib")) # Добавлення кнопки "Save to library" до інлайн клавіатури
    await message.reply_photo(photo_url, reply_markup=keyboard) # Відповідь на повідомлення та показ інлайн клавіатури


# Декоратор для обробника команди "/neustyletransfer", який викликає функцію "ai_neustyletransfer"
@dp.message_handler(commands="neustyletransfer")
async def Ai_neustyletransfer(message: types.Message):
    r = requests.post('https://boredhumans.com/api_neural_style_transfer.php') # Створення пост-запиту на сервер сайту "boredhumans.com"
    text = html2text.html2text(r.text) # Конвертування відповіді пост-запиту в текст за допомогою модуля "html2text"
    photo_url = text[text.find('htt'):text.find(')')] # Пошук посилання на картинку

    keyboard = types.InlineKeyboardMarkup() # Створення змінної, якій присвоюється інлайн клавіатура 
    keyboard.add(types.InlineKeyboardButton(text="Save to library", callback_data="save_to_lib")) # Добавлення кнопки "Save to library" до інлайн клавіатури
    await message.reply_photo(photo_url, reply_markup=keyboard) # Відповідь на повідомлення та показ інлайн клавіатури


# Декоратор для обробника команди "/sref", який викликає функцію "ai_photo_search_start"
@dp.message_handler(commands="sref")
async def Ai_photo_search_start(message: types.Message):
    await SearchReferendeStates.key_words.set() # Запуск стану, який буде очікувати введення ключового слова, або слів для пошуку
    await message.reply("Enter keywords") # Відповідь на повідомлення з описом потрібних дій

# Декоратор для обробника стану для можливості пошуку зображень(SearchReferendeStates.key_words) і запуск фукції "ai_photo_search", яка приймає параметри "message" та "state"
@dp.message_handler(state=SearchReferendeStates.key_words)
async def ai_photo_search(message: types.Message, state: FSMContext):
    await state.finish() # Завершення стану

    _data = {'question': message.text} # Створення тіла для пост-запиту
    r = requests.post('https://boredhumans.com/api_media_search.php', _data) # Створення пост-запиту на сервер сайту "boredhumans.com"
    text = html2text.html2text(r.text) # Конвертування відповіді пост-запиту в текст за допомогою модуля "html2text"
    new_text = text.translate({ord(c): None for c in string.whitespace}) # Видалення всіх пробілів

    # Створення масиву посиланнь і почергова спроба відсилати зрображення
    li = list(new_text.split(")](")) 
    li = li[1:]
    msg = ''

    for i in range(2, 20):
        li[i] = li[i][45:109]
        msg = msg+li[i]+"\n"

    for i in range(3, 13):
        try:
            keyboard = types.InlineKeyboardMarkup() # Створення змінної, якій присвоюється інлайн клавіатура 
            keyboard.add(types.InlineKeyboardButton(text="Save to library", callback_data="save_to_lib")) # Добавлення кнопки "Save to library" до інлайн клавіатури
            await bot.send_photo(message.chat.id, li[i], reply_markup=keyboard) # Відповідь на повідомлення та показ інлайн клавіатури
        except:
            continue

# Декоратор для обробника команди "/gslogan", який викликає функцію "ai_slogan"
@dp.message_handler(commands="gslogan")
async def Ai_slogan(message: types.Message):
    await GenerateSloganStates.comp_name.set() # Запуск стану, який буде очікува введення назву компанії
    await message.reply("Enter Your Company/Brand/Product Name") # Відповідь на повідомлення з вказівкою, що потрібно воодити
    
# Декоратор для обробника стану для отримання назви компанії(GenerateSloganStates.comp_name) і запуск фукції "ai_slogan_name", яка приймає параметри "message" та "state"
@dp.message_handler(state=GenerateSloganStates.comp_name)
async def Ai_slogan_name(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['comp_name'] = message.text.replace(" ", "") # Запис даних в тимчасову проксі-змінну з тексту повідомлення та видалення пробілів

    await GenerateSloganStates.next()    # Перехід на наступний стан
    await message.reply("Describe It (in a few words)") # Відповідь на повідомлення з вказівкою, що потрібно воодити

# Декоратор для обробника стану для отримання назви компанії(GenerateSloganStates.comp_descr) і запуск фукції "ai_slogan_descr", яка приймає параметри "message" та "state"
@dp.message_handler(state=GenerateSloganStates.comp_descr)
async def Ai_slogan_descr(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['comp_descr'] = message.text.replace(" ", "") # Запис даних в тимчасову проксі-змінну з тексту повідомлення та видалення пробілів
    await state.finish() # Завершення стану

    _data = {'x1': data['comp_name'], 'x2': data['comp_descr']} # Створення тіла для пост-запиту
    r = requests.post('https://boredhumans.com/api_slogans.php', _data) # Створення пост-запиту на сервер сайту "boredhumans.com"
    text = html2text.html2text(r.text) # Конвертування відповіді пост-запиту в текст за допомогою модуля "html2text"
    keyboard = types.InlineKeyboardMarkup() # Створення змінної, якій присвоюється інлайн клавіатура 
    keyboard.add(types.InlineKeyboardButton(text="Save to library", callback_data="save_to_lib")) # Добавлення кнопки "Save to library" до інлайн клавіатури
    await message.reply(f"{text}", reply_markup=keyboard) # Відповідь на повідомлення та показ інлайн клавіатури


# Декоратор для обробника команди "/ganimestory", який викликає функцію "generate_animne_story"
@dp.message_handler(commands="ganimestory")
async def generate_animne_story(message: types.Message):
    r = requests.get('https://boredhumans.com/anime_stories.php') # Створення пост-запиту на сервер сайту "boredhumans.com"
    text = html2text.html2text(r.text) # Конвертування відповіді пост-запиту в текст за допомогою модуля "html2text"
    main = text[text.find('![anime photos]'):text.find('Note: All computer generated anime images courtesy of')]
    photo_url = main[main.find('htt'):main.find(')')] # Пошук посилання на картинку
    story = main[main.find('\n'):main.find('...')] # Пошук тексту історії

    keyboard = types.InlineKeyboardMarkup() # Створення змінної, якій присвоюється інлайн клавіатура 
    keyboard.add(types.InlineKeyboardButton(text="Save to library", callback_data="save_to_lib")) # Добавлення кнопки "Save to library" до інлайн клавіатури
    await message.reply_photo(photo_url, story, reply_markup=keyboard) # Відповідь на повідомлення та показ інлайн клавіатури


# Декоратор для обробника команди "/gaipizza", який викликає функцію "generate_pizza"
@dp.message_handler(commands="gaipizza")
async def generate_pizza(message: types.Message):
    r = requests.get('https://boredhumans.com/api_food2.php') # Створення пост-запиту на сервер сайту "boredhumans.com"
    text = html2text.html2text(r.text) # Конвертування відповіді пост-запиту в текст за допомогою модуля "html2text"
    photo_url = text[text.find('https:'):text.find(')')] # Пошук посилання на картинку

    keyboard = types.InlineKeyboardMarkup() # Створення змінної, якій присвоюється інлайн клавіатура 
    keyboard.add(types.InlineKeyboardButton(text="Save to library", callback_data="save_to_lib")) # Добавлення кнопки "Save to library" до інлайн клавіатури
    await message.reply_photo(photo_url, reply_markup=keyboard) # Відповідь на повідомлення та показ інлайн клавіатури


# Декоратор для обробника команди "/gavmontage", який викликає функцію "movie_montage_command"
@dp.message_handler(commands="gavmontage")
async def movie_montage_command(message: types.Message):
    await MovieMontageCreatorStates.search_words.set() # Перехід на стан "MovieMontageCreatorStates.search_words"
    markup = types.ReplyKeyboardRemove() # Змінна, якій присвоюється видалення клавіатури
    await message.reply('Enter a keyword or phrase below to instantly create a video montage using footage from popular films:', reply_markup=markup) # Відповідь на повідомлення з описом потрібних наступних дій та видаленням клавіатури швидких відповідей
    
# Декоратор для обробника стану для отримання ключових слів для пошуку моменту у фільмах(MovieMontageCreatorStates.search_words) і запуск фукції "movie_montage_search", яка приймає параметри "message" та "state"
@dp.message_handler(state=MovieMontageCreatorStates.search_words)
async def movie_montage_search(message: types.Message, state: FSMContext):
    await state.finish() # Завершення стану

    words = message.text # Змінна, якій присвоюється значення тексту введеного користувачем

    _data = {'words': words} # Створення тіла для пост-запиту
    r = requests.post('https://boredhumans.com/api_video_montages.php', data=_data)  # Створення пост-запиту на сервер сайту "boredhumans.com"
    text = html2text.html2text(r.text) # Конвертування відповіді пост-запиту в текст за допомогою модуля "html2text"

    # Перевірка на коректну відповідь, якщо сервер присалав відповідь про помилку - сповіщаємо про це користувача
    if 'error' in text: 
        await message.answer('Ohh.. Sorry. Some error on server or service temporary not working :(')
    
    # Якщо сервер прислав коректну відповідь:
    else:
        texarr = text.split('},{') # Розбиваємо рядок з посиланнями на масив
        movie = texarr[0]
        vid_url = movie[text.find('"https:'):text.find('"}')] # Шукаємо посилання
        vid_url = vid_url.replace(";", '').replace('"', '') # Видаляємо символ ';'
        if vid_url.startswith('ht') == False: # Якщо випадково видалився перший символ посилання - добавляємо його
            vid_url = 'ht'+vid_url
        keyboard = types.InlineKeyboardMarkup() # Створення змінної, якій присвоюється інлайн клавіатура 
        keyboard.add(types.InlineKeyboardButton(text="Save to library", callback_data="save_to_lib")) # Добавлення кнопки "Save to library" до інлайн клавіатури
        await message.answer(vid_url, reply_markup=keyboard) # Відповідь на повідомлення та показ інлайн клавіатури
        

# Декоратори для обробників команди "/cancel" та слова "cancel" на будь-якому стані який викликає функцію "cancel_handler" і завершує поточний стан
@dp.message_handler(state='*', commands='cancel')
@dp.message_handler(Text(equals='cancel', ignore_case=True), state='*')
async def cancel_handler(message: types.Message, state: FSMContext):
    current_state = await state.get_state() # Отримуєтся поточний стан
    if current_state is None: # Якщо не знайдено ніякого стану - функція завершується
        return

    logging.info('Cancelling state %r', current_state) # Логування про завершення стану
    await state.finish() # Завершення стану
    await message.reply('Cancelled.', reply_markup=types.ReplyKeyboardRemove()) # Відповідь на питання та видалення клавіатури

# Декоратори для обробника помилки "BotBlocked", якщо бота заблокував користувач
@dp.errors_handler(exception=BotBlocked)
async def error_bot_blocked(update: types.Update, exception: BotBlocked):
    print(f"I was blocked by user!\Message: {update}\Error: {exception}")
    return True

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)