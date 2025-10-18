from flask import Flask, send_from_directory, request, jsonify
from flask_cors import CORS
import random
import os

app = Flask(__name__)
app.secret_key = 'tic_tac_toe_secret_key'
CORS(app)

class TicTacToeGame:
    def __init__(self):
        self.board = [' ' for _ in range(9)]
        self.current_player = 'X'
        self.winner = None
        self.game_over = False
        self.mode = 'easy'  # easy, medium, hard
        self.player_name = "Player"
        self.move_count = 0
    
    def reset_game(self):
        self.board = [' ' for _ in range(9)]
        self.current_player = 'X'
        self.winner = None
        self.game_over = False
        self.move_count = 0
    
    def make_move(self, position):
        if self.game_over or self.board[position] != ' ':
            return False
        self.board[position] = self.current_player
        self.move_count += 1
        if self.check_winner(self.current_player):
            self.winner = self.current_player
            self.game_over = True
        elif not any(cell == ' ' for cell in self.board):
            self.game_over = True
        else:
            self.current_player = 'O'
        return True
    
    def check_winner(self, player):
        # Rows
        for i in range(0, 9, 3):
            if self.board[i] == self.board[i+1] == self.board[i+2] == player:
                return True
        # Columns
        for i in range(3):
            if self.board[i] == self.board[i+3] == self.board[i+6] == player:
                return True
        # Diagonals
        if self.board[0] == self.board[4] == self.board[8] == player:
            return True
        if self.board[2] == self.board[4] == self.board[6] == player:
            return True
        return False
    
    def get_ai_move_easy(self):
        available_moves = [i for i, cell in enumerate(self.board) if cell == ' ']
        return random.choice(available_moves) if available_moves else None
    
    def get_ai_move_medium(self):
        available_moves = [i for i, cell in enumerate(self.board) if cell == ' ']
        # Try to win
        for move in available_moves:
            self.board[move] = 'O'
            if self.check_winner('O'):
                self.board[move] = ' '
                return move
            self.board[move] = ' '
        # Block player
        for move in available_moves:
            self.board[move] = 'X'
            if self.check_winner('X'):
                self.board[move] = ' '
                return move
            self.board[move] = ' '
        # 70% smart, 30% random
        if random.random() < 0.7:
            smart_moves = []
            for move in available_moves:
                if move == 4:
                    return move
                elif move in [0,2,6,8]:
                    smart_moves.append(move)
            if smart_moves:
                return random.choice(smart_moves)
        return random.choice(available_moves)
    
    def get_ai_move_hard(self):
        best_score = -float('inf')
        best_move = None
        for i in range(9):
            if self.board[i] == ' ':
                self.board[i] = 'O'
                score = self.minimax(0, False)
                self.board[i] = ' '
                if score > best_score:
                    best_score = score
                    best_move = i
        return best_move
    
    def minimax(self, depth, is_maximizing):
        if self.check_winner('O'):
            return 1
        elif self.check_winner('X'):
            return -1
        elif not any(cell == ' ' for cell in self.board):
            return 0
        if is_maximizing:
            best_score = -float('inf')
            for i in range(9):
                if self.board[i] == ' ':
                    self.board[i] = 'O'
                    score = self.minimax(depth + 1, False)
                    self.board[i] = ' '
                    best_score = max(score, best_score)
            return best_score
        else:
            best_score = float('inf')
            for i in range(9):
                if self.board[i] == ' ':
                    self.board[i] = 'X'
                    score = self.minimax(depth + 1, True)
                    self.board[i] = ' '
                    best_score = min(score, best_score)
            return best_score
    
    def make_ai_move(self):
        if self.current_player != 'O' or self.game_over:
            return False
        if self.mode == 'easy':
            ai_move = self.get_ai_move_easy()
        elif self.mode == 'medium':
            ai_move = self.get_ai_move_medium()
        else:
            ai_move = self.get_ai_move_hard()
        if ai_move is not None:
            self.board[ai_move] = 'O'
            self.move_count += 1
            if self.check_winner('O'):
                self.winner = 'O'
                self.game_over = True
            elif not any(cell == ' ' for cell in self.board):
                self.game_over = True
            else:
                self.current_player = 'X'
            return True
        return False
    
    def get_game_state(self):
        return {
            'board': self.board,
            'current_player': self.current_player,
            'winner': self.winner,
            'game_over': self.game_over,
            'mode': self.mode,
            'player_name': self.player_name,
            'move_count': self.move_count
        }

# Global game object
game = TicTacToeGame()

@app.route('/')
def index():
    return send_from_directory(os.getcwd(), 'index.html')

@app.route('/api/game/state', methods=['GET'])
def get_game_state():
    return jsonify(game.get_game_state())

@app.route('/api/game/move', methods=['POST'])
def make_move():
    data = request.json
    position = data.get('position')
    if game.current_player == 'X' and not game.game_over:
        success = game.make_move(position)
        if success:
            if not game.game_over:
                game.make_ai_move()
            return jsonify({'success': True, 'game_state': game.get_game_state()})
        else:
            return jsonify({'success': False, 'error': 'Invalid move'})
    return jsonify({'success': False, 'error': 'Not your turn'})

@app.route('/api/game/reset', methods=['POST'])
def reset_game():
    game.reset_game()
    return jsonify({'success': True, 'game_state': game.get_game_state()})

@app.route('/api/game/mode', methods=['POST'])
def set_game_mode():
    data = request.json
    mode = data.get('mode')
    if mode in ['easy', 'medium', 'hard']:
        game.mode = mode
        game.reset_game()
        return jsonify({'success': True, 'game_state': game.get_game_state()})
    else:
        return jsonify({'success': False, 'error': 'Invalid game mode'})

@app.route('/api/player/name', methods=['POST'])
def set_player_name():
    data = request.json
    name = data.get('name', '').strip()
    if name:
        game.player_name = name
        return jsonify({'success': True, 'player_name': game.player_name})
    else:
        return jsonify({'success': False, 'error': 'Name cannot be empty'})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
