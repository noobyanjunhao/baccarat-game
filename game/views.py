from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from .models import Game
import json
import uuid

def home(request):
    return render(request, 'game/home.html')

@login_required
def new_game(request):
    if request.method == 'POST':
        bet_on = request.POST.get('bet_on')
        buy_in = request.POST.get('buy_in')  # Changed from bet_amount
        
        game = Game.objects.create(
            player=request.user,
            bet_on=bet_on,
            buy_in=buy_in,  # Changed from bet_amount
            shoe_id=uuid.uuid4()  # Generate a unique ID for this shoe
        )
        
        game.initialize_shoe()  # Use 8-deck shoe instead of single deck
        game.deal_initial_cards()
        
        return redirect('game_play', game_id=game.id)
    
    return render(request, 'game/new_game.html')

@login_required
def game_play(request, game_id):
    game = get_object_or_404(Game, id=game_id, player=request.user)
    
    # Check if game is complete
    game_complete = game.result is not None
    
    context = {
        'game': game,
        'game_complete': game_complete,
    }
    
    return render(request, 'game/game_play.html', context)

@login_required
@require_POST
def flip_card(request, game_id):
    game = get_object_or_404(Game, id=game_id, player=request.user)
    data = json.loads(request.body)
    
    card_type = data.get('card_type')  # 'player' or 'banker'
    card_index = data.get('card_index')
    
    if card_type == 'player':
        if card_index < len(game.player_cards):
            game.player_cards[card_index]['flipped'] = True
    elif card_type == 'banker':
        if card_index < len(game.banker_cards):
            game.banker_cards[card_index]['flipped'] = True
    
    game.save()
    
    # Check if all initial cards are flipped
    all_flipped = all(card['flipped'] for card in game.player_cards[:2]) and \
                  all(card['flipped'] for card in game.banker_cards[:2])
    
    response_data = {
        'player_cards': game.player_cards,
        'banker_cards': game.banker_cards,
        'player_score': game.player_score,
        'banker_score': game.banker_score,
    }
    
    if all_flipped and game.is_active:
        # Check for natural win
        if not game.check_natural():
            # Draw third card according to rules
            game.draw_third_card()
            response_data['player_cards'] = game.player_cards
            response_data['banker_cards'] = game.banker_cards
            response_data['player_score'] = game.player_score
            response_data['banker_score'] = game.banker_score
        
        # Determine winner
        winner = game.determine_winner()
        response_data['result'] = winner
        response_data['payout'] = float(game.payout)
    
    return JsonResponse(response_data)

@login_required
def game_history(request):
    games = Game.objects.filter(player=request.user, is_active=False).order_by('-created_at')
    return render(request, 'game/history.html', {'games': games})

@login_required
def continue_game(request, game_id):
    """Start a new round with the same shoe"""
    previous_game = get_object_or_404(Game, id=game_id, player=request.user)
    
    if request.method == 'POST':
        bet_on = request.POST.get('bet_on')
        buy_in = request.POST.get('buy_in')  # Changed from bet_amount
        
        # Create new game with same shoe
        game = Game.objects.create(
            player=request.user,
            bet_on=bet_on,
            buy_in=buy_in,  # Changed from bet_amount
            shoe_id=previous_game.shoe_id,
            round_number=previous_game.round_number + 1,
            cards_used=previous_game.cards_used,
            deck=previous_game.deck
        )
        
        # Check if we need a new shoe
        if game.needs_new_shoe():
            game.initialize_shoe()
        
        game.deal_initial_cards()
        
        return redirect('game_play', game_id=game.id)
    
    return render(request, 'game/continue_game.html', {'previous_game': previous_game})