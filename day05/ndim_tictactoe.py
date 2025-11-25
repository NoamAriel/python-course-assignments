import random
import sys

# --- Helper Functions for Input and Exit ---

def get_valid_input(prompt, data_type, min_val=None, max_val=None):
    """
    Prompts the user for input, handles validation, and checks for 'exit'.
    Returns the validated input or 'exit'.
    """
    while True:
        try:
            user_input = input(prompt).strip().lower()

            if user_input == "exit":
                return "exit"
            
            # Check if input is a valid number of the specified type
            if data_type == int:
                value = int(user_input)
            else:
                raise ValueError # Should not happen if data_type is only int
            
            # Check range constraints
            if min_val is not None and value < min_val:
                print(f"Input must be at least {min_val}.")
                continue
            if max_val is not None and value > max_val:
                print(f"Input must be at most {max_val}.")
                continue
            
            return value

        except ValueError:
            print(f"Invalid input. Please enter a valid {data_type.__name__} or 'exit'.")
        except EOFError:
            print("\nEOF received. Exiting game.")
            sys.exit()

# --- Board Display Function ---

def show_board(board, board_size):
    """
    Displays the board dynamically for any size N.
    """
    print("\n" + " " * 4 + " ".join(f"{i+1:<2}" for i in range(board_size)))
    
    separator_length = board_size * 3 + 4
    separator = " " * 3 + "-" * separator_length
    
    for i, row in enumerate(board):
        print(separator)
        row_str = " | ".join(f"{cell or ' ':<1}" for cell in row)
        print(f"{i+1:<3} | {row_str} |")
    print(separator)


# --- Win Checking Logic ---

def check_win(board, board_size, win_length, symbol):
    """
    Checks if the current player (symbol) has a winning line of length 'win_length'.
    This logic is generalized for any board size and win length.
    """
    
    # 1. Check Rows and Columns
    for i in range(board_size):
        # Check rows
        for j in range(board_size - win_length + 1):
            # Check sequence board[i][j] to board[i][j + win_length - 1]
            if all(board[i][j+k] == symbol for k in range(win_length)):
                return True
        
        # Check columns
        for j in range(board_size - win_length + 1):
            # Check sequence board[j][i] to board[j + win_length - 1][i]
            if all(board[j+k][i] == symbol for k in range(win_length)):
                return True

    # 2. Check Diagonals (Top-Left to Bottom-Right)
    for i in range(board_size - win_length + 1):
        for j in range(board_size - win_length + 1):
            # Check sequence starting at board[i][j]
            if all(board[i+k][j+k] == symbol for k in range(win_length)):
                return True

    # 3. Check Diagonals (Top-Right to Bottom-Left)
    for i in range(board_size - win_length + 1):
        for j in range(win_length - 1, board_size): # Start from the win_length-1 column
            # Check sequence starting at board[i][j]
            if all(board[i+k][j-k] == symbol for k in range(win_length)):
                return True

    return False

# --- Main Game Function ---

def extended_tic_tac_toe():
    """
    Main function to run the N-dimensional, K-to-win Tic-Tac-Toe game.
    """
    print("✨ Welcome to Extended N x N Tic-Tac-Toe! ✨")
    print("Type 'exit' at any prompt to quit the game.")
    
    # 1. Get Board Size (N)
    board_size_input = get_valid_input(
        "Enter the board size (N, e.g., 5 for 5x5, min 3): ", 
        int, 
        min_val=3
    )
    if board_size_input == "exit":
        print("\n--- Game Exited. Thanks for playing! ---")
        return
    board_size = board_size_input
    
    # 2. Get Winning Length (K)
    win_length_input = get_valid_input(
        f"Enter the length required to win (K, min 3, max {board_size}): ", 
        int, 
        min_val=3, 
        max_val=board_size
    )
    if win_length_input == "exit":
        print("\n--- Game Exited. Thanks for playing! ---")
        return
    win_length = win_length_input
    
    # Initialize the board
    board = [[' ' for _ in range(board_size)] for _ in range(board_size)]
    
    current_player = random.randint(1, 2)
    symbols = {1: 'X', 2: 'O'}
    print(f"\nPlayer {current_player} ({symbols[current_player]}) goes first.")
    
    game_over = False
    moves_made = 0
    total_cells = board_size * board_size

    show_board(board, board_size)

    # 3. Main Game Loop
    while not game_over:
        symbol = symbols[current_player]
        print(f"\nPlayer {current_player} ({symbol}), your turn.")
        
        while True:
            # Get Row Input
            row_input = get_valid_input(f"Choose a row (1 to {board_size}): ", int, min_val=1, max_val=board_size)
            if row_input == "exit":
                game_over = True
                break
            
            # Get Column Input
            col_input = get_valid_input(f"Choose a column (1 to {board_size}): ", int, min_val=1, max_val=board_size)
            if col_input == "exit":
                game_over = True
                break
                
            row, col = row_input - 1, col_input - 1 # Convert to 0-based index
            
            # Check if position is available
            if board[row][col] == ' ':
                board[row][col] = symbol
                moves_made += 1
                break 
            else:
                print("That position is occupied. Please choose again.")
        
        if game_over:
            break

        show_board(board, board_size)

        # 4. Check for Win
        if check_win(board, board_size, win_length, symbol):
            print(f"🏆 Player {current_player} ({symbol}) is the winner!! Congratulations! 🏆")
            game_over = True
        
        # 5. Check for Draw
        elif moves_made == total_cells:
            print("\n🤝 It is a draw! Well done, both players. 🤝")
            game_over = True
        
        # 6. Switch Player
        else:
            current_player = 3 - current_player # Switches 1 to 2, and 2 to 1

    print("\n--- Game Over! Thanks for playing! ---")

if __name__ == '__main__':
    extended_tic_tac_toe()