import pygame
import sys
import socket
import threading
import pickle
import time

# Classe pour gérer le réseau (hôte)
class NetworkHost:
    def __init__(self, game, port):
        """Initialise un serveur réseau pour le jeu"""
        self.game = game
        self.port = port
        self.server = None
        self.client = None
        self.thread = None
        self.running = True
    def send_chat_message(self, message):
        """Envoie un message de chat"""
        if hasattr(self, 'client') and self.client:  # Pour NetworkHost
            try:
                data = pickle.dumps({'type': 'chat', 'message': message})
                self.client.send(data)
                print(f"Message envoyé: {message}")
            except Exception as e:
                print(f"Erreur lors de l'envoi du message: {e}")
        elif hasattr(self, 'socket') and self.socket:  # Pour NetworkClient
            try:
                data = pickle.dumps({'type': 'chat', 'message': message})
                self.socket.send(data)
                print(f"Message envoyé: {message}")
            except Exception as e:  
                print(f"Erreur lors de l'envoi du message: {e}")
    def start(self):
        """Démarre le serveur et attend une connexion"""
        self.thread = threading.Thread(target=self.run)
        self.thread.daemon = True
        self.thread.start()
        return True
    def handle_message(self, message):
        """Gère les messages reçus du client"""
        if message.get("type") == "chat":
            chat_message = message.get("message")
            print(f"Message de chat reçu: {chat_message}")
            self.game.chat.add_message("Adversaire", chat_message)
    def run(self):
        """Exécute le serveur et gère les connexions"""
        try:
            self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server.bind(('', self.port))
            self.server.listen(1)
            print(f"Serveur démarré sur le port {self.port}, en attente de connexion...")

            while self.running:
                try:
                    self.client, addr = self.server.accept()
                    print(f"Client connecté: {addr}")
                    self.send_game_state()  # Envoie l'état initial du jeu
                    self.handle_client()
                except socket.timeout:
                    continue
        except Exception as e:
            print(f"Erreur serveur: {e}")
        finally:
            if self.server:
                self.server.close()
            print("Serveur arrêté")

    def stop(self):
        """Arrête le serveur"""
        self.running = False
        if self.client:
            self.client.close()
        if self.thread:
            self.thread.join(2.0)  # Attente maximale de 2 secondes

    def send_game_state(self):
        """Envoie l'état complet du jeu au client"""
        if not self.client:
            return

        game_state = {
            'board': self.game.board,
            'turn': self.game.turn,
            'king_positions': self.game.king_positions,
            'castling_rights': self.game.castling_rights,
            'en_passant_target': self.game.en_passant_target,
            'in_check': self.game.in_check,
            'game_status': self.game.game_status
        }

        try:
            self.client.sendall(pickle.dumps(game_state))
            print("État du jeu envoyé au client")
        except Exception as e:
            print(f"Erreur lors de l'envoi de l'état du jeu: {e}")

    def send_move(self, start, end):
        """Envoie un mouvement au client"""
        if self.client:
            try:
                move = (start, end)
                data = pickle.dumps(move)
                self.client.send(data)
                print(f"Mouvement envoyé: {start} -> {end}")
            except Exception as e:
                print(f"Erreur lors de l'envoi du mouvement: {e}")

    def update_game_from_network(self, start, end):
        """Met à jour le jeu avec un mouvement reçu du réseau"""
        # Obtenez l'état actuel avant de faire le mouvement
        print(f"État avant le mouvement: tour = {self.game.turn}")
        print(f"Pièce à déplacer: {self.game.board[start[0]][start[1]]}")
        
        # Sauvegarde le tour actuel
        current_turn = self.game.turn
        
        # Force le tour au joueur qui fait le mouvement (pour éviter les problèmes)
        piece = self.game.board[start[0]][start[1]]
        if piece != '--':
            self.game.turn = piece[0]
        
        # Effectue le mouvement
        self.game.board[end[0]][end[1]] = self.game.board[start[0]][start[1]]
        self.game.board[start[0]][start[1]] = '--'
        
        # Restaure le tour
        self.game.turn = 'b' if current_turn == 'w' else 'w'
        
        print(f"État après le mouvement: tour = {self.game.turn}")
        print(f"Pièce déplacée vers: {self.game.board[end[0]][end[1]]}")
    
        # Met à jour l'affichage
        pygame.display.flip()

    def update_full_game_state(self, game_state):
        """Met à jour le jeu avec un état complet reçu du réseau"""
        self.game.board = game_state['board']
        self.game.turn = game_state['turn']
        self.game.king_positions = game_state['king_positions']
        self.game.in_check = game_state['in_check']
        self.game.castling_rights = game_state['castling_rights']
        self.game.en_passant_target = game_state['en_passant_target']
        self.game.game_status = game_state['game_status']
        print("État complet du jeu mis à jour")
        
        # Force le rafraîchissement de l'affichage
        pygame.display.flip()
def process_data(self, data):
    ""
    try:
        loaded_data = pickle.loads(data)
        
        # Vérifie si c'est un message de chat
        if isinstance(loaded_data, dict) and 'type' in loaded_data and loaded_data['type'] == 'chat':
            message = loaded_data['message']
            print(f"Message de chat reçu: {message}")
            self.game.chat.add_message("Adversaire", message)
            return
            
        # Traitement des autres types de données...
        if isinstance(loaded_data, tuple) and len(loaded_data) == 2:
            start, end = loaded_data
            if isinstance(start, tuple) and isinstance(end, tuple):
                print(f"Mouvement reçu: {start} -> {end}")
                self.update_game_from_network(start, end)
        elif isinstance(loaded_data, dict) and 'board' in loaded_data:
            print("État de jeu complet reçu")
            self.update_full_game_state(loaded_data)
    except Exception as e:
        print(f"Erreur lors du traitement des données: {e}")

    try:
        data = pickle.loads(data)
        if isinstance(data, dict):  # État complet du jeu
            self.game.board = data['board']
            self.game.turn = data['turn']
            self.game.castling_rights = data['castling_rights']
            self.game.en_passant_target = data['en_passant_target']
            self.game.king_positions = data['king_positions']
            self.game.in_check = data['in_check']
            self.game.game_status = data['game_status']
            
            # Traiter les informations de l'horloge
            if 'time_mode' in data and data['time_mode'] and not self.game.clock:
                # Configurer l'horloge si elle n'existe pas encore
                self.game.setup_clock(data['time_mode'])
            
            if 'clock' in data and data['clock'] and self.game.clock:
                # Mettre à jour l'état de l'horloge
                self.game.clock.white_time = data['clock']['white_time']
                self.game.clock.black_time = data['clock']['black_time']
                self.game.clock.increment = data['clock']['increment']
                self.game.clock.active_color = data['clock']['active_color']
                self.game.clock.is_running = data['clock']['is_running']
                self.game.clock.game_over = data['clock']['game_over']
                self.game.clock.timeout_color = data['clock']['timeout_color']
                
                # Mettre à jour l'horloge locale
                self.game.clock.last_update = time.time()
            
            # Mettre à jour l'état de démarrage du jeu
            if 'game_started' in data:
                self.game.game_started = data['game_started']
    except Exception as e:
        print(f"Erreur lors du traitement des données: {e}")
