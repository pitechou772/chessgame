import pygame
import sys
import socket
import threading
import pickle
import time

# Initialisation de Pygame
pygame.init()
WIDTH, HEIGHT = 600, 600
SQUARE_SIZE = WIDTH // 8
WINDOW = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Jeu d'Échecs Multijoueur")

# Couleurs
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (128, 128, 128)
LIGHT_SQUARE = (240, 217, 181)
DARK_SQUARE = (181, 136, 99)
HIGHLIGHT = (186, 202, 68)
MOVE_HIGHLIGHT = (106, 135, 77, 150)  # Couleur semi-transparente pour les mouvements
CHECK_HIGHLIGHT = (214, 85, 80, 200)   # Rouge semi-transparent pour l'échec

# Chargement des images des pièces
def load_images():
    """Charge les images des pièces d'échecs depuis le dossier 'images'"""
    pieces = ['wp', 'wR', 'wN', 'wB', 'wQ', 'wK', 'bp', 'bR', 'bN', 'bB', 'bQ', 'bK']
    images = {}
    for piece in pieces:
        try:
            images[piece] = pygame.transform.scale(
                pygame.image.load(f"images/{piece}.png"), (SQUARE_SIZE, SQUARE_SIZE)
            )
        except:
            print(f"Impossible de charger l'image pour {piece}. Utilisation d'une représentation simple.")
            images[piece] = None
    return images

# Classe principale pour le jeu d'échecs
class ChessGame:
    def __init__(self):
        """Initialise une nouvelle partie d'échecs"""
        self.board = self.create_board()
        self.selected_piece = None
        self.turn = 'w'  # 'w' pour blanc, 'b' pour noir
        self.valid_moves = []
        self.images = load_images()
        self.network = None
        self.is_host = False
        self.game_id = None
        self.player_color = None
        self.move_history = []
        self.king_positions = {'w': (7, 4), 'b': (0, 4)}
        self.in_check = {'w': False, 'b': False}
        self.game_status = "Playing"  # "Playing", "Checkmate", "Stalemate"
        self.castling_rights = {
            'w': {'kingside': True, 'queenside': True},
            'b': {'kingside': True, 'queenside': True}
        }
        self.en_passant_target = None  # Position d'une case où la prise en passant est possible
    
    def create_board(self):
        """Crée et retourne le plateau initial"""
        board = [
            ['bR', 'bN', 'bB', 'bQ', 'bK', 'bB', 'bN', 'bR'],
            ['bp', 'bp', 'bp', 'bp', 'bp', 'bp', 'bp', 'bp'],
            ['--', '--', '--', '--', '--', '--', '--', '--'],
            ['--', '--', '--', '--', '--', '--', '--', '--'],
            ['--', '--', '--', '--', '--', '--', '--', '--'],
            ['--', '--', '--', '--', '--', '--', '--', '--'],
            ['wp', 'wp', 'wp', 'wp', 'wp', 'wp', 'wp', 'wp'],
            ['wR', 'wN', 'wB', 'wQ', 'wK', 'wB', 'wN', 'wR']
        ]
        return board
    
    def draw_board(self, window):
        """Dessine le plateau et les pièces"""
        # Dessine l'échiquier
        for row in range(8):
            for col in range(8):
                color = LIGHT_SQUARE if (row + col) % 2 == 0 else DARK_SQUARE
                pygame.draw.rect(window, color, pygame.Rect(col * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))
                
                # Dessine la pièce
                piece = self.board[row][col]
                if piece != '--' and self.images.get(piece):
                    window.blit(self.images[piece], pygame.Rect(col * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))
                elif piece != '--':
                    # Affichage simplifié si l'image n'est pas disponible
                    font = pygame.font.SysFont('Arial', 30)
                    text = font.render(piece, True, WHITE if piece[0] == 'b' else BLACK)
                    window.blit(text, (col * SQUARE_SIZE + 15, row * SQUARE_SIZE + 15))
                
                # Surligne la case sélectionnée
                if self.selected_piece == (row, col):
                    pygame.draw.rect(window, HIGHLIGHT, pygame.Rect(col * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE), 3)
                
                # Surligne les mouvements valides
                if (row, col) in self.valid_moves:
                    # Si la case cible contient une pièce (capture), dessiner un cercle autour
                    if self.board[row][col] != '--':
                        pygame.draw.circle(window, MOVE_HIGHLIGHT, 
                                          (col * SQUARE_SIZE + SQUARE_SIZE // 2, row * SQUARE_SIZE + SQUARE_SIZE // 2), 
                                          SQUARE_SIZE // 2 - 5, 3)
                    else:
                        # Sinon, dessiner un point
                        pygame.draw.circle(window, MOVE_HIGHLIGHT, 
                                          (col * SQUARE_SIZE + SQUARE_SIZE // 2, row * SQUARE_SIZE + SQUARE_SIZE // 2), 
                                          SQUARE_SIZE // 6)
        
        # Surligne le roi en échec
        for color in ['w', 'b']:
            if self.in_check[color]:
                king_row, king_col = self.king_positions[color]
                king_rect = pygame.Rect(king_col * SQUARE_SIZE, king_row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE)
                
                # Crée une surface semi-transparente
                s = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
                s.fill(CHECK_HIGHLIGHT)
                window.blit(s, king_rect)
        
        # Dessine le statut du jeu si la partie est terminée
        if self.game_status != "Playing":
            status_surface = pygame.Surface((WIDTH, 50), pygame.SRCALPHA)
            status_surface.fill((0, 0, 0, 180))
            window.blit(status_surface, (0, HEIGHT // 2 - 25))
            
            font = pygame.font.SysFont('Arial', 36)
            text = font.render(self.game_status, True, WHITE)
            window.blit(text, (WIDTH // 2 - text.get_width() // 2, HEIGHT // 2 - text.get_height() // 2))
    
    def select_piece(self, pos):
        """Gère la sélection d'une pièce et son déplacement"""
        # Si la partie est terminée, ne rien faire
        if self.game_status != "Playing":
            return
            
        # Convertit la position du clic en position sur le plateau
        col, row = pos[0] // SQUARE_SIZE, pos[1] // SQUARE_SIZE
        
        # Si c'est le tour du joueur et qu'il sélectionne une de ses pièces
        if self.player_color and self.turn != self.player_color:
            return
        
        # Si une pièce est déjà sélectionnée
        if self.selected_piece:
            # Si le joueur clique sur la même pièce, désélectionne-la
            if self.selected_piece == (row, col):
                self.selected_piece = None
                self.valid_moves = []
                return
            
            # Si le joueur clique sur une destination valide, déplace la pièce
            if (row, col) in self.valid_moves:
                self.move_piece(self.selected_piece, (row, col))
                self.selected_piece = None
                self.valid_moves = []
                return
            
            # Si le joueur clique sur une autre pièce de sa couleur, la sélectionne
            piece = self.board[row][col]
            if piece != '--' and piece[0] == self.turn:
                self.selected_piece = (row, col)
                self.valid_moves = self.get_valid_moves((row, col))
                return
                
            # Sinon, désélectionne la pièce
            self.selected_piece = None
            self.valid_moves = []
        else:
            # Sélectionne une pièce si elle appartient au joueur actuel
            piece = self.board[row][col]
            if piece != '--' and piece[0] == self.turn:
                self.selected_piece = (row, col)
                self.valid_moves = self.get_valid_moves((row, col))
    
    def get_all_possible_moves(self, color):
        """Obtient tous les mouvements possibles pour une couleur, sans vérifier l'échec"""
        moves = []
        for row in range(8):
            for col in range(8):
                piece = self.board[row][col]
                if piece != '--' and piece[0] == color:
                    piece_moves = self.get_piece_moves((row, col))
                    moves.extend([((row, col), move) for move in piece_moves])
        return moves
    
    def is_in_check(self, color):
        """Vérifie si le roi de la couleur spécifiée est en échec"""
        king_row, king_col = self.king_positions[color]
        opponent_color = 'b' if color == 'w' else 'w'
        
        # Vérifie tous les mouvements possibles de l'adversaire
        for start_pos, end_pos in self.get_all_possible_moves(opponent_color):
            if end_pos == (king_row, king_col):
                return True
        
        return False
    
    def get_valid_moves(self, pos):
        """Obtient tous les mouvements valides pour une pièce, en tenant compte de l'échec"""
        row, col = pos
        piece = self.board[row][col]
        color = piece[0]
        
        # Obtient tous les mouvements possibles pour cette pièce
        possible_moves = self.get_piece_moves(pos)
        valid_moves = []
        
        # Vérifie chaque mouvement pour s'assurer qu'il ne met pas le roi en échec
        for move in possible_moves:
            # Fait le mouvement temporairement
            end_row, end_col = move
            captured_piece = self.board[end_row][end_col]
            
            # Mise à jour temporaire de la position du roi
            king_pos = self.king_positions[color]
            if piece[1] == 'K':
                self.king_positions[color] = (end_row, end_col)
            
            # Simule le mouvement
            self.board[end_row][end_col] = piece
            self.board[row][col] = '--'
            
            # Vérifie si le roi est en échec après ce mouvement
            in_check = self.is_in_check(color)
            
            # Annule le mouvement
            self.board[row][col] = piece
            self.board[end_row][end_col] = captured_piece
            
            # Restaure la position du roi
            if piece[1] == 'K':
                self.king_positions[color] = king_pos
            
            # Si le mouvement ne met pas le roi en échec, il est valide
            if not in_check:
                valid_moves.append(move)
        
        return valid_moves
    
    def get_piece_moves(self, pos):
        """Obtient tous les mouvements possibles pour une pièce spécifique, sans tenir compte de l'échec"""
        row, col = pos
        piece = self.board[row][col]
        piece_type = piece[1]
        color = piece[0]
        moves = []
        
        # Mouvements du pion
        if piece_type == 'p':
            direction = 1 if color == 'b' else -1
            
            # Avancer d'une case
            if 0 <= row + direction < 8 and self.board[row + direction][col] == '--':
                moves.append((row + direction, col))
                
                # Avancer de deux cases depuis la position initiale
                if (color == 'w' and row == 6) or (color == 'b' and row == 1):
                    if self.board[row + 2*direction][col] == '--':
                        moves.append((row + 2*direction, col))
            
            # Capturer en diagonale
            for offset in [-1, 1]:
                if 0 <= row + direction < 8 and 0 <= col + offset < 8:
                    # Capture normale
                    target = self.board[row + direction][col + offset]
                    if target != '--' and target[0] != color:
                        moves.append((row + direction, col + offset))
                    
                    # Prise en passant
                    if self.en_passant_target == (row + direction, col + offset):
                        moves.append((row + direction, col + offset))
        
        # Mouvements de la tour
        elif piece_type == 'R':
            # Directions: haut, droite, bas, gauche
            directions = [(-1, 0), (0, 1), (1, 0), (0, -1)]
            for dr, dc in directions:
                for i in range(1, 8):
                    r, c = row + i*dr, col + i*dc
                    if not (0 <= r < 8 and 0 <= c < 8):
                        break
                    target = self.board[r][c]
                    if target == '--':
                        moves.append((r, c))
                    elif target[0] != color:
                        moves.append((r, c))
                        break
                    else:
                        break
        
        # Mouvements du cavalier
        elif piece_type == 'N':
            knight_moves = [
                (row-2, col-1), (row-2, col+1),
                (row-1, col-2), (row-1, col+2),
                (row+1, col-2), (row+1, col+2),
                (row+2, col-1), (row+2, col+1)
            ]
            for move in knight_moves:
                r, c = move
                if 0 <= r < 8 and 0 <= c < 8:
                    target = self.board[r][c]
                    if target == '--' or target[0] != color:
                        moves.append((r, c))
        
        # Mouvements du fou
        elif piece_type == 'B':
            # Directions: diagonales
            directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
            for dr, dc in directions:
                for i in range(1, 8):
                    r, c = row + i*dr, col + i*dc
                    if not (0 <= r < 8 and 0 <= c < 8):
                        break
                    target = self.board[r][c]
                    if target == '--':
                        moves.append((r, c))
                    elif target[0] != color:
                        moves.append((r, c))
                        break
                    else:
                        break
        
        # Mouvements de la reine (combinaison tour + fou)
        elif piece_type == 'Q':
            # Directions: horizontales, verticales et diagonales
            directions = [
                (-1, 0), (0, 1), (1, 0), (0, -1),  # Tour
                (-1, -1), (-1, 1), (1, -1), (1, 1)  # Fou
            ]
            for dr, dc in directions:
                for i in range(1, 8):
                    r, c = row + i*dr, col + i*dc
                    if not (0 <= r < 8 and 0 <= c < 8):
                        break
                    target = self.board[r][c]
                    if target == '--':
                        moves.append((r, c))
                    elif target[0] != color:
                        moves.append((r, c))
                        break
                    else:
                        break
        
        # Mouvements du roi
        elif piece_type == 'K':
            # Directions: toutes les cases adjacentes
            directions = [
                (-1, -1), (-1, 0), (-1, 1),
                (0, -1),           (0, 1),
                (1, -1),  (1, 0),  (1, 1)
            ]
            for dr, dc in directions:
                r, c = row + dr, col + dc
                if 0 <= r < 8 and 0 <= c < 8:
                    target = self.board[r][c]
                    if target == '--' or target[0] != color:
                        moves.append((r, c))
            
            # Roque
            if self.castling_rights[color]['kingside']:
                if self.can_castle_kingside(color):
                    moves.append((row, col + 2))
            
            if self.castling_rights[color]['queenside']:
                if self.can_castle_queenside(color):
                    moves.append((row, col - 2))
        
        return moves
    
    def can_castle_kingside(self, color):
        """Vérifie si le roque côté roi est possible"""
        row = 7 if color == 'w' else 0
        
        # Vérifie si les cases entre le roi et la tour sont vides
        if self.board[row][5] != '--' or self.board[row][6] != '--':
            return False
        
        # Vérifie si la tour est toujours à sa place
        if self.board[row][7] != color + 'R':
            return False
        
        # Vérifie si le roi est en échec ou si les cases traversées sont attaquées
        if self.is_in_check(color):
            return False
        
        # Simule le déplacement du roi d'une case vers la droite et vérifie l'échec
        king_pos = self.king_positions[color]
        self.board[row][4], self.board[row][5] = '--', color + 'K'
        self.king_positions[color] = (row, 5)
        middle_square_attacked = self.is_in_check(color)
        self.board[row][4], self.board[row][5] = color + 'K', '--'
        self.king_positions[color] = king_pos
        
        if middle_square_attacked:
            return False
        
        return True
    
    def can_castle_queenside(self, color):
        """Vérifie si le roque côté dame est possible"""
        row = 7 if color == 'w' else 0
        
        # Vérifie si les cases entre le roi et la tour sont vides
        if self.board[row][1] != '--' or self.board[row][2] != '--' or self.board[row][3] != '--':
            return False
        
        # Vérifie si la tour est toujours à sa place
        if self.board[row][0] != color + 'R':
            return False
        
        # Vérifie si le roi est en échec ou si les cases traversées sont attaquées
        if self.is_in_check(color):
            return False
        
        # Simule le déplacement du roi d'une case vers la gauche et vérifie l'échec
        king_pos = self.king_positions[color]
        self.board[row][4], self.board[row][3] = '--', color + 'K'
        self.king_positions[color] = (row, 3)
        middle_square_attacked = self.is_in_check(color)
        self.board[row][4], self.board[row][3] = color + 'K', '--'
        self.king_positions[color] = king_pos
        
        if middle_square_attacked:
            return False
        
        return True
    
    def move_piece(self, start, end):
        """Déplace une pièce et gère les règles spéciales (promotion, roque, etc.)"""
        start_row, start_col = start
        end_row, end_col = end
        moved_piece = self.board[start_row][start_col]
        captured_piece = self.board[end_row][end_col]
        
        # Enregistre le mouvement dans l'historique
        self.move_history.append((start, end, moved_piece, captured_piece))
        
        # Gestion du roque
        if moved_piece[1] == 'K' and abs(start_col - end_col) == 2:
            # Roque côté roi
            if end_col > start_col:
                # Déplace la tour
                self.board[end_row][end_col - 1] = self.board[end_row][7]
                self.board[end_row][7] = '--'
            # Roque côté dame
            else:
                # Déplace la tour
                self.board[end_row][end_col + 1] = self.board[end_row][0]
                self.board[end_row][0] = '--'
        
        # Gestion de la prise en passant
        if moved_piece[1] == 'p' and (start_col != end_col) and captured_piece == '--':
            # C'est une prise en passant, supprime le pion capturé
            self.board[start_row][end_col] = '--'
        
        # Mise à jour de la cible de prise en passant
        self.en_passant_target = None
        if moved_piece[1] == 'p' and abs(start_row - end_row) == 2:
            # Le pion a avancé de deux cases, définir la case de prise en passant
            self.en_passant_target = (start_row + (end_row - start_row) // 2, start_col)
        
        # Déplace la pièce
        self.board[end_row][end_col] = moved_piece
        self.board[start_row][start_col] = '--'
        
        # Promotion du pion
        if moved_piece[1] == 'p' and (end_row == 0 or end_row == 7):
            # Par défaut, promotion en dame
            self.board[end_row][end_col] = moved_piece[0] + 'Q'
        
        # Mise à jour de la position du roi
        if moved_piece[1] == 'K':
            self.king_positions[moved_piece[0]] = (end_row, end_col)
        
        # Mise à jour des droits de roque
        if moved_piece[1] == 'K':
            self.castling_rights[moved_piece[0]]['kingside'] = False
            self.castling_rights[moved_piece[0]]['queenside'] = False
        
        elif moved_piece[1] == 'R':
            # Tour côté roi
            if start_col == 7:
                self.castling_rights[moved_piece[0]]['kingside'] = False
            # Tour côté dame
            elif start_col == 0:
                self.castling_rights[moved_piece[0]]['queenside'] = False
        
        # Change le tour
        self.turn = 'b' if self.turn == 'w' else 'w'
        
        # Vérifie l'échec pour les deux couleurs
        self.in_check['w'] = self.is_in_check('w')
        self.in_check['b'] = self.is_in_check('b')
        
        # Vérifie si la partie est terminée (échec et mat ou pat)
        self.check_game_over()
        
        # Si en réseau, envoie le mouvement ET l'état complet du jeu
        if self.network:
            self.network.send_move(start, end)
            # Envoie également l'état complet du jeu pour garantir la synchronisation
            time.sleep(0.1)  # Petit délai pour éviter les problèmes de réception
            self.network.send_game_state()
    def check_game_over(self):
        """Vérifie si la partie est terminée (échec et mat ou pat)"""
        # Vérifie si le joueur actuel a des mouvements valides
        has_valid_moves = False
        for row in range(8):
            for col in range(8):
                piece = self.board[row][col]
                if piece != '--' and piece[0] == self.turn:
                    moves = self.get_valid_moves((row, col))
                    if moves:
                        has_valid_moves = True
                        break
            if has_valid_moves:
                break
        
        # Si aucun mouvement valide, c'est soit un échec et mat, soit un pat
        if not has_valid_moves:
            if self.in_check[self.turn]:
                winner = 'Blancs' if self.turn == 'b' else 'Noirs'
                self.game_status = f"Échec et mat! {winner} gagnent!"
            else:
                self.game_status = "Pat! Match nul!"
    
    def host_game(self, port=5555):
        """Démarre un jeu en tant qu'hôte"""
        self.is_host = True
        self.player_color = 'w'  # L'hôte joue les blancs
        self.network = NetworkHost(self, port)
        self.network.start()
        return True
    
    def join_game(self, host, port=5555):
        """Rejoint un jeu en tant que client"""
        self.is_host = False
        self.player_color = 'b'  # Le client joue les noirs
        self.network = NetworkClient(self, host, port)
        connected = self.network.connect()
        if connected:
            self.network.start()
        return connected

# Fonction principale
def main():
    """Fonction principale du jeu"""
    game = ChessGame()
    clock = pygame.time.Clock()
    running = True
    menu_active = True

    # Police pour le menu
    font = pygame.font.SysFont('Arial', 36)

    while running:
        # Menu principal
        while menu_active and running:
            WINDOW.fill(LIGHT_SQUARE)
            
            # Titre
            title = font.render("Jeu d'Échecs Multijoueur", True, BLACK)
            WINDOW.blit(title, (WIDTH//2 - title.get_width()//2, 100))

            # Bouton Héberger
            host_button = pygame.Rect(WIDTH//2 - 100, 200, 200, 50)
            pygame.draw.rect(WINDOW, DARK_SQUARE, host_button)
            host_text = font.render("Héberger", True, WHITE)
            WINDOW.blit(host_text, (WIDTH//2 - host_text.get_width()//2, 210))

            # Bouton Rejoindre
            join_button = pygame.Rect(WIDTH//2 - 100, 300, 200, 50)
            pygame.draw.rect(WINDOW, DARK_SQUARE, join_button)
            join_text = font.render("Rejoindre", True, WHITE)
            WINDOW.blit(join_text, (WIDTH//2 - join_text.get_width()//2, 310))

            # Bouton Quitter
            quit_button = pygame.Rect(WIDTH//2 - 100, 400, 200, 50)
            pygame.draw.rect(WINDOW, DARK_SQUARE, quit_button)
            quit_text = font.render("Quitter", True, WHITE)
            WINDOW.blit(quit_text, (WIDTH//2 - quit_text.get_width()//2, 410))

            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    menu_active = False
                
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_pos = pygame.mouse.get_pos()
                    
                    # Héberger une partie
                    if host_button.collidepoint(mouse_pos):
                        if game.host_game():
                            menu_active = False
                    
                    # Rejoindre une partie
                    elif join_button.collidepoint(mouse_pos):
                        # Demande l'adresse IP de l'hôte
                        input_active = True
                        host_ip = ""
                        input_font = pygame.font.SysFont('Arial', 30)
                        while input_active and running:
                            WINDOW.fill(LIGHT_SQUARE)
                            
                            # Instructions
                            prompt = font.render("Entrez l'adresse IP de l'hôte:", True, BLACK)
                            WINDOW.blit(prompt, (WIDTH//2 - prompt.get_width()//2, 200))
                            
                            # Champ de saisie
                            input_rect = pygame.Rect(WIDTH//2 - 150, 250, 300, 40)
                            pygame.draw.rect(WINDOW, WHITE, input_rect)
                            pygame.draw.rect(WINDOW, BLACK, input_rect, 2)
                            
                            # Texte saisi
                            input_surface = input_font.render(host_ip, True, BLACK)
                            WINDOW.blit(input_surface, (input_rect.x + 5, input_rect.y + 5))
                            
                            # Bouton Valider
                            validate_button = pygame.Rect(WIDTH//2 - 100, 320, 200, 50)
                            pygame.draw.rect(WINDOW, DARK_SQUARE, validate_button)
                            validate_text = font.render("Valider", True, WHITE)
                            WINDOW.blit(validate_text, (WIDTH//2 - validate_text.get_width()//2, 330))
                            
                            pygame.display.flip()
                            
                            for input_event in pygame.event.get():
                                if input_event.type == pygame.QUIT:
                                    input_active = False
                                    running = False
                                
                                if input_event.type == pygame.KEYDOWN:
                                    if input_event.key == pygame.K_RETURN:
                                        input_active = False
                                    elif input_event.key == pygame.K_BACKSPACE:
                                        host_ip = host_ip[:-1]
                                    else:
                                        host_ip += input_event.unicode
                                
                                if input_event.type == pygame.MOUSEBUTTONDOWN:
                                    if validate_button.collidepoint(pygame.mouse.get_pos()):
                                        input_active = False
                        
                        if running and host_ip:
                            if game.join_game(host_ip):
                                menu_active = False
                    
                    # Quitter
                    elif quit_button.collidepoint(mouse_pos):
                        running = False
                        menu_active = False

            clock.tick(30)

        # Boucle principale du jeu
        while not menu_active and running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:  # Clic gauche
                        game.select_piece(event.pos)
                
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        # Retour au menu
                        if game.network:
                            game.network.stop()
                            game.network = None
                        menu_active = True
                        game = ChessGame()  # Réinitialise le jeu

            # Dessine le plateau
            game.draw_board(WINDOW)
            pygame.display.flip()
            clock.tick(60)

    # Nettoyage
    if game.network:
        game.network.stop()
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()