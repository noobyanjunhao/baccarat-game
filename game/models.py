from django.db import models

# Create your models here.
from django.db import models
from django.contrib.auth.models import User
import random
import json

class Game(models.Model):
    player = models.ForeignKey(User, on_delete=models.CASCADE, related_name='games')
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    player_cards = models.JSONField(default=list)
    banker_cards = models.JSONField(default=list)
    deck = models.JSONField(default=list)
    player_score = models.IntegerField(default=0)
    banker_score = models.IntegerField(default=0)
    bet_on = models.CharField(max_length=10, choices=[
        ('player', 'Player'),
        ('banker', 'Banker'),
        ('tie', 'Tie')
    ])
    buy_in = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    result = models.CharField(max_length=10, null=True, blank=True)
    payout = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # New fields for shoe management
    shoe_id = models.CharField(max_length=36, null=True, blank=True)
    round_number = models.IntegerField(default=1)
    cards_used = models.IntegerField(default=0)
    
    # New field to track total winnings
    total_winnings = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    def initialize_deck(self):
        suits = ['hearts', 'diamonds', 'clubs', 'spades']
        values = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']
        deck = [{'suit': suit, 'value': value, 'flipped': False} for suit in suits for value in values]
        random.shuffle(deck)
        self.deck = deck
        self.save()
    
    # Add new method for 8-deck shoe
    def initialize_shoe(self):
        """Initialize a shoe with 8 decks of cards"""
        suits = ['hearts', 'diamonds', 'clubs', 'spades']
        values = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']
        
        # Create 8 decks
        shoe = []
        for _ in range(8):
            deck = [{'suit': suit, 'value': value, 'flipped': False} 
                   for suit in suits for value in values]
            shoe.extend(deck)
        
        random.shuffle(shoe)
        self.deck = shoe
        self.cards_used = 0
        self.save()
    
    def needs_new_shoe(self):
        """Determine if we need a new shoe"""
        # Typically reshuffle when about 70-80% of cards are used
        # With 8 decks (416 cards), reshuffle after ~300 cards
        return self.cards_used > 300 or not self.deck
    
    def draw_card(self):
        if not self.deck:
            self.initialize_shoe()
        card = self.deck.pop(0)
        self.cards_used += 1
        self.save()
        return card
    
    def deal_initial_cards(self):
        # Deal 2 cards to player and banker
        self.player_cards = [self.draw_card(), self.draw_card()]
        self.banker_cards = [self.draw_card(), self.draw_card()]
        self.calculate_scores()
        self.save()
    
    def calculate_scores(self):
        self.player_score = self.calculate_hand_score(self.player_cards)
        self.banker_score = self.calculate_hand_score(self.banker_cards)
        self.save()
    
    def calculate_hand_score(self, cards):
        score = 0
        for card in cards:
            value = card['value']
            if value in ['10', 'J', 'Q', 'K']:
                card_value = 0
            elif value == 'A':
                card_value = 1
            else:
                card_value = int(value)
            score += card_value
        
        # In Baccarat, only the last digit of the total matters
        return score % 10
    
    def check_natural(self):
        # Check if either hand has a natural 8 or 9
        return self.player_score >= 8 or self.banker_score >= 8
    
    def draw_third_card(self):
        # Player's third card rule
        if self.player_score <= 5:
            self.player_cards.append(self.draw_card())
            self.calculate_scores()
            player_third_card_value = self.get_card_value(self.player_cards[2])
            
            # Banker's third card rule
            if self.banker_score <= 2:
                self.banker_cards.append(self.draw_card())
            elif self.banker_score == 3 and player_third_card_value != 8:
                self.banker_cards.append(self.draw_card())
            elif self.banker_score == 4 and player_third_card_value in [2, 3, 4, 5, 6, 7]:
                self.banker_cards.append(self.draw_card())
            elif self.banker_score == 5 and player_third_card_value in [4, 5, 6, 7]:
                self.banker_cards.append(self.draw_card())
            elif self.banker_score == 6 and player_third_card_value in [6, 7]:
                self.banker_cards.append(self.draw_card())
        elif self.banker_score <= 5:
            # If player stands with 6 or 7, banker draws on 0-5
            self.banker_cards.append(self.draw_card())
        
        self.calculate_scores()
        self.save()
    
    def get_card_value(self, card):
        value = card['value']
        if value in ['10', 'J', 'Q', 'K']:
            return 0
        elif value == 'A':
            return 1
        else:
            return int(value)
    
    def determine_winner(self):
        if self.player_score == self.banker_score:
            self.result = 'tie'
        elif self.player_score > self.banker_score:
            self.result = 'player'
        else:
            self.result = 'banker'
        
        self.calculate_payout()
        self.is_active = False
        self.save()
        return self.result
    
    def calculate_payout(self):
        if self.result == self.bet_on:
            if self.bet_on == 'player':
                self.payout = self.buy_in * 2  # 1:1 payout
                self.total_winnings = self.buy_in  # Net win is the bet amount
            elif self.bet_on == 'banker':
                # 1:1 payout with 5% commission
                self.payout = self.buy_in * 1.95
                self.total_winnings = self.buy_in * 0.95  # Net win minus commission
            elif self.bet_on == 'tie':
                self.payout = self.buy_in * 9  # 8:1 payout
                self.total_winnings = self.buy_in * 8  # Net win is 8x the bet
        else:
            self.payout = 0
            self.total_winnings = -self.buy_in  # Loss is negative buy-in amount
        self.save()