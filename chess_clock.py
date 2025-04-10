# chess_clock.py
import pygame
import time
from constants import WIDTH, HEIGHT, WHITE, BLACK

class ChessClock:
    def __init__(self, initial_time, increment=0):
        """
        Initialise une horloge d'échecs
        :param initial_time: Temps initial en secondes
        :param increment: Incrément de temps après chaque coup en secondes
        """
        self.time_left = {'w': initial_time, 'b': initial_time}
        self.increment = increment
        self.running = False
        self.active_color = None
        self.last_update = 0
        self.game_over = False
        self.timeout_color = None
    
    def start(self, starting_color='w'):
        """Démarre l'horloge"""
        self.running = True
        self.active_color = starting_color
        self.last_update = time.time()
    
    def stop(self):
        """Arrête l'horloge"""
        self.running = False
    
    def switch(self):
        """Change le joueur actif et applique l'incrément"""
        if not self.running:
            return
        
        current_time = time.time()
        elapsed = current_time - self.last_update
        self.time_left[self.active_color] -= elapsed
        
        # Vérifie si le temps est écoulé
        if self.time_left[self.active_color] <= 0:
            self.time_left[self.active_color] = 0
            self.game_over = True
            self.timeout_color = self.active_color
            self.running = False
            return
        
        # Ajoute l'incrément
        self.time_left[self.active_color] += self.increment
        
        # Change le joueur actif
        self.active_color = 'b' if self.active_color == 'w' else 'w'
        self.last_update = current_time
    
    def update(self):
        """Met à jour le temps restant"""
        if not self.running or self.game_over:
            return
        
        current_time = time.time()
        elapsed = current_time - self.last_update
        self.time_left[self.active_color] -= elapsed
        self.last_update = current_time
        
        # Vérifie si le temps est écoulé
        if self.time_left[self.active_color] <= 0:
            self.time_left[self.active_color] = 0
            self.game_over = True
            self.timeout_color = self.active_color
            self.running = False
    
    def format_time(self, seconds):
        """Formate le temps en minutes:secondes"""
        minutes = int(seconds) // 60
        seconds = int(seconds) % 60
        return f"{minutes:02d}:{seconds:02d}"
    
    def draw(self, window, font, width, height):
        """Dessine l'horloge à l'écran"""
        self.update()
        
        # Dessine le fond des horloges
        clock_height = 30
        black_clock_rect = pygame.Rect(0, 0, width, clock_height)
        white_clock_rect = pygame.Rect(0, height - clock_height, width, clock_height)
        
        pygame.draw.rect(window, (50, 50, 50), black_clock_rect)
        pygame.draw.rect(window, (50, 50, 50), white_clock_rect)
        
        # Surligne l'horloge active
        if self.active_color == 'b':
            pygame.draw.rect(window, (70, 70, 70), black_clock_rect, 3)
        elif self.active_color == 'w':
            pygame.draw.rect(window, (70, 70, 70), white_clock_rect, 3)
        
        # Affiche le temps restant
        black_time = font.render(self.format_time(self.time_left['b']), True, WHITE)
        white_time = font.render(self.format_time(self.time_left['w']), True, WHITE)
        
        window.blit(black_time, (width//2 - black_time.get_width()//2, 5))
        window.blit(white_time, (width//2 - white_time.get_width()//2, height - clock_height + 5))