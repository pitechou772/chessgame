import pygame
import pickle
import socket
import threading
import time

# Première étape: Ajoutons une classe ChatSystem qui gérera les messages
class ChatSystem:
    def __init__(self, max_messages=10):
        self.messages = []
        self.max_messages = max_messages
        self.input_text = ""
        self.input_active = False
        self.chat_visible = True
        
    def add_message(self, user, message):
        """Ajoute un message au système de chat"""
        self.messages.append((user, message))
        # Garde seulement les derniers messages
        if len(self.messages) > self.max_messages:
            self.messages.pop(0)
    
    def draw(self, window, font, width, height):
        """Dessine l'interface de chat"""
        if not self.chat_visible:
            # Affiche juste un bouton pour montrer le chat
            chat_btn = pygame.Rect(width - 80, height - 30, 70, 25)
            pygame.draw.rect(window, (70, 70, 70), chat_btn)
            btn_text = font.render("Chat", True, (255, 255, 255))
            window.blit(btn_text, (width - 65, height - 28))
            return
            
        # Dessine la zone de chat en bas de l'écran
        chat_height = min(200, height * 0.25)
        chat_surface = pygame.Surface((width, chat_height), pygame.SRCALPHA)
        chat_surface.fill((0, 0, 0, 180))  # Semi-transparent
        window.blit(chat_surface, (0, height - chat_height))
        
        # Dessine les messages
        y_offset = height - chat_height + 10
        for user, msg in self.messages:
            message_text = font.render(f"{user}: {msg}", True, (255, 255, 255))
            window.blit(message_text, (10, y_offset))
            y_offset += 20
        
        # Dessine la zone de saisie
        input_rect = pygame.Rect(10, height - 30, width - 90, 25)
        pygame.draw.rect(window, (255, 255, 255), input_rect)
        pygame.draw.rect(window, (0, 0, 0), input_rect, 1)
        
        # Affiche le texte en cours de saisie
        input_surface = font.render(self.input_text, True, (0, 0, 0))
        window.blit(input_surface, (input_rect.x + 5, input_rect.y + 3))
        
        # Bouton pour cacher le chat
        hide_btn = pygame.Rect(width - 80, height - 30, 70, 25)
        pygame.draw.rect(window, (70, 70, 70), hide_btn)
        btn_text = font.render("Cacher", True, (255, 255, 255))
        window.blit(btn_text, (width - 65, height - 28))
        
        # Si l'entrée est active, affiche un curseur
        if self.input_active:
            cursor_x = input_rect.x + 5 + input_surface.get_width()
            cursor_y = input_rect.y + 3
            cursor_height = input_surface.get_height()
            pygame.draw.line(window, (0, 0, 0), (cursor_x, cursor_y), 
                            (cursor_x, cursor_y + cursor_height), 2)

    def handle_event(self, event, network):
        """Gère les événements liés au chat"""
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()
            window_width, window_height = pygame.display.get_surface().get_size()
            
            # Vérifie si on clique sur le bouton de chat (afficher/cacher)
            chat_btn = pygame.Rect(window_width - 80, window_height - 30, 70, 25)
            if chat_btn.collidepoint(mouse_pos):
                self.chat_visible = not self.chat_visible
                return True
                
            if not self.chat_visible:
                return False
                
            # Vérifie si on clique sur la zone de saisie
            input_rect = pygame.Rect(10, window_height - 30, window_width - 90, 25)
            self.input_active = input_rect.collidepoint(mouse_pos)
            return self.input_active
            
        elif event.type == pygame.KEYDOWN and self.input_active and self.chat_visible:
            if event.key == pygame.K_RETURN:
                if self.input_text.strip():  # Vérifie que le message n'est pas vide
                    try:
                        # Envoie le message
                        network.send_chat_message(self.input_text)
                        # Ajoute le message localement
                        self.add_message("Vous", self.input_text)
                    except Exception as e:
                        print(f"Erreur lors de l'envoi du message : {e}")
                    self.input_text = ""
                self.input_active = False
                return True
            elif event.key == pygame.K_BACKSPACE:
                self.input_text = self.input_text[:-1]
                return True
            elif event.key == pygame.K_ESCAPE:
                self.input_active = False
                return True
            else:
                # Limite la longueur du texte
                if len(self.input_text) < 50:  
                    self.input_text += event.unicode
                return True
            
                return False
                
            # Vérifie si on clique sur la zone de saisie
            input_rect = pygame.Rect(10, window_height - 30, window_width - 90, 25)
            self.input_active = input_rect.collidepoint(mouse_pos)
            return self.input_active
            
        elif event.type == pygame.KEYDOWN and self.input_active and self.chat_visible:
            if event.key == pygame.K_RETURN:
                if self.input_text.strip():  # Vérifie que le message n'est pas vide
                    try:
                        # Envoie le message
                        network.send_chat_message(self.input_text)
                        # Ajoute le message localement
                        self.add_message("Vous", self.input_text)
                    except Exception as e:
                        print(f"Erreur lors de l'envoi du message : {e}")
                    self.input_text = ""
                self.input_active = False
                return True
            elif event.key == pygame.K_BACKSPACE:
                self.input_text = self.input_text[:-1]
                return True
            elif event.key == pygame.K_ESCAPE:
                self.input_active = False
                return True
            else:
                # Limite la longueur du texte
                if len(self.input_text) < 50:  
                    self.input_text += event.unicode
                return True
                
        return False

