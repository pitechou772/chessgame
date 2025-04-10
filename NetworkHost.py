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

    def start(self):
        """Démarre le serveur et attend une connexion"""
        self.thread = threading.Thread(target=self.run)
        self.thread.daemon = True
        self.thread.start()
        return True

    def run(self):
        """Exécute le serveur et gère les connexions"""
        try:
            # Crée et configure le socket serveur
            self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server.bind(('', self.port))
            self.server.listen(1)
            print(f"Serveur démarré sur le port {self.port}, en attente de connexion...")

            # Attente limitée pour permettre de vérifier self.running
            self.server.settimeout(1.0)

            # Attente d'une connexion client
            while self.running:
                try:
                    self.client, addr = self.server.accept()
                    print(f"Client connecté: {addr}")
                    
                    # Envoie l'état initial du jeu au client
                    self.send_game_state()
                    
                    # Boucle pour recevoir les messages du client
                    self.client.settimeout(0.1)
                    while self.running:
                        try:
                            data = self.client.recv(4096)  # Augmenté pour les états de jeu
                            if not data:
                                break
                                
                            # Essaie d'abord de décoder comme un mouvement
                            try:
                                move = pickle.loads(data)
                                if isinstance(move, tuple) and len(move) == 2:
                                    start, end = move
                                    if isinstance(start, tuple) and isinstance(end, tuple):
                                        print(f"Mouvement reçu: {start} -> {end}")
                                        self.update_game_from_network(start, end)
                                elif isinstance(move, dict) and 'board' in move:
                                    print("État de jeu complet reçu")
                                    self.update_full_game_state(move)
                            except Exception as e:
                                print(f"Erreur lors du traitement des données: {e}")
                                
                        except socket.timeout:
                            # Timeout est normal, continue la boucle
                            continue
                        except Exception as e:
                            print(f"Erreur lors de la réception des données du client: {e}")
                            break
                            
                    if self.client:
                        self.client.close()
                        self.client = None
                    print("Client déconnecté, en attente d'une nouvelle connexion...")
                    
                except socket.timeout:
                    # Timeout est normal, continue la boucle
                    continue
                except Exception as e:
                    print(f"Erreur lors de l'attente de connexion: {e}")
                    break
                    
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
        """Envoie l'état complet du jeu"""
        game_state = {
            'board': self.game.board, 
            'turn': self.game.turn,
            'castling_rights': self.game.castling_rights,
            'en_passant_target': self.game.en_passant_target,
            'king_positions': self.game.king_positions,
            'in_check': self.game.in_check,
            'game_status': self.game.game_status,
            # Ajouter les informations de l'horloge
            'clock': {
                'white_time': self.game.clock.white_time if self.game.clock else None,
                'black_time': self.game.clock.black_time if self.game.clock else None,
                'increment': self.game.clock.increment if self.game.clock else None,
                'active_color': self.game.clock.active_color if self.game.clock else None,
                'is_running': self.game.clock.is_running if self.game.clock else False,
                'game_over': self.game.clock.game_over if self.game.clock else False,
                'timeout_color': self.game.clock.timeout_color if self.game.clock else None
            },
        'time_mode': self.game.time_mode,
        'game_started': self.game.game_started
    }
        self.connection.send(pickle.dumps(game_state))
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
    """Traite les données reçues"""
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