import random


def tic_tac_toe():
    
    # Use ' ' for empty, 'X' for player 1, 'O' for player 2
    board = [
        [' ', ' ', ' '],
        [' ', ' ', ' '],
        [' ', ' ', ' ']
    ]
    board_size = 3  
    win_len = 3     

    print("👋 Welcome to Tic-Tac-Toe!")

    # Start with a random player (1 or 2)
    current_player = random.randint(1, 2)
    print(f"\nPlayer {current_player} goes first.")
    
    game_over = False
    
    # --- Function to Show Board  ---
    def show_board():
        print("\n---")
        # Loop through rows
        for i in range(board_size):
            # Print the row number
            print(f"{i + 1} ", end="")
            # Print the cells, separated by |
            print(f"{board[i][0]}|{board[i][1]}|{board[i][2]}")
            # Add separators, but not after the last row
            if i < board_size - 1:
                print("  -+-+-")
        print("  1 2 3") # Column numbers
        print("---")

    show_board()

    # --- Main Game Loop ---
    while not game_over:
        if current_player == 1:
            symbol = 'X'
        else:
            symbol = 'O'
            
        print(f"\nPlayer {current_player} ({symbol}), your turn.")
        
        # --- Get Player Input and Validate ---
        while True:
            try:
                # Ask for row input
                row_input = input("Enter row (1, 2, or 3, or type 'exit'): ").strip()
                
                if row_input.lower() == 'exit':
                    game_over = True
                    break

                row = int(row_input)
                
                # Ask for column input
                col_input = input("Enter column (1, 2, or 3): ").strip()
                
                if col_input.lower() == 'exit':
                    game_over = True
                    break

                col = int(col_input)
                
                # Check for valid numbers (1, 2, or 3)
                if 1 <= row <= board_size and 1 <= col <= board_size:
                    # Convert to 0-based index
                    r, c = row - 1, col - 1
                    
                    # Check if position is empty
                    if board[r][c] == ' ':
                        # Place the symbol
                        board[r][c] = symbol
                        break  # Input is good, break out of the input loop
                    else:
                        print("That spot is taken! Pick another one.")
                else:
                    print("Row/column must be 1, 2, or 3.")
            except ValueError:
                print("Bad input. Please enter a number or 'exit'.")
        
        # If exit was typed, break the main loop immediately
        if game_over:
            break
            
        show_board()

        # --- Check for Winner (The simple, hardcoded way) ---
        winner_found = False
        
        # Check rows
        for i in range(board_size):
            if board[i][0] == symbol and board[i][1] == symbol and board[i][2] == symbol:
                winner_found = True
                break
                
        # Check columns
        if not winner_found:
            for j in range(board_size):
                if board[0][j] == symbol and board[1][j] == symbol and board[2][j] == symbol:
                    winner_found = True
                    break
        
        # Check main diagonal (top-left to bottom-right)
        if not winner_found:
            if board[0][0] == symbol and board[1][1] == symbol and board[2][2] == symbol:
                winner_found = True
        
        # Check anti-diagonal (top-right to bottom-left)
        if not winner_found:
            if board[0][2] == symbol and board[1][1] == symbol and board[2][0] == symbol:
                winner_found = True

        # --- Announce Winner/Draw ---
        if winner_found:
            print(f"🥳 Player {current_player} ({symbol}) WINS!")
            game_over = True
        else:
            # Check for Draw (no empty spaces left)
            is_draw = True
            for row in board:
                if ' ' in row:
                    is_draw = False
                    break
                    
            if is_draw:
                print("🤝 It's a DRAW! Well played both.")
                game_over = True
            
            # --- Switch Players ---
            else:
                if current_player == 1:
                    current_player = 2
                else:
                    current_player = 1

    print("\n--- Game Over! Thanks for playing! ---")

# Execute the game function
if __name__ == '__main__':
    tic_tac_toe()