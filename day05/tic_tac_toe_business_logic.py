# This file contains the logic extracted from the main game function
# for testing purposes.

def check_win_condition(board, symbol):
    """
    Checks if the given symbol has won the 3x3 game.
    A win is three in a row, column, or diagonal.
    """
    board_size = 3
    
    # Check rows
    for i in range(board_size):
        if board[i][0] == symbol and board[i][1] == symbol and board[i][2] == symbol:
            return True
            
    # Check columns
    for j in range(board_size):
        if board[0][j] == symbol and board[1][j] == symbol and board[2][j] == symbol:
            return True
    
    # Check main diagonal (top-left to bottom-right)
    if board[0][0] == symbol and board[1][1] == symbol and board[2][2] == symbol:
        return True
    
    # Check anti-diagonal (top-right to bottom-left)
    if board[0][2] == symbol and board[1][1] == symbol and board[2][0] == symbol:
        return True

    return False

def check_draw_condition(board):
    """
    Checks if the game has resulted in a draw (board is full and no winner).
    Note: It only checks if the board is full. The main game loop must
    call check_win_condition first.
    """
    # Check for Draw (no empty spaces left)
    for row in board:
        if ' ' in row:
            return False
    return True

# Note: The original tic_tac_toe function is kept separate as it handles I/O.
# Only the logic functions above are used for testing.