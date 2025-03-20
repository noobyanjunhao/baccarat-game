# Baccarat Game

A web-based implementation of the classic casino card game Baccarat, built with Django.

## Features

- Authentic Baccarat gameplay following standard casino rules
- 8-deck shoe implementation for realistic card distribution
- Continuous play option to keep playing with the same shoe
- Tracking of winnings and losses
- Game history to review past hands
- User authentication system

## Game Rules

Baccarat is a comparing card game played between two hands, the "player" and the "banker". Each baccarat coup (round of play) has three possible outcomes:
- Player wins
- Banker wins
- Tie

### Card Values
- Cards 2-9 are worth their face value
- 10, J, Q, K are worth 0
- Ace is worth 1

The score of a hand is the sum of the values of its cards modulo 10 (only the last digit matters).

### Betting Options
- Bet on Player: Pays 1:1
- Bet on Banker: Pays 1:1 (minus 5% commission)
- Bet on Tie: Pays 8:1

## Technical Details

- Built with Django 5.1
- Uses SQLite database for data storage
- JavaScript for interactive card flipping and game progression
- Bootstrap for responsive design

## Usage

1. Register or log in to your account
2. Start a new game by selecting your bet type and buy-in amount
3. Click on cards to flip them and reveal their values
4. After the hand is complete, you can:
   - Continue with the same shoe
   - Start a new game with a fresh shoe
   - View your game history

## Future Enhancements

- Multiplayer functionality
- More betting options (e.g., Pair bets)
- Animated card dealing
- Sound effects
- Mobile app version
