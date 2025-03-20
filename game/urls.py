from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('new-game/', views.new_game, name='new_game'),
    path('game/<int:game_id>/', views.game_play, name='game_play'),
    path('game/<int:game_id>/continue/', views.continue_game, name='continue_game'),
    path('game/<int:game_id>/flip-card/', views.flip_card, name='flip_card'),
    path('history/', views.game_history, name='game_history'),
]