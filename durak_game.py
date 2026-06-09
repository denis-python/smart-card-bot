import json
from random import shuffle, choice

# Твої залізобетонні масті з емодзі
SUITS = ["♠️", "♣️", "♦️", "♥️"]

class Card:
    def __init__(self, suit, rank, rank_val):
        self.suit = suit          # Масть (наприклад, "♠️")
        self.rank = rank          # Ранг текстовий (наприклад, "6" або "A")
        self.rank_val = rank_val  # Сила карти в пам'яті (наприклад, 6 або 14)

    def is_joker(self):
        """Перевіряє, чи є карта Джокером"""
        return self.suit == "🃏"  # Замінили порожній рядок на красивий емодзі-джокер!

    def __str__(self):
        # Метод красивого виведення карти на екран Poco
        return f"{self.rank}{self.suit}"

    def is_super_trump(self, trump_suit):
        """Перевіряє, чи є цей Джокер Супер-Козирем для поточного козиря"""
        if not self.is_joker():
            return False
        if self.rank == "B":  # Чорний Джокер б'є чорні масті
            return trump_suit in ["♠️", "♣️"]
        else:                 # Червоний Джокер б'є червоні масті
            return trump_suit in ["♥️", "♦️"]

class Deck:
    def __init__(self, deck_type=36):
        self.cards = []
        suits = SUITS
        # Визначаємо ранги залежно від вибору користувача
        if deck_type == 36:
            ranks = ["6", "7", "8", "9", "10", "J", "Q", "K", "A"]
        else:  # Для 52 та 54 карт
            ranks = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]
        # Заповнюємо базові значення сили карт (2=2, 3=3 ... А=14)
        rank_values = {str(i): i for i in range(2, 11)}
        rank_values.update({"J": 11, "Q": 12, "K": 13, "A": 14})
        # Автоматичний цикл генерації колоди (твій фірмовий двигун!)
        for suit in suits:
            for rank in ranks:
                self.cards.append(Card(suit, rank, rank_values[rank]))
        # Якщо обрано колоду з Джокерами (54 карти)
        if deck_type == 54:
            self.cards.append(Card("🃏", "B", 15))  # Чорний Джокер
            self.cards.append(Card("🃏", "R", 15))  # Червоний Джокер
        # Перемішуємо колоду при створенні
        shuffle(self.cards)

    def pop_card(self):
        """Дістає верхню карту з колоди"""
        if len(self.cards) > 0:
            return self.cards.pop(0)
        return None


class Player:
    def __init__(self, name):
        self.name = name
        self.hand = []  # Список об'єктів класу Card у руці гравця

    def take_card(self, card):
        """Додає карту в руку, якщо вона існує"""
        if card:
            self.hand.append(card)

    def sort_hand(self, trump_suit):
        """Сортує руку: спочатку звичайні, потім Джокери, потім козирі, в кінці Супер-Джокер"""
        self.hand.sort(key=lambda card: (
            card.is_super_trump(trump_suit),  # 3. Найвищий пріоритет (Супер-Джокер буде в самому кінці)
            card.suit == trump_suit,  # 2. Другий пріоритет (звичайні козирі)
            card.is_joker(),  # 1. Третій пріоритет (звичайні некозиRequest Джокери)
            card.rank_val  # 0. Сортування за силою всередині масті
        ))

    def get_best_attack_card(self, trump_suit):
        """Знаходить найкращу карту для ходу, враховуючи заборону Джокера на останній хід"""
        if len(self.hand) == 1:
            return self.hand[0]

        # Відфільтровуємо руку: прибираємо Джокерів із вибору, щоб залишити їх на потім
        playable_cards = [card for card in self.hand if not card.is_joker()]

        if playable_cards:
            non_trumps = [card for card in playable_cards if card.suit != trump_suit]
            if non_trumps:
                return min(non_trumps, key=lambda card: card.rank_val)
            else:
                return min(playable_cards, key=lambda card: card.rank_val)
        else:
            return min(self.hand, key=lambda card: card.rank_val)
