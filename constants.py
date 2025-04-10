
# constants.py
import pygame

# Dimensions
WIDTH, HEIGHT = 600, 600
SQUARE_SIZE = WIDTH // 8

# Couleurs
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (128, 128, 128)
LIGHT_SQUARE = (240, 217, 181)
DARK_SQUARE = (181, 136, 99)
HIGHLIGHT = (186, 202, 68)
MOVE_HIGHLIGHT = (106, 135, 77, 150)  # Couleur semi-transparente pour les mouvements
CHECK_HIGHLIGHT = (214, 85, 80, 200)   # Rouge semi-transparent pour l'échec

# Modes de jeu
GAME_MODES = {
    "Blitz": {"time": 180, "increment": 2, "description": "3min + 2sec"},
    "Rapide": {"time": 600, "increment": 5, "description": "10min + 5sec"},
    "Standard": {"time": 1800, "increment": 0, "description": "30min"}
}

# Initialisation des polices
pygame.font.init()
TITLE_FONT = pygame.font.SysFont('Arial', 36)
SMALL_FONT = pygame.font.SysFont('Arial', 24)
INPUT_FONT = pygame.font.SysFont('Arial', 30)