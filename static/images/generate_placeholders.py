"""
Generate placeholder images for vehicle types.
Run this script once to create default images.
"""
from PIL import Image, ImageDraw, ImageFont
import os

def create_placeholder(text, color, filename):
    """Create a placeholder image with text."""
    width, height = 800, 600
    image = Image.new('RGB', (width, height), color=color)
    draw = ImageDraw.Draw(image)
    
    # Try to use a nice font, fall back to default if not available
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 80)
    except:
        font = ImageFont.load_default()
    
    # Calculate text position (centered)
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    x = (width - text_width) / 2
    y = (height - text_height) / 2
    
    # Draw text
    draw.text((x, y), text, fill='white', font=font)
    
    # Save image
    image.save(filename)
    print(f"Created {filename}")

if __name__ == "__main__":
    # Create placeholder images
    create_placeholder("CAR", "#667eea", "car.jpg")
    create_placeholder("MOTORBIKE", "#764ba2", "motorbike.jpg")
    create_placeholder("TRUCK", "#28a745", "truck.jpg")
    create_placeholder("VEHICLE", "#6c757d", "default.jpg")
    
    print("\nPlaceholder images created successfully!")
    print("You can replace these with real vehicle images later.")

