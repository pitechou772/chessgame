import pygame
import sys
import socket
import threading
import pickle
import time

class NetworkClient:
    def __init__(self, game, host, port):
        """Initialise un client réseau pour le jeu"""
        self.game = game
        self.host = host
        self.port = port
        self.socket = None
        self.thread = None
        self.running = True

    def connect(self):
        """Se connecte au serveur"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            print(f"Connecté au serveur {self.host}:{self.port}")
            return True
        except Exception as e:
            print(f"Erreur de connexion au serveur: {e}")
            return False

    def start(self):
        """Démarre le thread du client"""
        self.thread = threading.Thread(target=self.run)
        self.thread.daemon = True
        self.thread.start()

    def run(self):
        """Exécute le client et gère les messages du serveur"""
        try:
            # Reçoit l'état initial du jeu
            self.receive_game_state()

            # Boucle pour recevoir les mises à jour du serveur
            self.socket.settimeout(0.1)  # Petit timeout pour pouvoir vérifier self.running
            while self.running:
                try:
                    data = self.socket.recv(4096)  # Augmenté pour les états de jeu
                    if not data:
                        break

                    # Essaie d'abord de décoder comme un mouvement
                    try:
                        loaded_data = pickle.loads(data)
                        if isinstance(loaded_data, tuple) and len(loaded_data) == 2:
                            start, end = loaded_data
                            if isinstance(start, tuple) and isinstance(end, tuple):
                                print(f"Mouvement reçu: {start} -> {end}")
                                self.update_game_from_network(start, end)
                        elif isinstance(loaded_data, dict) and 'board' in loaded_data:
                            print("État de jeu complet reçu")
                            self.update_full_game_state(loaded_data)
                    except Exception as e:
                        print(f"Erreur lors du traitement des données reçues: {e}")

                except socket.timeout:
                    # Timeout est normal, continue la boucle
                    continue
                except Exception as e:
                    print(f"Erreur lors de la réception des données: {e}")
                    break

        except Exception as e:
            print(f"Erreur client: {e}")
        finally:
            if self.socket:
                self.socket.close()
            print("Client arrêté")

    def stop(self):
        """Arrête le client"""
        self.running = False
        if self.thread:
            self.thread.join(2.0)  # Attente maximale de 2 secondes

    def receive_game_state(self):
        """Reçoit l'état complet du jeu depuis le serveur"""
        try:
            data = self.socket.recv(4096)  # Taille plus grande pour l'état initial
            if data:
                game_state = pickle.loads(data)
                self.update_full_game_state(game_state)
        except Exception as e:
            print(f"Erreur lors de la réception de l'état du jeu: {e}")

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

    def send_move(self, start, end):
        """Envoie un mouvement au serveur"""
        if self.socket:
            try:
                move = (start, end)
                data = pickle.dumps(move)
                self.socket.send(data)
                print(f"Mouvement envoyé: {start} -> {end}")
            except Exception as e:
                print(f"Erreur lors de l'envoi du mouvement: {e}")

    def send_game_state(self):
        """Envoie l'état complet du jeu au serveur"""
        if self.socket:
            try:
                game_state = {
                    'board': self.game.board,
                    'turn': self.game.turn,
                    'king_positions': self.game.king_positions,
                    'in_check': self.game.in_check,
                    'castling_rights': self.game.castling_rights,
                    'en_passant_target': self.game.en_passant_target,
                    'game_status': self.game.game_status
                }
                data = pickle.dumps(game_state)
                self.socket.send(data)
                print("État du jeu envoyé au serveur")
            except Exception as e:
                print(f"Erreur lors de l'envoi de l'état du jeu: {e}")

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
