import os
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardMarkup
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


def can_beat_card(attack_card, defend_card, trump_suit) -> bool:
    """Твоя фірмова логіка відбиття з урахуванням Джокерів та Козирів"""
    # 1. Якщо карта захисту — Супер-Джокер
    if defend_card.is_super_trump(trump_suit):
        return True
    # 2. Якщо карта атаки — Супер-Джокер, її побити не можна
    if attack_card.is_super_trump(trump_suit):
        return False
    # 3. Якщо захищаємося звичайним Джокером (він некозирний і нічого не б'є)
    if defend_card.is_joker():
        return False
    # 4. Якщо нас атакують звичайним Джокером (він некозирний)
    if attack_card.is_joker():
        # Звичайного Джокера можна побити будь-яким козирем
        return defend_card.suit == trump_suit
    # 5. Класичні правила для звичайних карт
    if attack_card.suit == defend_card.suit:
        return defend_card.rank_val > attack_card.rank_val
    # Якщо масті різні, побити можна тільки козирем
    return defend_card.suit == trump_suit


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
def get_player_cards_dict(player_hand, role: str) -> dict:
    cards_buttons = {}
    # Заповнюємо карти
    for index, card in enumerate(player_hand):
        cards_buttons[f"move_{index}"] = f"{card.rank}{card.suit}"
    # Додаємо спец-кнопку в самий кінець словника!
    if role == "defend":
        cards_buttons["action_take"] = "🥵 Забрати карти"
    elif role == "attack":
        cards_buttons["action_bito"] = "✅ Бито (Пас)"
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
    # Визначаємо випадково, хто ходить першим (як у твоїй грі!)
    from random import choice as rand_choice
    attacker = rand_choice(["player", "bot"])
    # ЗБЕРІГАЄМО СТАН ГРИ У СЕЙФ (додали змінну attacker)
    user_games[chat_id] = {
        "deck": deck,
        "player": player,
        "bot": bot_player,
        "trump_suit": trump_suit,
        "attacker": attacker,  # Хто зараз атакує
        "table": []  # Карти, які зараз лежать на столі
    }
    # Показуємо інформацію про гру
    await context.bot.send_message(
        chat_id=chat_id,
        text=f"🃏 Гра почалася! Козир: {trump_suit}\n"
             f"👉 Першим ходить: {'ТИ' if attacker == 'player' else '🤖 БОТ'}"
    )
    # ЯКЩО ПЕРШИМ ХОДИТЬ БОТ — запускаємо його атаку одразу!
    if attacker == "bot":
        await bot_attack_logic(update, context, chat_id)
    else:
        # Якщо ходиш ти — виводимо твої карти
        player_buttons = get_player_cards_dict(player.hand, role="attack")
        await send_grid_buttons(update, context, "Твої карти для ходу:", player_buttons, row_width=3)

    # 4. ВИВОДИМО РЕЗУЛЬТАТ В БОТА
    # Показуємо інформацію про гру
    await context.bot.send_message(
        chat_id=chat_id,
        text=f" Game Started!\nКолода: {deck_type} карт.\nКозирний супер-супутник цієї партії: {trump_suit}\n"
             f"У колоді залишилось карт: {len(deck.cards)}"
    )
    # Генеруємо словник кнопок для карт
    player_buttons = get_player_cards_dict(player.hand, role="attack")
    # Виводимо карти красивою, компактною сіткою по 4 штуки в ряд!
    await send_grid_buttons(
        update,
        context,
        "Твої карти (сортовані). Зроби свій перший хід, клікнувши по кнопці:",
        player_buttons,
        row_width=3
    )
async def bot_attack_logic(update: Update, context: ContextTypes.DEFAULT_TYPE, chat_id: int):
    game_data = user_games[chat_id]
    bot_player = game_data["bot"]
    trump_suit = game_data["trump_suit"]
    player = game_data["player"]
    # Бот шукає найкращу карту для атаки з твого алгоритму min!
    bot_card = bot_player.get_best_attack_card(trump_suit)
    if bot_card:
        bot_player.hand.remove(bot_card)
        game_data["table"].append(bot_card)  # Кладемо карту на стіл
        # Бот походив, тепер черга Дениса ВІДБИВАТИСЯ!
        player_buttons = get_player_cards_dict(player.hand, role="defend")
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"⚔️ Бот атакує тебе картою: {bot_card.rank}{bot_card.suit}\nВибери карту з рук, щоб ПОБИТИ її:"
        )
        await send_grid_buttons(update, context, "Чим будеш битися?", player_buttons, row_width=3, edit=True)
    else:
        # Якщо у бота раптом немає карт — кінець
        await context.bot.send_message(chat_id=chat_id, text="🏳️ У бота закінчилися карти!")


async def player_card_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    chat_id = update.effective_chat.id
    query_data = update.callback_query.data

    if chat_id not in user_games:
        return

    game_data = user_games[chat_id]
    player = game_data["player"]
    bot_player = game_data["bot"]
    deck = game_data["deck"]
    trump_suit = game_data["trump_suit"]
    attacker = game_data["attacker"]

    card_index = int(query_data.split("_")[1])
    if card_index >= len(player.hand):
        return

    # === СЦЕНАРІЙ 1: ДЕНИС АТАКУЄ (Бот має відбитися) ===
    if attacker == "player":
        player_card = player.hand.pop(card_index)
        # Шукаємо, чим бот може побити твою карту
        suitable_defend_cards = [c for c in bot_player.hand if can_beat_card(player_card, c, trump_suit)]
        if suitable_defend_cards:
            best_defend_card = min(suitable_defend_cards, key=lambda card: card.rank_val)
            bot_player.hand.remove(best_defend_card)

            # ХІД ПЕРЕХОДИТЬ ДО БОТА!
            game_data["attacker"] = "bot"
            # Добір карт (Твій фірмовий цикл)
            while len(deck.cards) > 0 and len(player.hand) < 6: player.take_card(deck.pop_card())
            while len(deck.cards) > 0 and len(bot_player.hand) < 6: bot_player.take_card(deck.pop_card())
            player.sort_hand(trump_suit)
            # Запускаємо атаку бота
            await bot_attack_logic(update, context, chat_id)
        else:
            # Бот не зміг відбитися і забирає карту!
            bot_player.take_card(player_card)
            # Замість send_message ми беремо існуючий update і примусово міняємо текст всередині кнопки!
            await update.callback_query.edit_message_text(
                text=f"⚔️ Твій хід прийнято!\n🃏 Карт у колоді: {len(deck.cards)}",
                reply_markup=InlineKeyboardMarkup(keyboard)  # Передаємо нову сітку карт прямо сюди!
            )
            # Хід залишається у Дениса. Добираємо карти і виводимо нові кнопки
            while len(deck.cards) > 0 and len(player.hand) < 6: player.take_card(deck.pop_card())
            player.sort_hand(trump_suit)
            player_buttons = get_player_cards_dict(player.hand, role="attack")
            await send_grid_buttons(update, context, "Твої карти для наступного ходу:", player_buttons, row_width=3, edit=True)
    # === СЦЕНАРІЙ 2: ДЕНИС ВІДБИВАЄТЬСЯ ВІД БОТА ===
    elif attacker == "bot":
        bot_attack_card = game_data["table"][-1]  # Остання карта бота на столі
        player_card = player.hand[card_index]  # Карта, якою Денис хоче побити
        # Перевіряємо за твоїми правилами, чи може Денис побити карту бота
        if can_beat_card(bot_attack_card, player_card, trump_suit):
            player.hand.pop(card_index)  # Прибираємо карту з руки, бо хід валідний
            game_data["table"].pop()  # Прибираємо карту бота зі столу
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"🛡️ Ти успішно побив {bot_attack_card} своєю {player_card}!\n\nБИТО! Тепер ТВОЯ черга атакувати бота ⚔️"
            )
            # ХІД ПЕРЕХОДИТЬ ДО ДЕНИСА!
            game_data["attacker"] = "player"
            # Добір карт
            while len(deck.cards) > 0 and len(player.hand) < 6: player.take_card(deck.pop_card())
            while len(deck.cards) > 0 and len(bot_player.hand) < 6: bot_player.take_card(deck.pop_card())
            player.sort_hand(trump_suit)
            # Виводимо карти Дениса для його власної атаки
            player_buttons = get_player_cards_dict(player.hand, role="attack")
            await send_grid_buttons(update, context, "Твої карти для атаки на бота:", player_buttons, row_width=3)
        else:
            # Якщо користувач вибрав карту, яка не б'є за правилами
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"❌ Твоя {player_card} не може побити {bot_attack_card}! Вибери іншу карту або візьми (цю логіку допишемо)."
            )


chat_gpt = ChatGptService('CHATGPT_TOKEN')
app = ApplicationBuilder().token('BOT_TOKEN').build()

# 4. Двигун запуску бота (в самому низу файлу bot.py)
if __name__ == "__main__":
    print("Бот-Дурак з ШІ запускається...")
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    # Реєструємо команду /start
    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(CallbackQueryHandler(select_deck_callback, pattern="^setup_"))
    app.add_handler(CallbackQueryHandler(player_card_callback, pattern="^move_"))
    print("Бот успішно злетів! Перевіряй на Poco.")
    app.run_polling()

                # Зареєструвати обробник команди можна так:
                # app.add_handler(CommandHandler('command', handler_func))

                # Зареєструвати обробник колбеку можна так:
                # app.add_handler(CallbackQueryHandler(app_button, pattern='^app_.*'))
# app.add_handler(CallbackQueryHandler(default_callback_handler))
# app.run_polling()
