import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

from gpt import ChatGptService
# 1. Підключаємо наші автономні модулі-зварювальники
from durak_game import Deck, Player  # Твої вчорашні залізобетонні класи!
from util import send_text_buttons, send_grid_buttons, load_message  # Наші утиліти


# async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     text = load_message('main')
#     await send_image(update, context, 'main')
#     await send_text(update, context, text)
#     await show_main_menu(update, context, {
#         'start': 'Головне меню',
#         'random': 'Дізнатися випадковий цікавий факт 🧠',
#         'gpt': 'Задати питання чату GPT 🤖',
#         'talk': 'Поговорити з відомою особистістю 👤',
#         'quiz': 'Взяти участь у квізі ❓'
#         # Додати команду в меню можна так:
#         # 'command': 'button text'
#
#     })

# 2. Завантажуємо секретні токени через модуль os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, '.env'))
BOT_TOKEN = os.getenv("BOT_TOKEN")
# Глобальний словник для збереження активних ігор користувачів: {chat_id: об'єкт_гри}
user_games = {}

# 3. Хендлер команди /start
async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    # Створюємо словник для кнопок вибору колоди
    deck_options = {
        "setup_36": "🃏 36 карт (Класична)",
        "setup_52": "🃏 52 карти (Велика)",
        "setup_54": "🃏 54 карти (З Джокерами! 🔥)"
    }
    # Використовуємо готову утиліту для відправки тексту з кнопками!
    await send_text_buttons(
        update,
        context,
        "Привіт! Ласкаво просимо до гри в Дурака з ШІ.\nВибери розмір колоди для цієї партії:",
        deck_options
    )
# Функція-конвертер карт гравця у словник для кнопок
def get_player_cards_dict(player_hand) -> dict:
    cards_buttons = {}
    for index, card in enumerate(player_hand):
        # Технічний ключ для хендлера (наприклад, "move_0") та красивий текст карти для екрана
        cards_buttons[f"move_{index}"] = f"{card.rank}{card.suit}"
    return cards_buttons

# Хендлер, який ловить кліки по кнопках вибору колоди
async def select_deck_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Зупиняємо таймер-коліщатко на кнопці в Telegram, щоб вона не зависала
    await update.callback_query.answer()
    chat_id = update.effective_chat.id
    query_data = update.callback_query.data  # Отримуємо сигнал (наприклад, "setup_54")
    # Визначаємо розмір колоди на основі натиснутої кнопки
    deck_type = 36
    if query_data == "setup_52":
        deck_type = 52
    elif query_data == "setup_54":
        deck_type = 54
    # 1. СТВОРЮЄМО ОБ'ЄКТИ ГРИ В ПАМ'ЯТІ
    deck = Deck(deck_type=deck_type)
    player = Player("Денис")
    bot_player = Player("ChatGPT")
    # 2. ПЕРША РОЗДАЧА КАРТ
    # Роздаємо по 6 карт гравцю та боту строго через .pop_card()
    for _ in range(6):
        player.take_card(deck.pop_card())
        bot_player.take_card(deck.pop_card())
    # Визначаємо козир (беремо випадкову карту з залишку колоди)
    trump_card = deck.cards[-1] if len(deck.cards) > 0 else player.hand[0]
    trump_suit = trump_card.suit
    # Сортуємо руку за допомогою алгоритму сортування з вагами!
    player.sort_hand(trump_suit)
    # 3. ЗБЕРІГАЄМО СТАН ГРИ У СЕЙФ
    # Записуємо всі об'єкти в наш глобальний словник, щоб гра не губилася між повідомленнями!
    user_games[chat_id] = {
        "deck": deck,
        "player": player,
        "bot": bot_player,
        "trump_suit": trump_suit
    }
    # 4. ВИВОДИМО РЕЗУЛЬТАТ В БОТА
    # Показуємо інформацію про гру
    await context.bot.send_message(
        chat_id=chat_id,
        text=f" Game Started!\nКолода: {deck_type} карт.\nКозирний супер-супутник цієї партії: {trump_suit}\n"
             f"У колоді залишилось карт: {len(deck.cards)}"
    )
    # Генеруємо словник кнопок для карт
    player_buttons = get_player_cards_dict(player.hand)
    # Виводимо карти красивою, компактною сіткою по 4 штуки в ряд!
    await send_grid_buttons(
        update,
        context,
        "Твої карти (сортовані). Зроби свій перший хід, клікнувши по кнопці:",
        player_buttons,
        row_width=3
    )
# 4. Двигун запуску бота (в самому низу файлу bot.py)
if __name__ == "__main__":
    print("Бот-Дурак з ШІ запускається...")
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    # Реєструємо команду /start
    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(CallbackQueryHandler(select_deck_callback, pattern="^setup_"))
    print("Бот успішно злетів! Перевіряй на Poco.")
    app.run_polling()



chat_gpt = ChatGptService('CHATGPT_TOKEN')
app = ApplicationBuilder().token('BOT_TOKEN').build()

                # Зареєструвати обробник команди можна так:
                # app.add_handler(CommandHandler('command', handler_func))

                # Зареєструвати обробник колбеку можна так:
                # app.add_handler(CallbackQueryHandler(app_button, pattern='^app_.*'))
# app.add_handler(CallbackQueryHandler(default_callback_handler))
# app.run_polling()
