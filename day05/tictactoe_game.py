import random


def tic_tac_toe():
    board = [
        [' ', ' ', ' '],
        [' ', ' ', ' '],
        [' ', ' ', ' ']
    ]
    board_size = 3  


    print("Welcome to Tic-Tac-Toe!")

    current_player = random.randint(1, 2)
    print(f"\nPlayer {current_player} goes first.")
    
    game_over = False
    
    def show_board():

        print("\n1 ", board[0][0], "|", board[0][1], "|", board[0][2])
        print("   ---------")
        print("2 ", board[1][0], "|", board[1][1], "|", board[1][2])
        print("   ---------")
        print("3 ", board[2][0], "|", board[2][1], "|", board[2][2])
        print("    1  2  3")
 

    show_board()

   
    while not game_over:
        if current_player == 1:
            symbol = 'X'
        else:
            symbol = 'O'
            
        print(f"\nPlayer {current_player} ({symbol}), your turn.")
        
        while True:
            try:
                row_input = input("Choose a row:").strip()

                row = int(row_input)
                col_input = input("Choose a column: ").strip()
                col = int(col_input)
                
                if 1 <= row <= board_size and 1 <= col <= board_size:
                    r, c = row - 1, col - 1
                    
                    if board[r][c] == ' ':
                        board[r][c] = symbol
                        break 
                    else:
                        print("That position is occupied. player {current_player} ({symbol}) pls choose again.")
                else:
                    print("that row/column doesn''t exist. player {current_player} ({symbol}) pls choose again")
            except ValueError:
                print("Choose a native number:")
        
        show_board()

        winner_found = False
        
        for i in range(board_size):
            if board[i][0] == symbol and board[i][1] == symbol and board[i][2] == symbol:
                winner_found = True
                break
                
        if not winner_found:
            for j in range(board_size):
                if board[0][j] == symbol and board[1][j] == symbol and board[2][j] == symbol:
                    winner_found = True
                    break
        
        if not winner_found:
            if board[0][0] == symbol and board[1][1] == symbol and board[2][2] == symbol:
                winner_found = True
        
        if not winner_found:
            if board[0][2] == symbol and board[1][1] == symbol and board[2][0] == symbol:
                winner_found = True

        if winner_found:
            print(f" Player {current_player} ({symbol}) is the winner!! Congratulations!")
            game_over = True
        else:
            is_draw = True
            for row in board:
                if ' ' in row:
                    is_draw = False
                    break
                    
            if is_draw:
                print("It is a draw!\n You both know how to play!\n Welldone!\n")
                game_over = True
            
            else:
                if current_player == 1:
                    current_player = 2
                else:
                    current_player = 1

    print("\n--- Game Over! Thanks for playing! ---")

if __name__ == '__main__':
    tic_tac_toe()