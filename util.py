from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Message, \
    BotCommand, MenuButtonCommands, BotCommandScopeChat, MenuButtonDefault
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

# конвертує об'єкт user в рядок
def dialog_user_info_to_str(user_data) -> str:
    mapper = {'language_from': 'Мова оригіналу', 'language_to': 'Мова перекладу',
              'text_to_translate': 'Текст для перекладу'}
    return '\n'.join(map(lambda k, v: (mapper[k], v), user_data.items()))

# надсилає в чат текстове повідомлення
async def send_text(update: Update, context: ContextTypes.DEFAULT_TYPE,
                    text: str) -> Message:
    if text.count('_') % 2 != 0:
        message = f"Рядок '{text}' є невалідним з точки зору markdown. Скористайтеся методом send_html()"
        print(message)
        return await update.message.reply_text(message)

    text = text.encode('utf16', errors='surrogatepass').decode('utf16')
    return await context.bot.send_message(chat_id=update.effective_chat.id,
                                          text=text,
                                          parse_mode=ParseMode.MARKDOWN)

# надсилає в чат html повідомлення
async def send_html(update: Update, context: ContextTypes.DEFAULT_TYPE,
                    text: str) -> Message:
    text = text.encode('utf16', errors='surrogatepass').decode('utf16')
    return await context.bot.send_message(chat_id=update.effective_chat.id,
                                          text=text, parse_mode=ParseMode.HTML)

# надсилає в чат текстове повідомлення, та додає до нього кнопки
async def send_text_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE,
                            text: str, buttons: dict) -> Message:
    text = text.encode('utf16', errors='surrogatepass').decode('utf16')
    keyboard = []
    for key, value in buttons.items():
        button = InlineKeyboardButton(str(value), callback_data=str(key))
        keyboard.append([button])
    reply_markup = InlineKeyboardMarkup(keyboard)
    return await context.bot.send_message(
        update.effective_message.chat_id,
        text=text, reply_markup=reply_markup,
        message_thread_id=update.effective_message.message_thread_id)


# Надсилає повідомлення та красиву сітку кнопок (по N штук в рядку)
async def send_grid_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE,
                            text: str, buttons: dict, row_width: int = 3) -> Message:
    text = text.encode('utf16', errors='surrogatepass').decode('utf16')

    keyboard = []
    current_row = []  # Кишеня для одного рядка

    for key, value in buttons.items():
        button = InlineKeyboardButton(str(value), callback_data=str(key))
        current_row.append(button)  # Додаємо кнопку в поточний рядок

        # Якщо рядок заповнився (наприклад, там уже 3 карти) — скидаємо його в клавіатуру
        if len(current_row) == row_width:
            keyboard.append(current_row)
            current_row = []  # Очищаємо кишеню для наступного рядка

    # Якщо після циклу залишилися «хвости» (наприклад, всього було 5 карт: 3 лягли в перший рядок, 2 залишилися)
    if current_row:
        keyboard.append(current_row)

    reply_markup = InlineKeyboardMarkup(keyboard)
    return await context.bot.send_message(
        update.effective_message.chat_id,
        text=text, reply_markup=reply_markup,
        message_thread_id=update.effective_message.message_thread_id)


# надсилає в чат фото
async def send_image(update: Update, context: ContextTypes.DEFAULT_TYPE,
                     name: str) -> Message:
    with open(f'resources/images/{name}.jpg', 'rb') as image:
        return await context.bot.send_photo(chat_id=update.effective_chat.id,
                                            photo=image)

# відображає команду та головне меню
async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE,
                         commands: dict):
    command_list = [BotCommand(key, value) for key, value in commands.items()]
    await context.bot.set_my_commands(command_list, scope=BotCommandScopeChat(
        chat_id=update.effective_chat.id))
    await context.bot.set_chat_menu_button(menu_button=MenuButtonCommands(),
                                           chat_id=update.effective_chat.id)

# видаляємо команди для конкретного чату
async def hide_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.delete_my_commands(
        scope=BotCommandScopeChat(chat_id=update.effective_chat.id))
    await context.bot.set_chat_menu_button(menu_button=MenuButtonDefault(),
                                           chat_id=update.effective_chat.id)

# завантажує повідомлення з папки /resources/messages/
def load_message(name):
    with open("resources/messages/" + name + ".txt", "r",
              encoding="utf8") as file:
        return file.read()

# завантажує промпт з папки /resources/messages/
def load_prompt(name):
    with open("resources/prompts/" + name + ".txt", "r",
              encoding="utf8") as file:
        return file.read()

async def default_callback_handler(update: Update,
                                   context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    query = update.callback_query.data
    await send_html(update, context, f'You have pressed button with {query} callback')


async def send_grid_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE,
                            text: str, buttons: dict, row_width: int = 3, edit: bool = False) -> Message:
    text = text.encode('utf16', errors='surrogatepass').decode('utf16')
    keyboard = []  # ОСЬ ВІН — НАШ СПИСОК КЛАВІАТУРИ, ЯКИЙ ЗГУБИВСЯ!
    current_row = []  # Тимчасова кишеня для одного рядка
    for key, value in buttons.items():
        button = InlineKeyboardButton(str(value), callback_data=str(key))
        current_row.append(button)
        if len(current_row) == row_width:
            keyboard.append(current_row)
            current_row = []
    if current_row:
        keyboard.append(current_row)
    reply_markup = InlineKeyboardMarkup(keyboard)  # Тепер Python чітко бачить цей список!
    if edit:
        return await update.callback_query.edit_message_text(text=text, reply_markup=reply_markup)
    else:
        return await context.bot.send_message(chat_id=update.effective_chat.id, text=text, reply_markup=reply_markup)


class Dialog:
    pass