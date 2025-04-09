import os
from PIL import Image
import numpy as np

# Taille des cases
SQUARE_SIZE = 80

# Liste des pièces
pieces = ['wp', 'wR', 'wN', 'wB', 'wQ', 'wK', 'bp', 'bR', 'bN', 'bB', 'bQ', 'bK']

# Dossiers source et destination
source_dir = "./images"
adjusted_dir = "./images"
os.makedirs(adjusted_dir, exist_ok=True)

def remove_background(img):
    # Convertir l'image en tableau numpy
    data = np.array(img)
    
    # Créer un masque alpha (transparence)
    # Déterminer la couleur de fond en prenant celle du coin supérieur gauche
    background_color = tuple(data[0, 0, :3])
    
    # Tolérance de couleur (pour les variations légères dans la couleur de fond)
    tolerance = 30
    
    # Créer un masque où True indique les pixels qui sont proches du fond
    r, g, b = background_color
    mask = ((abs(data[:,:,0] - r) < tolerance) & 
            (abs(data[:,:,1] - g) < tolerance) & 
            (abs(data[:,:,2] - b) < tolerance))
    
    # Appliquer le masque au canal alpha
    data[:,:,3] = np.where(mask, 0, 255)
    
    return Image.fromarray(data)

# Traiter les images des pièces
for piece in pieces:
    try:
        img_path = os.path.join(source_dir, piece + ".png")
        piece_img = Image.open(img_path).convert("RGBA")

        # Redimensionner la pièce
        resized_piece = piece_img.resize((SQUARE_SIZE, SQUARE_SIZE), Image.LANCZOS)
        
        # Retirer l'arrière-plan
        transparent_piece = remove_background(resized_piece)
        
        # Sauvegarder l'image avec transparence
        transparent_piece.save(os.path.join(adjusted_dir, piece + ".png"), "PNG")
        print(f"Image traitée: {piece}.png")
    except Exception as e:
        print(f"Erreur pour la pièce {piece}: {e}")