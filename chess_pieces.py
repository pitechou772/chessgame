# chess_pieces.py

class ChessPiece:
    """Classe de base pour toutes les pièces d'échecs"""
    def __init__(self, color, position):
        self.color = color  # 'w' pour blanc, 'b' pour noir
        self.position = position  # (row, col)
        self.has_moved = False
    
    def get_moves(self, board):
        """Méthode à implémenter dans les sous-classes"""
        return []
    
    @property
    def notation(self):
        """Renvoie la notation de la pièce (ex: 'wK', 'bQ')"""
        return f"{self.color}{self.type_char}"

class Pawn(ChessPiece):
    type_char = 'p'
    
    def get_moves(self, board):
        """Renvoie tous les mouvements possibles pour un pion"""
        row, col = self.position
        moves = []
        direction = 1 if self.color == 'b' else -1
        
        # Avancer d'une case
        if 0 <= row + direction < 8 and board[row + direction][col] == '--':
            moves.append((row + direction, col))
            
            # Avancer de deux cases depuis la position initiale
            if not self.has_moved and board[row + 2*direction][col] == '--':
                moves.append((row + 2*direction, col))
        
        # Capturer en diagonale
        for offset in [-1, 1]:
            if 0 <= row + direction < 8 and 0 <= col + offset < 8:
                target = board[row + direction][col + offset]
                if target != '--' and target[0] != self.color:
                    moves.append((row + direction, col + offset))
        
        # Note: La prise en passant sera gérée séparément par le gestionnaire de jeu
        return moves

class Rook(ChessPiece):
    type_char = 'R'
    
    def get_moves(self, board):
        """Renvoie tous les mouvements possibles pour une tour"""
        row, col = self.position
        moves = []
        
        # Directions: haut, droite, bas, gauche
        directions = [(-1, 0), (0, 1), (1, 0), (0, -1)]
        for dr, dc in directions:
            for i in range(1, 8):
                r, c = row + i*dr, col + i*dc
                if not (0 <= r < 8 and 0 <= c < 8):
                    break
                target = board[r][c]
                if target == '--':
                    moves.append((r, c))
                elif target[0] != self.color:
                    moves.append((r, c))
                    break
                else:
                    break
        
        return moves

class Knight(ChessPiece):
    type_char = 'N'
    
    def get_moves(self, board):
        """Renvoie tous les mouvements possibles pour un cavalier"""
        row, col = self.position
        moves = []
        
        knight_moves = [
            (row-2, col-1), (row-2, col+1),
            (row-1, col-2), (row-1, col+2),
            (row+1, col-2), (row+1, col+2),
            (row+2, col-1), (row+2, col+1)
        ]
        
        for move in knight_moves:
            r, c = move
            if 0 <= r < 8 and 0 <= c < 8:
                target = board[r][c]
                if target == '--' or target[0] != self.color:
                    moves.append((r, c))
        
        return moves

class Bishop(ChessPiece):
    type_char = 'B'
    
    def get_moves(self, board):
        """Renvoie tous les mouvements possibles pour un fou"""
        row, col = self.position
        moves = []
        
        # Directions: diagonales
        directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
        for dr, dc in directions:
            for i in range(1, 8):
                r, c = row + i*dr, col + i*dc
                if not (0 <= r < 8 and 0 <= c < 8):
                    break
                target = board[r][c]
                if target == '--':
                    moves.append((r, c))
                elif target[0] != self.color:
                    moves.append((r, c))
                    break
                else:
                    break
        
        return moves

class Queen(ChessPiece):
    type_char = 'Q'
    
    def get_moves(self, board):
        """Renvoie tous les mouvements possibles pour une reine"""
        row, col = self.position
        moves = []
        
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
                target = board[r][c]
                if target == '--':
                    moves.append((r, c))
                elif target[0] != self.color:
                    moves.append((r, c))
                    break
                else:
                    break
        
        return moves

class King(ChessPiece):
    type_char = 'K'
    
    def get_moves(self, board):
        """Renvoie tous les mouvements possibles pour un roi"""
        row, col = self.position
        moves = []
        
        # Directions: toutes les cases adjacentes
        directions = [
            (-1, -1), (-1, 0), (-1, 1),
            (0, -1),           (0, 1),
            (1, -1),  (1, 0),  (1, 1)
        ]
        for dr, dc in directions:
            r, c = row + dr, col + dc
            if 0 <= r < 8 and 0 <= c < 8:
                target = board[r][c]
                if target == '--' or target[0] != self.color:
                    moves.append((r, c))
        
        # Note: Le roque sera géré séparément par le gestionnaire de jeu
        return moves

def create_piece(piece_code, position):
    """Crée une instance de pièce en fonction de son code"""
    if not piece_code or piece_code == '--':
        return None
    
    color = piece_code[0]
    piece_type = piece_code[1]
    
    piece_classes = {
        'p': Pawn,
        'R': Rook,
        'N': Knight,
        'B': Bishop,
        'Q': Queen,
        'K': King
    }
    
    if piece_type in piece_classes:
        return piece_classes[piece_type](color, position)
    
    return None