import random
import re



def check_correct_input(prompt, min_val=1, max_val=None):
    """
    Prompts the user for a valid positive integer input within optional min/max bounds.
    In addition, checks for the string 'exit' (case-insensitive).
    Returns the integer, or the string 'exit'.
    """
    while True:
        try:
            native_input = input(prompt).strip()
            if not native_input:
                print("Input cannot be empty. Please enter a number or 'exit'.")
                continue

            # --- Check for Exit Command ---
            if native_input.lower() == 'exit':
                return 'exit'

            # --- Process Numeric Input ---
            if not native_input.isdigit():
                print("Input must be a whole number (digit) or 'exit'.")
                continue

            native_num = int(native_input)

            if native_num < min_val:
                print(f"Input must be at least {min_val}.")
                continue

            if max_val is not None and native_num > max_val:
                print(f"Input must be less than or equal to {max_val}.")
                continue

            return native_num

        except ValueError:
            print("Invalid input. Please enter a whole number or 'exit'.")

def display_board(board):
    """
    Displays the board in a clean, readable format.
    """
    size = len(board)
    header = "  " + " ".join([str(i) for i in range(1, size + 1)])
    print("-" * (len(header) + 2))
    print(header)

    for i in range(size):
        row_display = [cell if cell != ' ' else '_' for cell in board[i]]
        print(f"{i + 1} |{'|'.join(row_display)}|")
    print("-" * (len(header) + 2))

def do_action(current_player, board):
    """
    Prompts the current player for a move (row and column) and updates the board.
    Returns the board and a flag indicating if the game should exit.
    """
    size = len(board)
    symbol = 'X' if current_player == 1 else 'O'
    print(f"\nPlayer {current_player} ({symbol}), it is your turn. (Type 'exit' to quit)")

    while True:
        # Prompt for row
        row_input = check_correct_input("Choose a row: ", 1, size)
        
        # Check for exit command after the first input
        if row_input == 'exit':
            return board, True # Return board and exit=True

        # Prompt for column
        col_input = check_correct_input("Choose a column: ", 1, size)
        
        # Check for exit command after the second input
        if col_input == 'exit':
            return board, True # Return board and exit=True

        # Input is valid number, proceed with 0-based indexing
        r, c = row_input - 1, col_input - 1

        if board[r][c] == ' ':
            board[r][c] = symbol
            return board, False # Return board and exit=False
        else:
            print("That position is occupied. Please choose again.")

def check_line(board, symbol, R):
    """
    Checks for a winning sequence of length R in all directions.
    R is the required 'in a row' length (the win_condition).
    """
    size = len(board)
    
    def check_direction(r, c, dr, dc):
        for k in range(R):
            row_check = r + k * dr
            col_check = c + k * dc
            if not (0 <= row_check < size and 0 <= col_check < size and board[row_check][col_check] == symbol):
                return False
        return True

    for r in range(size):
        for c in range(size):
            if board[r][c] == symbol:
                # Directions: Horizontal(0, 1), Vertical(1, 0), Diag-DR(1, 1), Diag-DL(1, -1)
                if check_direction(r, c, 0, 1) or \
                   check_direction(r, c, 1, 0) or \
                   check_direction(r, c, 1, 1) or \
                   check_direction(r, c, 1, -1):
                    return True
                    
    return False

def is_there_winner(board, symbol, win_condition):
    """
    Checks if the given symbol has won (using the win_condition length) or if the game is a draw.
    Returns 1 if there is a winner/draw, 0 otherwise.
    """
    if check_line(board, symbol, win_condition):
        return 1 # Winner

    # Check for Draw (no empty spaces left)
    if all(cell != ' ' for row in board for cell in row):
        print(" It is a draw!\n You both know how to play! Welldone!")
        return 1 # Draw (game ends)

    return 0


# --- Main Game Function  ---

def game_x_o_python():
    """
    Runs the main Tic-Tac-Toe game loop.
    """
    print("👋 Welcome to Tic-Tac-Toe!")

    # 1. Get Board Dimension
    size_game = check_correct_input('Choose a game dimension (e.g., 5, 6, 7): ', min_val=3)

    # 2. Get Win Condition (R)
    print("\nNext, let's set the number of symbols required for a win.")
    win_condition = check_correct_input(
        f'Choose the "in a row" length (must be between 3 and {size_game}): ', 
        min_val=3, 
        max_val=size_game
    )

    print(f"\nGame setup: Board Size {size_game}x{size_game}. Win condition: Connect {win_condition}.")
    
    # 3. Setup the board
    board = [[' ' for _ in range(size_game)] for _ in range(size_game)]

    # 4. Choose starting player
    current_player = random.randint(1, 2)
    print(f"\nPlayer {current_player} goes first.")
    display_board(board)

    # 5. Game Loop
    is_winner = 0
    game_exit = False
    
    while is_winner == 0 and not game_exit:
        symbol = 'X' if current_player == 1 else 'O'

        # Execute move - receive board and the exit flag
        board, game_exit = do_action(current_player, board)

        if game_exit:
            break # Exit the loop immediately if the player typed 'exit'

        # Display the updated board
        display_board(board)

        # Check for winner or draw
        is_winner = is_there_winner(board, symbol, win_condition)

        if is_winner == 1:
            if all(cell != ' ' for row in board for cell in row):
                 # Draw message is printed inside is_there_winner
                 pass 
            else:
                 print(f"\n--- Game Over! Player {current_player} ({symbol}) is the winner by connecting {win_condition}! ---")
        elif is_winner == 0:
            # Switch player (1 -> 2, 2 -> 1)
            current_player = 3 - current_player

    if game_exit:
        print("\n👋 Game aborted. Thanks for playing!")


# --- Run the game ---
if __name__ == '__main__':
    game_x_o_python()