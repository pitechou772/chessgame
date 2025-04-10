import pygame
import time

class ChessClock:
    def __init__(self, initial_time_seconds=600, increment_seconds=0):
        """
        Initialise une horloge d'échecs
        
        Args:
            initial_time_seconds: Temps initial en secondes (10 minutes par défaut)
            increment_seconds: Incrément de temps en secondes après chaque coup (0 par défaut)
        """
        self.white_time = initial_time_seconds
        self.black_time = initial_time_seconds
        self.increment = increment_seconds
        self.active_color = None  # Aucune horloge active au départ
        self.last_update = 0
        self.is_running = False
        self.game_over = False
        self.timeout_color = None

    def start(self, starting_color='w'):
        """Démarre l'horloge pour la couleur spécifiée"""
        self.active_color = starting_color
        self.last_update = time.time()
        self.is_running = True

    def stop(self):
        """Arrête l'horloge"""
        self.update()
        self.is_running = False
        self.active_color = None

    def pause(self):
        """Met en pause l'horloge sans changer le tour"""
        self.update()
        self.is_running = False

    def resume(self):
        """Reprend l'horloge pour le joueur actuel"""
        if self.active_color:
            self.last_update = time.time()
            self.is_running = True

    def switch(self):
        """Change le tour et ajoute l'incrément au joueur qui vient de jouer"""
        if not self.is_running or self.game_over:
            return

        self.update()
        
        # Ajouter l'incrément au joueur qui vient de jouer
        if self.active_color == 'w':
            self.white_time += self.increment
        else:
            self.black_time += self.increment
        
        # Changer le tour
        self.active_color = 'b' if self.active_color == 'w' else 'w'
        self.last_update = time.time()

    def update(self):
        """Met à jour le temps restant pour le joueur actif"""
        if not self.is_running or not self.active_color or self.game_over:
            return

        current_time = time.time()
        elapsed = current_time - self.last_update
        self.last_update = current_time

        # Soustraire le temps écoulé
        if self.active_color == 'w':
            self.white_time -= elapsed
            if self.white_time <= 0:
                self.white_time = 0
                self.game_over = True
                self.timeout_color = 'w'
                self.is_running = False
        else:
            self.black_time -= elapsed
            if self.black_time <= 0:
                self.black_time = 0
                self.game_over = True
                self.timeout_color = 'b'
                self.is_running = False

    def get_time_str(self, color):
        """Retourne le temps restant formaté pour la couleur spécifiée"""
        seconds = self.white_time if color == 'w' else self.black_time
        
        minutes = int(seconds // 60)
        seconds = int(seconds % 60)
        
        # Si moins d'une minute, afficher au dixième de seconde près
        if minutes == 0 and seconds < 10:
            tenths = int((seconds % 1) * 10)
            return f"{seconds}.{tenths}"
        else:
            return f"{minutes:02}:{seconds:02}"

    def draw(self, window, font, width, height):
        """Dessine les horloges sur l'écran"""
        # Mise à jour du temps
        self.update()
        
        # Fond des horloges
        clock_height = 60
        white_rect = pygame.Rect(width - 100, height - 20 - clock_height, 80, clock_height)
        black_rect = pygame.Rect(20, 20, 80, clock_height)
        
        # Couleurs
        active_color = (220, 220, 220)
        inactive_color = (180, 180, 180)
        text_color = (0, 0, 0)
        
        # Dessine la boîte de l'horloge blanche
        white_bg_color = active_color if self.active_color == 'w' else inactive_color
        pygame.draw.rect(window, white_bg_color, white_rect)
        pygame.draw.rect(window, (0, 0, 0), white_rect, 2)
        
        # Dessine la boîte de l'horloge noire
        black_bg_color = active_color if self.active_color == 'b' else inactive_color
        pygame.draw.rect(window, black_bg_color, black_rect)
        pygame.draw.rect(window, (0, 0, 0), black_rect, 2)
        
        # Dessine le temps
        white_time_text = font.render(self.get_time_str('w'), True, text_color)
        black_time_text = font.render(self.get_time_str('b'), True, text_color)
        
        # Position du texte centré dans les rectangles
        white_text_pos = (white_rect.centerx - white_time_text.get_width() // 2, 
                         white_rect.centery - white_time_text.get_height() // 2)
        black_text_pos = (black_rect.centerx - black_time_text.get_width() // 2, 
                         black_rect.centery - black_time_text.get_height() // 2)
        
        window.blit(white_time_text, white_text_pos)
        window.blit(black_time_text, black_text_pos)
        
        # Si le temps est écoulé, afficher un message
        if self.game_over and self.timeout_color:
            timeout_msg = "Temps écoulé!"
            winner = "Noirs gagnent!" if self.timeout_color == 'w' else "Blancs gagnent!"
            
            timeout_surface = pygame.Surface((width, 50), pygame.SRCALPHA)
            timeout_surface.fill((0, 0, 0, 180))
            window.blit(timeout_surface, (0, height // 2 - 50))
            
            timeout_text = font.render(timeout_msg, True, (255, 255, 255))
            winner_text = font.render(winner, True, (255, 255, 255))
            
            window.blit(timeout_text, (width // 2 - timeout_text.get_width() // 2, height // 2 - 45))
            window.blit(winner_text, (width // 2 - winner_text.get_width() // 2, height // 2 - 15))