import socket
import threading
import pickle
import pygame
import time
import math
from dotenv import load_dotenv
import os
from random import randint
import time

WIDTH, HEIGHT = 960, 600
PADDLE_WIDTH, PADDLE_HEIGHT = 120, 10
BALL_RADIUS = 8
BALL_SPEED_X_INITIAL, BALL_SPEED_Y_INITIAL = 4, 4
SPEED_INCREASE_PER_FRAME = 0.005
MAX_SPEED = 12

# Initialize pygame to use Rect
pygame.init()

class Game:
    """
    Represents a two-player Pong game.
    Each game has its own lock to securely access the game state.
    """
    def __init__(self, game_id: str):
        self.game_id = game_id
        self.lock = threading.Lock() 
        self.state = {
            "paddles": [
                pygame.Rect(WIDTH/2 - PADDLE_WIDTH/2, HEIGHT - 20 - PADDLE_HEIGHT, PADDLE_WIDTH, PADDLE_HEIGHT),
                pygame.Rect(WIDTH/2 - PADDLE_WIDTH/2, 20, PADDLE_WIDTH, PADDLE_HEIGHT)
            ],
            "ball": pygame.Rect(WIDTH/2 - BALL_RADIUS, HEIGHT/2 - BALL_RADIUS, BALL_RADIUS * 2, BALL_RADIUS * 2),
            "winner_id": None,
            "game_started": False,
            "countdown": 3,
            "ball_speed": [BALL_SPEED_X_INITIAL, BALL_SPEED_Y_INITIAL],
            "player_names": ["", ""],
            "connected_players": 0,
            "active": True,
            "play_again_votes": 0,
            "player_leaved": False
        }
    
    def get_state_copy(self):
        """Get a secure copy of the current game state"""
        with self.lock:
            return self.state.copy()
    
    def update_connected_players(self, delta: int):
        """Updates the number of securely connected players"""
        with self.lock:
            self.state["connected_players"] += delta
    
    def set_player_name(self, player_id: int, name: str):
        """Set a player's name securely"""
        with self.lock:
            self.state["player_names"][player_id] = name
    
    def update_paddle(self, player_id: int, paddle_rect):
        """Updates a player's racket position"""
        with self.lock:
            self.state["paddles"][player_id] = paddle_rect
    
    def increment_play_again_votes(self):
        """Add a vote to play again"""
        with self.lock:
            self.state["play_again_votes"] += 1
            return self.state["play_again_votes"]
    
    def reset_game(self):
        """Restart the game for a new start"""
        with self.lock:
            self.state["paddles"] = [
                pygame.Rect(WIDTH/2 - PADDLE_WIDTH/2, HEIGHT - 20 - PADDLE_HEIGHT, PADDLE_WIDTH, PADDLE_HEIGHT),
                pygame.Rect(WIDTH/2 - PADDLE_WIDTH/2, 20, PADDLE_WIDTH, PADDLE_HEIGHT)
            ]
            self.state["ball"] = pygame.Rect(WIDTH/2 - BALL_RADIUS, HEIGHT/2 - BALL_RADIUS, BALL_RADIUS * 2, BALL_RADIUS * 2)
            self.state["winner_id"] = None
            self.state["game_started"] = False
            self.state["countdown"] = 3
            self.state["ball_speed"] = [BALL_SPEED_X_INITIAL, BALL_SPEED_Y_INITIAL]
            self.state["play_again_votes"] = 0
    
    def set_player_left(self):
        """Marks that a player has left the match"""
        with self.lock:
            self.state["player_leaved"] = True
    
    def deactivate(self):
        """Disables the game (ends the match)"""
        with self.lock:
            self.state["active"] = False

def countdown_thread(game: Game):
    """
    Countdown before the game starts
    """
    print(f"Starting countdown for game {game.game_id}")
    
    while True:
        with game.lock:
            is_active = game.state["active"]
            current_countdown = game.state["countdown"]
        if not is_active:
            break
        if current_countdown > 0:
            time.sleep(1)
            with game.lock:
                game.state["countdown"] -= 1
                print(f"Game {game.game_id}: Countdown = {game.state['countdown']+1}")
        else:
            with game.lock:
                game.state["game_started"] = True
            break
    
    print(f"Countdown for game {game.game_id} has ended")

def game_logic_thread(game: Game):
    """
    Control the movement of the ball and check who won.    
    """
    print(f"Starting game {game.game_id} logic")

    while True:
        with game.lock:
            is_active = game.state["active"]
            countdown = game.state["countdown"]
            winner_id = game.state["winner_id"]
        
        if not is_active:
            break

        if countdown <= 0 and winner_id is None:
            
            # Captures snapshot of the current state with minimal locking
            with game.lock:
                current_ball = game.state["ball"].copy()
                current_speed = game.state["ball_speed"].copy()
                current_paddles = [paddle.copy() for paddle in game.state["paddles"]]
                connected_players = game.state["connected_players"]
            
            ball_speed_x, ball_speed_y = current_speed
            
            # Increase speed gradually
            if abs(ball_speed_y) < MAX_SPEED:
                new_speed_y = abs(ball_speed_y) + SPEED_INCREASE_PER_FRAME
                ball_speed_y = math.copysign(new_speed_y, ball_speed_y)
            
            if abs(ball_speed_x) < MAX_SPEED:
                new_speed_x = abs(ball_speed_x) + SPEED_INCREASE_PER_FRAME
                ball_speed_x = math.copysign(new_speed_x, ball_speed_x)
            
            # Calculates new ball position
            new_ball_x = current_ball.x + ball_speed_x
            new_ball_y = current_ball.y + ball_speed_y
            
            # Collisions with side walls
            if new_ball_x <= 0 or new_ball_x >= WIDTH - current_ball.width:
                ball_speed_x *= -1
                new_ball_x = current_ball.x + ball_speed_x  # Recalcula posição
            
            # Creates temporary rect for collision testing
            temp_ball = pygame.Rect(new_ball_x, new_ball_y, current_ball.width, current_ball.height)
            
            # Collisions with rackets
            if (temp_ball.colliderect(current_paddles[0]) and ball_speed_y > 0):
                ball_speed_y = -abs(ball_speed_y)
                new_ball_y = current_ball.y + ball_speed_y
            elif (temp_ball.colliderect(current_paddles[1]) and ball_speed_y < 0):
                ball_speed_y = abs(ball_speed_y)
                new_ball_y = current_ball.y + ball_speed_y
            
            # Check victory conditions
            new_winner_id = None
            if new_ball_y <= 0:
                new_winner_id = 0
            elif new_ball_y >= HEIGHT - current_ball.height:
                new_winner_id = 1
            
            with game.lock:
                game.state["ball"].x = new_ball_x
                game.state["ball"].y = new_ball_y
                game.state["ball_speed"] = [ball_speed_x, ball_speed_y]
                
                if new_winner_id is not None:
                    game.state["winner_id"] = new_winner_id
                    if connected_players == 2:
                        print(f'Game {game.game_id}: Player {new_winner_id+1} won!')
        
        time.sleep(1/60)
    print(f"Closing game {game.game_id} logic")

def client_thread(conn: socket.socket, game: Game, player_id: int):
    """
    Thread that handles communication with a specific client.
    """
    try:
        print(f"Connected client: Game {game.game_id}, Player {player_id+1}")
        
        # Send player ID
        conn.send(pickle.dumps(player_id))
        
        # Receive player name
        try:
            player_name = pickle.loads(conn.recv(2048))
        except Exception as e:
            print(f"Erro ao receber nome: {e}")
            player_name = "So-and-so"
        

        # Save player name
        game.set_player_name(player_id, player_name)
        print(f"Player {player_id+1} of game {game.game_id} defined as: {player_name}")

        game.update_connected_players(1)
        
        # If both players are connected, countdown starts
        with game.lock:
            if game.state["connected_players"] == 2 and not game.state["game_started"]:
                countdown_logic = threading.Thread(target=countdown_thread, args=(game,))
                countdown_logic.start()
                game.state["game_started"] = True
        
        # Client main loop
        while game.state["active"]:
            try:
                # Send curr game state
                conn.send(pickle.dumps(game.get_state_copy()))
                
                data = conn.recv(2048)
                if not data: # Disconnected client
                    break
                
                received_data = pickle.loads(data)
                
                if isinstance(received_data, str) and received_data == "play_again":
                    votes = game.increment_play_again_votes()
                    print(f"Voto para reiniciar jogo {game.game_id}: {votes}/2")
                    
                    # If both voted, restart the game
                    if votes >= 2:
                        print(f"Restarting game {game.game_id}")
                        game.reset_game()
                        countdown_logic = threading.Thread(target=countdown_thread, args=(game,))
                        countdown_logic.start()
                        
                elif isinstance(received_data, pygame.Rect):
                    game.update_paddle(player_id, received_data)
                
            except Exception as e:
                print(f"Error in communication with {player_name}: {e}")
                break
        
        print(f"Disconnecting {player_name} from game {game.game_id}")
        game.update_connected_players(-1)
        game.set_player_left()
        
        with game.lock:
            if game.state["connected_players"] == 0:
                game.deactivate()
                print(f"Game {game.game_id} terminated - no players connected")
    except Exception as e:
        print(f"Error in client thread of {player_name} in game {game.game_id}: {e}")
    
    try:
        conn.close()
    except:
        pass

def main():
    load_dotenv()
    
    ip_address = os.getenv("SERVER_IP")
    port_number = int(os.getenv("SERVER_PORT"))
    
    # TCP socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
    
    try:
        s.bind((ip_address, port_number))
        s.listen(5) 
        print(f"Pong game server started at {ip_address}:{port_number}")
        print("Waiting for connections...")
    except socket.error as e:
        print(f"Error starting server: {e}")
        return
    
    # List of games waiting for a second player
    unmatched_games = list()  
    
    try:
        while True:
            conn, addr = s.accept()
            print(f"New connection from {addr}")
            
            game = None
            player_id = int()

            # Check if there is a game waiting for a player, otherwise create a new one
            if len(unmatched_games) > 0:
                game = unmatched_games.pop()
                player_id = 1
                print(f"Adding player to game {game.game_id}")
            else:
                # Create a new game
                game_id = str(randint(1000, 9999))
                game = Game(game_id)
                unmatched_games.append(game)
                player_id = 0
                print(f"Creating new game {game.game_id}")
                
                # Start the game logic (ball movement, physics)
                game_logic = threading.Thread(target=game_logic_thread, args=(game,))
                game_logic.start()
            
            # Start client thread
            client_logic = threading.Thread(target=client_thread, args=(conn, game, player_id))
            client_logic.start()
            
    except KeyboardInterrupt:
        print("\nServer interrupted by user")
    except Exception as e:
        print(f"Server error: {e}")
    finally:
        s.close()

if __name__ == "__main__":
    main()
