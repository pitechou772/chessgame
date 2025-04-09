from PIL import Image
import os

# Load the image
image_path = "./images/image-chess.jpg"
img = Image.open(image_path).convert("RGBA")

# Dimensions and setup
width, height = img.size
rows, cols = 2, 6  # 2 rows (white, black), 6 columns (rook to pawn)
piece_codes = [
    'R', 'N', 'B', 'Q', 'K', 'P'  # Rook, Knight, Bishop, Queen, King, Pawn
]
colors = ['b', 'w']  # top row = black, bottom row = white

# Calculate size of each piece
piece_width = width // cols
piece_height = height // rows

# Create output directory
output_dir = "./images"
os.makedirs(output_dir, exist_ok=True)

# Crop and save each piece
filenames = []

for row in range(rows):
    for col in range(cols):
        left = col * piece_width
        upper = row * piece_height
        right = left + piece_width
        lower = upper + piece_height

        piece = img.crop((left, upper, right, lower))

        # Remove background (make fully transparent where background-colored)
        datas = piece.getdata()
        newData = []
        for item in datas:
            # Assuming background is this greyish color
            if item[:3] == (203, 208, 207):  # background RGB
                newData.append((255, 255, 255, 0))  # fully transparent
            else:
                newData.append(item)
        piece.putdata(newData)

        # Naming: bR.png, wK.png, etc.
        filename = f"{colors[row]}{piece_codes[col]}.png"
        filepath = os.path.join(output_dir, filename)
        piece.save(filepath, "PNG")
        filenames.append(filename)

filenames
