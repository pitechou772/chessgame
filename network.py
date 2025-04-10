
# network.py
import socket
import threading
import pickle
import time

class Network:
    """Classe de base pour la communication réseau"""
    def __init__(self, game, port=5555):
        self.game = game
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.running = False
        self.thread = None
    
    def start(self):
        """Démarre le thread d'écoute"""
        self.running = True
        self.thread = threading.Thread(target=self.listen)
        self.thread.daemon = True
        self.thread.start()
    
    def stop(self):
        """Arrête le thread d'écoute et ferme la socket"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=1)
        try:
            self.socket.close()
        except:
            pass
    
    def listen(self):
        """Méthode abstraite pour l'écoute réseau"""
        pass
    
    def send_game_state(self):
        """Méthode abstraite pour envoyer l'état du jeu"""
        pass
    
    def send_move(self, start, end):
        """Méthode abstraite pour envoyer un mouvement"""
        pass


class NetworkHost(Network):
    """Serveur réseau pour héberger une partie"""
    def __init__(self, game, port=5555):
        super().__init__(game, port)
        self.client_socket = None
        self.client_address = None
    
    def start(self):
        """Configure et démarre le serveur"""
        try:
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind(('', self.port))
            self.socket.listen(1)
            print(f"Serveur démarré sur le port {self.port}...")
            super().start()
            return True
        except Exception as e:
            print(f"Erreur lors du démarrage du serveur: {e}")
            return False
    
    def listen(self):
        """Écoute les connexions et les messages"""
        try:
            # Attend une connexion client
            self.socket.settimeout(1)  # Timeout de 1 seconde pour vérifier régulièrement self.running
            
            while self.running:
                try:
                    self.client_socket, self.client_address = self.socket.accept()
                    print(f"Client connecté: {self.client_address}")
                    self.on_client_connected()
                    break
                except socket.timeout:
                    continue
                except Exception as e:
                    print(f"Erreur lors de l'attente de connexion: {e}")
                    return
            
            # Écoute les messages du client
            self.client_socket.settimeout(1)
            while self.running:
                try:
                    data = self.client_socket.recv(4096)
                    if not data:
                        break
                    
                    message = pickle.loads(data)
                    self.handle_message(message)
                except socket.timeout:
                    continue
                except Exception as e:
                    print(f"Erreur lors de la réception des données: {e}")
                    break
        finally:
            self.stop()
    
    def on_client_connected(self):
        """Appelé quand un client se connecte"""
        self.game.start_game()
        self.send_game_state()
    
    def handle_message(self, message):
        """Gère les messages reçus du client"""
        if not message:
            return
        
        if message.get("type") == "move":
            start = message.get("start")
            end = message.get("end")
            if start and end:
                # Simule le mouvement localement
                # On utilise un attribut pour savoir si on doit envoyer le mouvement
                # afin d'éviter une boucle infinie
                old_network = self.game.network
                self.game.network = None
                self.game.move_piece(start, end)
                self.game.network = old_network
        
        elif message.get("type") == "game_state":
            # Mise à jour de l'état du jeu depuis le client si nécessaire
            # Généralement pas utilisé dans cette direction, mais peut être utile pour la synchronisation
            pass
    
    def send_game_state(self):
        """Envoie l'état complet du jeu au client"""
        if not self.client_socket:
            return
        
        game_state = {
            "type": "game_state",
            "board": self.game.board,
            "turn": self.game.turn,
            "king_positions": self.game.king_positions,
            "castling_rights": self.game.castling_rights,
            "en_passant_target": self.game.en_passant_target,
            "in_check": self.game.in_check,
            "game_status": self.game.game_status
        }
        
        # Ajoute l'état de l'horloge si disponible
        if self.game.clock:
            game_state["clock"] = {
                "time_left": self.game.clock.time_left,
                "active_color": self.game.clock.active_color,
                "increment": self.game.clock.increment,
                "running": self.game.clock.running,
                "game_over": self.game.clock.game_over,
                "timeout_color": self.game.clock.timeout_color
            }
            game_state["time_mode"] = self.game.time_mode
        
        try:
            self.client_socket.sendall(pickle.dumps(game_state))
        except Exception as e:
            print(f"Erreur lors de l'envoi de l'état du jeu: {e}")
    
    def send_move(self, start, end):
        """Envoie un mouvement au client"""
        if not self.client_socket:
            return
        
        move_data = {
            "type": "move",
            "start": start,
            "end": end
        }
        
        try:
            self.client_socket.sendall(pickle.dumps(move_data))
        except Exception as e:
            print(f"Erreur lors de l'envoi du mouvement: {e}")


class NetworkClient(Network):
    """Client réseau pour rejoindre une partie"""
    def __init__(self, game, host, port=5555):
        super().__init__(game, port)
        self.host = host
    
    def connect(self):
        """Se connecte au serveur"""
        try:
            self.socket.connect((self.host, self.port))
            print(f"Connecté au serveur {self.host}:{self.port}")
            return True
        except Exception as e:
            print(f"Erreur lors de la connexion au serveur: {e}")
            return False
    
    def listen(self):
        """Écoute les messages du serveur"""
        self.socket.settimeout(1)
        while self.running:
            try:
                data = self.socket.recv(4096)
                if not data:
                    break
                
                message = pickle.loads(data)
                self.handle_message(message)
            except socket.timeout:
                continue
            except Exception as e:
                print(f"Erreur lors de la réception des données: {e}")
                break
        
        self.stop()
    
    def handle_message(self, message):
        """Gère les messages reçus du serveur"""
        if not message:
            return
        
        if message.get("type") == "move":
            start = message.get("start")
            end = message.get("end")
            if start and end:
                # Simule le mouvement localement
                old_network = self.game.network
                self.game.network = None
                self.game.move_piece(start, end)
                self.game.network = old_network
        
        elif message.get("type") == "game_state":
            # Mise à jour de l'état complet du jeu
            self.game.board = message.get("board", self.game.board)
            self.game.turn = message.get("turn", self.game.turn)
            self.game.king_positions = message.get("king_positions", self.game.king_positions)
            self.game.castling_rights = message.get("castling_rights", self.game.castling_rights)
            self.game.en_passant_target = message.get("en_passant_target", self.game.en_passant_target)
            self.game.in_check = message.get("in_check", self.game.in_check)
            self.game.game_status = message.get("game_status", self.game.game_status)
            
            # Mise à jour de l'horloge
            if message.get("clock") and not self.game.clock:
                # Crée une nouvelle horloge si elle n'existe pas
                clock_data = message.get("clock")
                time_mode = message.get("time_mode", "Standard")
                self.game.time_mode = time_mode
                self.game.setup_clock(time_mode)
                
                # Synchronise l'horloge avec les données reçues
                if self.game.clock:
                    self.game.clock.time_left = clock_data.get("time_left", self.game.clock.time_left)
                    self.game.clock.active_color = clock_data.get("active_color", self.game.clock.active_color)
                    self.game.clock.increment = clock_data.get("increment", self.game.clock.increment)
                    self.game.clock.running = clock_data.get("running", self.game.clock.running)
                    self.game.clock.game_over = clock_data.get("game_over", self.game.clock.game_over)
                    self.game.clock.timeout_color = clock_data.get("timeout_color", self.game.clock.timeout_color)
                    
                    # Met à jour le moment de la dernière mise à jour
                    if self.game.clock.running:
                        self.game.clock.last_update = time.time()
            
            elif message.get("clock") and self.game.clock:
                # Met à jour l'horloge existante
                clock_data = message.get("clock")
                self.game.clock.time_left = clock_data.get("time_left", self.game.clock.time_left)
                self.game.clock.active_color = clock_data.get("active_color", self.game.clock.active_color)
                self.game.clock.running = clock_data.get("running", self.game.clock.running)
                self.game.clock.game_over = clock_data.get("game_over", self.game.clock.game_over)
                self.game.clock.timeout_color = clock_data.get("timeout_color", self.game.clock.timeout_color)
                
                # Met à jour le moment de la dernière mise à jour
                if self.game.clock.running:
                    self.game.clock.last_update = time.time()
    
    def send_game_state(self):
        """Envoie l'état complet du jeu au serveur"""
        game_state = {
            "type": "game_state",
            "board": self.game.board,
            "turn": self.game.turn,
            "king_positions": self.game.king_positions,
            "castling_rights": self.game.castling_rights,
            "en_passant_target": self.game.en_passant_target,
            "in_check": self.game.in_check,
            "game_status": self.game.game_status
        }
        
        try:
            self.socket.sendall(pickle.dumps(game_state))
        except Exception as e:
            print(f"Erreur lors de l'envoi de l'état du jeu: {e}")
    
    def send_move(self, start, end):
        """Envoie un mouvement au serveur"""
        move_data = {
            "type": "move",
            "start": start,
            "end": end
        }
        
        try:
            self.socket.sendall(pickle.dumps(move_data))
        except Exception as e:
            print(f"Erreur lors de l'envoi du mouvement: {e}")