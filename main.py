import pygame
import sys
import time
import socket
import threading
import pickle
from chess_pieces import create_piece
from chess_clock import ChessClock
from network import NetworkHost, NetworkClient
from chatsyteme import ChatSystem

pygame.init()
WIDTH, HEIGHT = (600, 600)
SQUARE_SIZE = WIDTH // 8
WINDOW = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Jeu d'Échecs Multijoueur")
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (128, 128, 128)
LIGHT_SQUARE = (240, 217, 181)
DARK_SQUARE = (181, 136, 99)
HIGHLIGHT = (186, 202, 68)
MOVE_HIGHLIGHT = (106, 135, 77, 150)
CHECK_HIGHLIGHT = (214, 85, 80, 200)

def load_images():
    """Charge les images des pièces d'échecs depuis le dossier 'images'"""
    pieces = ['wp', 'wR', 'wN', 'wB', 'wQ', 'wK', 'bp', 'bR', 'bN', 'bB', 'bQ', 'bK']
    images = {}
    for piece in pieces:
        try:
            images[piece] = pygame.transform.scale(pygame.image.load(f'images/{piece}.png'), (SQUARE_SIZE, SQUARE_SIZE))
        except:
            print(f"Impossible de charger l'image pour {piece}. Utilisation d'une représentation simple.")
            images[piece] = None
    return images

class ChessGame:
    def __init__(self):
        """Initialise une nouvelle partie d'échecs"""
        self.board = self.create_board()
        self.piece_objects = self.create_piece_objects()  # Crée les objets de pièces
        self.selected_piece = None
        self.turn = 'w'
        self.valid_moves = []
        self.images = load_images()
        self.network = None
        self.is_host = False
        self.game_id = None
        self.player_color = None
        self.move_history = []
        self.king_positions = {'w': (7, 4), 'b': (0, 4)}
        self.in_check = {'w': False, 'b': False}
        self.game_status = 'Playing'
        self.castling_rights = {'w': {'kingside': True, 'queenside': True}, 'b': {'kingside': True, 'queenside': True}}
        self.en_passant_target = None
        self.clock = None
        self.time_mode = 'Standard'
        self.game_started = False
        self.chat = ChatSystem()

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
    
    def create_piece_objects(self):
        """Crée les objets de pièces à partir du tableau"""
        piece_objects = [[None for _ in range(8)] for _ in range(8)]
        for row in range(8):
            for col in range(8):
                piece_code = self.board[row][col]
                if piece_code != '--':
                    piece_objects[row][col] = create_piece(piece_code, (row, col))
        return piece_objects
    
    def update_piece_objects(self):
        """Met à jour les objets de pièces après un mouvement"""
        for row in range(8):
            for col in range(8):
                piece_code = self.board[row][col]
                if piece_code != '--' and self.piece_objects[row][col] is None:
                    self.piece_objects[row][col] = create_piece(piece_code, (row, col))
                elif piece_code == '--':
                    self.piece_objects[row][col] = None
                elif self.piece_objects[row][col] and self.piece_objects[row][col].notation != piece_code:
                    self.piece_objects[row][col] = create_piece(piece_code, (row, col))

    def draw_board(self, window):
        """Dessine le plateau et les pièces"""
        for row in range(8):
            for col in range(8):
                color = LIGHT_SQUARE if (row + col) % 2 == 0 else DARK_SQUARE
                pygame.draw.rect(window, color, pygame.Rect(col * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))
                piece = self.board[row][col]
                if piece != '--' and self.images.get(piece):
                    window.blit(self.images[piece], pygame.Rect(col * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))
                elif piece != '--':
                    font = pygame.font.SysFont('Arial', 30)
                    text = font.render(piece, True, WHITE if piece[0] == 'b' else BLACK)
                    window.blit(text, (col * SQUARE_SIZE + 15, row * SQUARE_SIZE + 15))
                
                if self.selected_piece == (row, col):
                    pygame.draw.rect(window, HIGHLIGHT, pygame.Rect(col * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE), 3)
                
                if (row, col) in self.valid_moves:
                    if self.board[row][col] != '--':
                        pygame.draw.circle(window, MOVE_HIGHLIGHT, (col * SQUARE_SIZE + SQUARE_SIZE // 2, row * SQUARE_SIZE + SQUARE_SIZE // 2), SQUARE_SIZE // 2 - 5, 3)
                    else:
                        pygame.draw.circle(window, MOVE_HIGHLIGHT, (col * SQUARE_SIZE + SQUARE_SIZE // 2, row * SQUARE_SIZE + SQUARE_SIZE // 2), SQUARE_SIZE // 6)
        
        # Afficher les rois en échec
        for color in ['w', 'b']:
            if self.in_check[color]:
                king_row, king_col = self.king_positions[color]
                king_rect = pygame.Rect(king_col * SQUARE_SIZE, king_row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE)
                s = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
                s.fill(CHECK_HIGHLIGHT)
                window.blit(s, king_rect)
        
        # Afficher le statut de la partie
        if self.game_status != 'Playing':
            status_surface = pygame.Surface((WIDTH, 50), pygame.SRCALPHA)
            status_surface.fill((0, 0, 0, 180))
            window.blit(status_surface, (0, HEIGHT // 2 - 25))
            font = pygame.font.SysFont('Arial', 36)
            text = font.render(self.game_status, True, WHITE)
            window.blit(text, (WIDTH // 2 - text.get_width() // 2, HEIGHT // 2 - text.get_height() // 2))
        
        # Afficher l'horloge
        if self.clock:
            clock_font = pygame.font.SysFont('Arial', 24)
            self.clock.draw(window, clock_font, WIDTH, HEIGHT)
            
        # Afficher le chat
        if hasattr(self, 'chat') and self.chat.chat_visible:
            small_font = pygame.font.SysFont('Arial', 16)
            self.chat.draw(window, small_font, WIDTH, HEIGHT)

    def select_piece(self, pos):
        """Gère la sélection d'une pièce et son déplacement"""
        if self.game_status != 'Playing':
            return
            
        col, row = (pos[0] // SQUARE_SIZE, pos[1] // SQUARE_SIZE)
        
        # Vérifier si c'est le tour du joueur
        if self.player_color and self.turn != self.player_color:
            return
            
        if self.selected_piece:
            # Si on clique sur la même pièce, désélectionner
            if self.selected_piece == (row, col):
                self.selected_piece = None
                self.valid_moves = []
                return
                
            # Si on clique sur une case valide, déplacer la pièce
            if (row, col) in self.valid_moves:
                self.move_piece(self.selected_piece, (row, col))
                self.selected_piece = None
                self.valid_moves = []
                return
                
            # Si on clique sur une autre pièce de même couleur, la sélectionner
            piece = self.board[row][col]
            if piece != '--' and piece[0] == self.turn:
                self.selected_piece = (row, col)
                self.valid_moves = self.get_valid_moves((row, col))
                return
                
            # Sinon, désélectionner
            self.selected_piece = None
            self.valid_moves = []
        else:
            # Sélectionner une pièce si elle est de la bonne couleur
            piece = self.board[row][col]
            if piece != '--' and piece[0] == self.turn:
                self.selected_piece = (row, col)
                self.valid_moves = self.get_valid_moves((row, col))

    def get_piece_moves(self, pos):
        """Obtient tous les mouvements possibles pour une pièce spécifique en utilisant les objets de pièces"""
        row, col = pos
        piece_obj = self.piece_objects[row][col]
        
        if not piece_obj:
            return []
            
        # Utilise la méthode get_moves définie dans chess_pieces.py
        return piece_obj.get_moves(self.board)

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
        
        for start_pos, end_pos in self.get_all_possible_moves(opponent_color):
            if end_pos == (king_row, king_col):
                return True
        return False

    def get_valid_moves(self, pos):
        """Obtient tous les mouvements valides pour une pièce, en tenant compte de l'échec"""
        row, col = pos
        piece = self.board[row][col]
        color = piece[0]
        possible_moves = self.get_piece_moves(pos)
        valid_moves = []
        
        for move in possible_moves:
            end_row, end_col = move
            captured_piece = self.board[end_row][end_col]
            
            # Sauvegarder l'état actuel
            king_pos = self.king_positions[color]
            
            # Si c'est le roi qui bouge, mettre à jour sa position
            if piece[1] == 'K':
                self.king_positions[color] = (end_row, end_col)
                
            # Simuler le mouvement
            self.board[end_row][end_col] = piece
            self.board[row][col] = '--'
            
            # Vérifier si le roi est en échec après ce mouvement
            in_check = self.is_in_check(color)
            
            # Restaurer l'état précédent
            self.board[row][col] = piece
            self.board[end_row][end_col] = captured_piece
            
            if piece[1] == 'K':
                self.king_positions[color] = king_pos
                
            # Si le mouvement ne met pas le roi en échec, il est valide
            if not in_check:
                valid_moves.append(move)
                
        return valid_moves

    def move_piece(self, start, end):
        """Déplace une pièce et gère les règles spéciales (promotion, roque, etc.)"""
        start_row, start_col = start
        end_row, end_col = end
        moved_piece = self.board[start_row][start_col]
        captured_piece = self.board[end_row][end_col]
        
        # Enregistrer le mouvement dans l'historique
        self.move_history.append((start, end, moved_piece, captured_piece))
        
        # Gérer le roque
        if moved_piece[1] == 'K' and abs(start_col - end_col) == 2:
            if end_col > start_col:  # Roque côté roi
                self.board[end_row][end_col - 1] = self.board[end_row][7]
                self.board[end_row][7] = '--'
            else:  # Roque côté dame
                self.board[end_row][end_col + 1] = self.board[end_row][0]
                self.board[end_row][0] = '--'
        
        # Gérer la prise en passant
        if moved_piece[1] == 'p' and start_col != end_col and captured_piece == '--':
            self.board[start_row][end_col] = '--'
        
        # Réinitialiser la cible de prise en passant
        self.en_passant_target = None
        
        # Définir une nouvelle cible de prise en passant si un pion avance de deux cases
        if moved_piece[1] == 'p' and abs(start_row - end_row) == 2:
            self.en_passant_target = (start_row + (end_row - start_row) // 2, start_col)
        
        # Déplacer la pièce
        self.board[end_row][end_col] = moved_piece
        self.board[start_row][start_col] = '--'
        
        # Mettre à jour les objets de pièces
        self.update_piece_objects()
        
        # Promotion du pion
        if moved_piece[1] == 'p' and (end_row == 0 or end_row == 7):
            self.board[end_row][end_col] = moved_piece[0] + 'Q'
            self.update_piece_objects()
        
        # Mettre à jour la position du roi
        if moved_piece[1] == 'K':
            self.king_positions[moved_piece[0]] = (end_row, end_col)
        
        # Mettre à jour les droits de roque
        if moved_piece[1] == 'K':
            self.castling_rights[moved_piece[0]]['kingside'] = False
            self.castling_rights[moved_piece[0]]['queenside'] = False
        elif moved_piece[1] == 'R':
            if start_col == 7:  # Tour côté roi
                self.castling_rights[moved_piece[0]]['kingside'] = False
            elif start_col == 0:  # Tour côté dame
                self.castling_rights[moved_piece[0]]['queenside'] = False
        
        # Changer de tour
        self.turn = 'b' if self.turn == 'w' else 'w'
        
        # Gérer l'horloge
        if self.clock and self.game_started:
            self.clock.switch()
        
        # Vérifier l'échec
        self.in_check['w'] = self.is_in_check('w')
        self.in_check['b'] = self.is_in_check('b')
        
        # Vérifier fin de partie
        self.check_game_over()
        
        # Envoyer le mouvement et l'état du jeu via le réseau
        if self.network:
            self.network.send_move(start, end)
            time.sleep(0.1)
            self.network.send_game_state()

    def check_game_over(self):
        """Vérifie si la partie est terminée (échec et mat, pat ou temps écoulé)"""
        # Vérifier si le temps est écoulé
        if self.clock and self.clock.game_over:
            winner = 'Blancs' if self.clock.timeout_color == 'b' else 'Noirs'
            self.game_status = f'Temps écoulé! {winner} gagnent!'
            return
        
        # Vérifier si le joueur actuel a des mouvements légaux
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
        
        # Si aucun mouvement légal, c'est soit échec et mat soit pat
        if not has_valid_moves:
            if self.in_check[self.turn]:
                winner = 'Blancs' if self.turn == 'b' else 'Noirs'
                self.game_status = f'Échec et mat! {winner} gagnent!'
            else:
                self.game_status = 'Pat! Match nul!'

    def setup_clock(self, time_mode='Standard'):
        """Configure l'horloge selon le mode de temps choisi"""
        self.time_mode = time_mode
        if time_mode == 'Blitz':
            self.clock = ChessClock(180, 2)  # 3 minutes + 2 secondes par coup
        elif time_mode == 'Rapide':
            self.clock = ChessClock(600, 5)  # 10 minutes + 5 secondes par coup
        elif time_mode == 'Standard':
            self.clock = ChessClock(1800, 0)  # 30 minutes sans incrément
        else:
            self.clock = ChessClock(600, 0)  # 10 minutes par défaut
        self.game_started = False

    def start_game(self):
        """Démarre la partie et l'horloge"""
        if self.clock and (not self.game_started):
            self.clock.start('w')
            self.game_started = True

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


def main():
    """Fonction principale du jeu"""
    game = ChessGame()
    clock = pygame.time.Clock()
    running = True
    menu_active = True
    
    # Polices
    font = pygame.font.SysFont('Arial', 36)
    small_font = pygame.font.SysFont('Arial', 24)
    
    while running:
        # Menu principal
        while menu_active and running:
            WINDOW.fill(LIGHT_SQUARE)
            
            # Titre
            title = font.render("Jeu d'Échecs Multijoueur", True, BLACK)
            WINDOW.blit(title, (WIDTH // 2 - title.get_width() // 2, 100))
            
            # Bouton pour héberger une partie
            host_button = pygame.Rect(WIDTH // 2 - 100, 200, 200, 50)
            pygame.draw.rect(WINDOW, DARK_SQUARE, host_button)
            host_text = font.render('Héberger', True, WHITE)
            WINDOW.blit(host_text, (WIDTH // 2 - host_text.get_width() // 2, 210))
            
            # Bouton pour rejoindre une partie
            join_button = pygame.Rect(WIDTH // 2 - 100, 300, 200, 50)
            pygame.draw.rect(WINDOW, DARK_SQUARE, join_button)
            join_text = font.render('Rejoindre', True, WHITE)
            WINDOW.blit(join_text, (WIDTH // 2 - join_text.get_width() // 2, 310))
            
            # Bouton pour quitter
            quit_button = pygame.Rect(WIDTH // 2 - 100, 400, 200, 50)
            pygame.draw.rect(WINDOW, DARK_SQUARE, quit_button)
            quit_text = font.render('Quitter', True, WHITE)
            WINDOW.blit(quit_text, (WIDTH // 2 - quit_text.get_width() // 2, 410))
            
            pygame.display.flip()
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    menu_active = False
                    
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_pos = pygame.mouse.get_pos()
                    
                    # Héberger une partie
                    if host_button.collidepoint(mouse_pos):
                        time_selection_active = True
                        selected_mode = None
                        
                        # Menu de sélection du mode de temps
                        while time_selection_active and running:
                            WINDOW.fill(LIGHT_SQUARE)
                            
                            mode_title = font.render('Choisissez un mode de jeu', True, BLACK)
                            WINDOW.blit(mode_title, (WIDTH // 2 - mode_title.get_width() // 2, 100))
                            
                            # Bouton Blitz
                            blitz_button = pygame.Rect(WIDTH // 2 - 100, 200, 200, 50)
                            pygame.draw.rect(WINDOW, DARK_SQUARE, blitz_button)
                            blitz_text = font.render('Blitz', True, WHITE)
                            WINDOW.blit(blitz_text, (WIDTH // 2 - blitz_text.get_width() // 2, 210))
                            blitz_desc = small_font.render('3min + 2sec', True, BLACK)
                            WINDOW.blit(blitz_desc, (WIDTH // 2 - blitz_desc.get_width() // 2, 260))
                            
                            # Bouton Rapide
                            rapid_button = pygame.Rect(WIDTH // 2 - 100, 300, 200, 50)
                            pygame.draw.rect(WINDOW, DARK_SQUARE, rapid_button)
                            rapid_text = font.render('Rapide', True, WHITE)
                            WINDOW.blit(rapid_text, (WIDTH // 2 - rapid_text.get_width() // 2, 310))
                            rapid_desc = small_font.render('10min + 5sec', True, BLACK)
                            WINDOW.blit(rapid_desc, (WIDTH // 2 - rapid_desc.get_width() // 2, 360))
                            
                            # Bouton Standard
                            standard_button = pygame.Rect(WIDTH // 2 - 100, 400, 200, 50)
                            pygame.draw.rect(WINDOW, DARK_SQUARE, standard_button)
                            standard_text = font.render('Standard', True, WHITE)
                            WINDOW.blit(standard_text, (WIDTH // 2 - standard_text.get_width() // 2, 410))
                            standard_desc = small_font.render('30min', True, BLACK)
                            WINDOW.blit(standard_desc, (WIDTH // 2 - standard_desc.get_width() // 2, 460))
                            
                            # Bouton Retour
                            back_button = pygame.Rect(WIDTH // 2 - 100, 500, 200, 50)
                            pygame.draw.rect(WINDOW, GRAY, back_button)
                            back_text = font.render('Retour', True, WHITE)
                            WINDOW.blit(back_text, (WIDTH // 2 - back_text.get_width() // 2, 510))
                            
                            pygame.display.flip()
                            
                            for mode_event in pygame.event.get():
                                if mode_event.type == pygame.QUIT:
                                    time_selection_active = False
                                    running = False
                                if mode_event.type == pygame.MOUSEBUTTONDOWN:
                                    mode_mouse_pos = pygame.mouse.get_pos()
                                    if blitz_button.collidepoint(mode_mouse_pos):
                                        selected_mode = 'Blitz'
                                        time_selection_active = False
                                    elif rapid_button.collidepoint(mode_mouse_pos):
                                        selected_mode = 'Rapide'
                                        time_selection_active = False
                                    elif standard_button.collidepoint(mode_mouse_pos):
                                        selected_mode = 'Standard'
                                        time_selection_active = False
                                    elif back_button.collidepoint(mode_mouse_pos):
                                        time_selection_active = False
                                        selected_mode = None
                            clock.tick(30)
                            
                        # Démarrer le jeu en tant qu'hôte avec le mode sélectionné
                        if selected_mode:
                            game.setup_clock(selected_mode)
                            if game.host_game():
                                menu_active = False
                    
                    # Rejoindre une partie
                    elif join_button.collidepoint(mouse_pos):
                        input_active = True
                        host_ip = ''
                        input_font = pygame.font.SysFont('Arial', 30)
                        
                        # Saisie de l'adresse IP
                        while input_active and running:
                            WINDOW.fill(LIGHT_SQUARE)
                            
                            prompt = font.render("Entrez l'adresse IP de l'hôte:", True, BLACK)
                            WINDOW.blit(prompt, (WIDTH // 2 - prompt.get_width() // 2, 200))
                            
                            input_rect = pygame.Rect(WIDTH // 2 - 150, 250, 300, 40)
                            pygame.draw.rect(WINDOW, WHITE, input_rect)
                            pygame.draw.rect(WINDOW, BLACK, input_rect, 2)
                            
                            input_surface = input_font.render(host_ip, True, BLACK)
                            WINDOW.blit(input_surface, (input_rect.x + 5, input_rect.y + 5))
                            
                            validate_button = pygame.Rect(WIDTH // 2 - 100, 320, 200, 50)
                            pygame.draw.rect(WINDOW, DARK_SQUARE, validate_button)
                            validate_text = font.render('Valider', True, WHITE)
                            WINDOW.blit(validate_text, (WIDTH // 2 - validate_text.get_width() // 2, 330))
                            
                            back_button = pygame.Rect(WIDTH // 2 - 100, 400, 200, 50)
                            pygame.draw.rect(WINDOW, GRAY, back_button)
                            back_text = font.render('Retour', True, WHITE)
                            WINDOW.blit(back_text, (WIDTH // 2 - back_text.get_width() // 2, 410))
                            
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
                                    mouse_pos = pygame.mouse.get_pos()
                                    if validate_button.collidepoint(mouse_pos):
                                        input_active = False
                                    elif back_button.collidepoint(mouse_pos):
                                        input_active = False
                                        host_ip = ''
                        
                        # Rejoindre la partie avec l'IP saisie
                        if running and host_ip:
                            if game.join_game(host_ip):
                                menu_active = False
                    
                    # Quitter le jeu
                    elif quit_button.collidepoint(mouse_pos):
                        running = False
                        menu_active = False
            
            clock.tick(30)
  
        while not menu_active and running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    
                # Traite les événements du chat d'abord
                if game.network and hasattr(game, 'chat'):
                    if game.chat.handle_event(event, game.network):
                        continue  # L'événement a été traité par le chat
                    
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        game.select_piece(event.pos)
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        if game.network:
                            game.network.stop()
                            game.network = None
                        if game.clock:
                            game.clock.stop()
                        menu_active = True
                    elif event.key == pygame.K_TAB:  # Touche pour activer/désactiver le chat
                        if hasattr(game, 'chat'):
                            game.chat.chat_visible = not game.chat.chat_visible
        game.draw_board(WINDOW)
        pygame.display.flip()
        clock.tick(60)
        game.network.stop()
    pygame.quit()
    sys.exit()
if __name__ == '__main__':
    main()