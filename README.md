# Pong Game 🏓

## Description

Multiplayer implementation of the *Pong* game using the **Pygame** library for the graphical interface.  
The project demonstrates practical applications of **Computer Networks** and **Operating Systems** concepts, such as **client-server architecture**, **TCP socket communication**, **multithreading**, and **locks**, to create a real-time game.

## Technologies Used

- **Language:** Python 3.8+
- **Libraries:**
  - `pygame`: For graphical interface and game rendering.
  - `socket`: For network communication via TCP.
  - `threading`: For handling multiple clients and simultaneous matches.
  - `pickle`: For serializing Python objects to send over the network.
  - `python-dotenv`: For managing environment variables (IP, port, etc.).

## How to Run

### Requirements

- Python 3.8 or higher  
- pip (Python package manager)  

### Execution Instructions

**1. Clone the repository**

```bash
git clone https://github.com/joaoloss/multiplayer-pong-game.git
cd multiplayer-pong-game
```

**2. Environment Setup**

```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

**3. Connection Setup**

Create a `.env` file in the project root:

```bash
SERVER_IP=<ip_address>
SERVER_PORT=<port_number>
```

**4. Run the server**

```bash
python3 server.py
```

**5. Run the client**

For each player:

```bash
python3 client.py
```

## How to Test

1. Start the server. It will wait for client connections.  
2. Start the first client, input a name, and wait on the "Waiting for opponent..." screen.  
3. Once the second client connects, the server starts the match with a countdown.  
4. Control the paddle with **arrow keys (left/right)**.  
5. At the end, a victory or defeat message is displayed, with an option for a **Rematch**.

## Workflow

![Server flowchart](readme_imgs/server_flux.jpg)  
![Client flowchart](readme_imgs/client_flux.jpg)  

## Features

- Online multiplayer: Two players can play simultaneously.  
- Matchmaking system: Server pairs connecting players.  
- Graphical interface developed with Pygame.  
- Progressive difficulty: Ball speed increases as the match progresses.  
- Client-server architecture with TCP communication.  
- Rematch option after a match.  
- Handles player disconnections gracefully.  
- Thread-safe access to game state using locks.  
- Automation scripts for setup and execution.  
- Network configuration via `.env` file.  
- Realistic physics: Collision system and ball acceleration.  
- Intuitive interface: Name input and visual feedback.  
- Supports multiple simultaneous matches.

## Possible Future Improvements

### Game Enhancements

- Play with specific friends.  
- Audio and sound effects (collisions, background music, victory).  
- In-game scoring system.  
- Player ranking system.  
- Allow searching for new opponents without restarting.

### Network Enhancements

- Reconnection mechanism for temporary disconnections.  
- Consider using **UDP** for paddle movements.  
- Optimize network data size.  
- Evaluate slightly lower FPS (<60) for performance.

