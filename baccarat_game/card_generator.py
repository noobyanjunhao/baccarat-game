# card_generator.py
from PIL import Image, ImageDraw, ImageFont
import os

# Create directory if it doesn't exist
os.makedirs('static/images/cards', exist_ok=True)

# Create card back
img = Image.new('RGB', (100, 140), color=(53, 101, 77))
d = ImageDraw.Draw(img)
d.rectangle([5, 5, 95, 135], outline=(255, 215, 0), width=2)
d.text((50, 70), "?", fill=(255, 215, 0), anchor="mm", font=ImageFont.load_default())
img.save('static/images/cards/back.png')

# Card suits and values
suits = ['hearts', 'diamonds', 'clubs', 'spades']
values = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']

# Colors for suits
suit_colors = {
    'hearts': (255, 0, 0),
    'diamonds': (255, 0, 0),
    'clubs': (0, 0, 0),
    'spades': (0, 0, 0)
}

# Create card for each suit and value
for suit in suits:
    for value in values:
        img = Image.new('RGB', (100, 140), color=(255, 255, 255))
        d = ImageDraw.Draw(img)
        d.rectangle([5, 5, 95, 135], outline=(0, 0, 0), width=1)
        
        # Draw value at top-left and bottom-right
        color = suit_colors[suit]
        d.text((10, 10), value, fill=color, font=ImageFont.load_default())
        d.text((90, 130), value, fill=color, anchor="rs", font=ImageFont.load_default())
        
        # Draw suit symbol in the middle
        suit_symbol = {'hearts': '♥', 'diamonds': '♦', 'clubs': '♣', 'spades': '♠'}[suit]
        d.text((50, 70), suit_symbol, fill=color, anchor="mm", font=ImageFont.load_default())
        
        # Save the image
        img.save(f'static/images/cards/{suit}_{value}.png')

print("Card images created successfully!")