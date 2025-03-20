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
        """Deal initial cards to player and banker"""
        # Clear existing cards
        self.player_cards = []
        self.banker_cards = []
        
        # Deal two cards to player and banker
        for _ in range(2):
            player_card = self.draw_card()
            player_card['flipped'] = False  # Explicitly set to False
            self.player_cards.append(player_card)
            
            banker_card = self.draw_card()
            banker_card['flipped'] = False  # Explicitly set to False
            self.banker_cards.append(banker_card)
        
        # Calculate initial scores
        self.calculate_scores()
        self.save()
        
        print(f"Dealt cards - Player: {self.player_cards}, Banker: {self.banker_cards}")
    
    def calculate_scores(self):
        """Calculate the scores for player and banker hands"""
        self.player_score = self.calculate_hand_score(self.player_cards)
        self.banker_score = self.calculate_hand_score(self.banker_cards)
        self.save()
    
    def calculate_hand_score(self, cards):
        """Calculate the score for a hand of cards"""
        score = 0
        for card in cards:
            if card['value'] in ['J', 'Q', 'K', '10']:
                # Face cards are worth 0
                value = 0
            elif card['value'] == 'A':
                # Ace is worth 1
                value = 1
            else:
                # Number cards are worth their face value
                value = int(card['value'])
            score += value
        
        # In Baccarat, only the last digit of the sum matters
        return score % 10
    
    def check_natural(self):
        """Check if either hand has a natural win (8 or 9)"""
        if self.player_score >= 8 or self.banker_score >= 8:
            return True
        return False
    
    def draw_third_card(self):
        """Draw a third card according to Baccarat rules"""
        # Player draws first if needed
        if len(self.player_cards) == 2 and self.player_score <= 5:
            player_third = self.draw_card()
            player_third['flipped'] = True  # Third card is automatically flipped
            self.player_cards.append(player_third)
            # Recalculate player score
            self.player_score = self.calculate_hand_score(self.player_cards)
        
        # Banker draws based on complex rules
        if len(self.banker_cards) == 2:
            if self.banker_score <= 2:
                # Banker always draws with 0-2
                banker_third = self.draw_card()
                banker_third['flipped'] = True
                self.banker_cards.append(banker_third)
            elif self.banker_score == 3 and (len(self.player_cards) != 3 or self.player_cards[2]['value'] != '8'):
                # Banker draws with 3 unless player's third card is 8
                banker_third = self.draw_card()
                banker_third['flipped'] = True
                self.banker_cards.append(banker_third)
            elif self.banker_score == 4 and len(self.player_cards) == 3 and self.player_cards[2]['value'] in ['2', '3', '4', '5', '6', '7']:
                # Banker draws with 4 if player's third card is 2-7
                banker_third = self.draw_card()
                banker_third['flipped'] = True
                self.banker_cards.append(banker_third)
            elif self.banker_score == 5 and len(self.player_cards) == 3 and self.player_cards[2]['value'] in ['4', '5', '6', '7']:
                # Banker draws with 5 if player's third card is 4-7
                banker_third = self.draw_card()
                banker_third['flipped'] = True
                self.banker_cards.append(banker_third)
            elif self.banker_score == 6 and len(self.player_cards) == 3 and self.player_cards[2]['value'] in ['6', '7']:
                # Banker draws with 6 if player's third card is 6-7
                banker_third = self.draw_card()
                banker_third['flipped'] = True
                self.banker_cards.append(banker_third)
        
        # Recalculate banker score
        self.banker_score = self.calculate_hand_score(self.banker_cards)
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