
import unittest
# Import the game function from the file where you saved it
from tictactoe_game import tic_tac_toe_beginner 

# Since the original tic_tac_toe_beginner runs the whole game 
# interactively, we need to extract the core logic for testing.

# For a beginner-style approach, let's create a simple BoardChecker
# class that mimics the win logic from the game loop.

class BoardChecker:
    """Helper class to replicate the simple, hardcoded win check logic."""
    def __init__(self, board):
        self.board = board
        self.board_size = 3
        
    def check_for_win(self, symbol):
        # Check rows
        for i in range(self.board_size):
            if self.board[i][0] == symbol and self.board[i][1] == symbol and self.board[i][2] == symbol:
                return True
                
        # Check columns
        for j in range(self.board_size):
            if self.board[0][j] == symbol and self.board[1][j] == symbol and self.board[2][j] == symbol:
                return True
        
        # Check main diagonal (top-left to bottom-right)
        if self.board[0][0] == symbol and self.board[1][1] == symbol and self.board[2][2] == symbol:
            return True
        
        # Check anti-diagonal (top-right to bottom-left)
        if self.board[0][2] == symbol and self.board[1][1] == symbol and self.board[2][0] == symbol:
            return True
        
        return False

    def check_for_draw(self):
        # Check if the board is full and nobody won
        for row in self.board:
            if ' ' in row:
                return False
        # If full, and win check passes (meaning nobody won yet), it's a draw
        # (Note: In a real game, you check win first, then draw)
        return True


class TestTicTacToeLogic(unittest.TestCase):
    
    # Test case 1: Player 'X' wins on the first row
    def test_win_row1(self):
        board = [
            ['X', 'X', 'X'],
            ['O', ' ', ' '],
            ['O', ' ', ' ']
        ]
        checker = BoardChecker(board)
        self.assertTrue(checker.check_for_win('X'), "Should detect a win in Row 1")

    # Test case 2: Player 'O' wins on the second column
    def test_win_col2(self):
        board = [
            ['X', 'O', 'X'],
            [' ', 'O', ' '],
            ['X', 'O', ' ']
        ]
        checker = BoardChecker(board)
        self.assertTrue(checker.check_for_win('O'), "Should detect a win in Column 2")

    # Test case 3: Player 'X' wins on the main diagonal
    def test_win_diag_main(self):
        board = [
            ['X', 'O', ' '],
            ['O', 'X', ' '],
            ['O', ' ', 'X']
        ]
        checker = BoardChecker(board)
        self.assertTrue(checker.check_for_win('X'), "Should detect a win in Main Diagonal")

    # Test case 4: Player 'O' wins on the anti-diagonal
    def test_win_diag_anti(self):
        board = [
            ['X', 'X', 'O'],
            ['X', 'O', ' '],
            ['O', ' ', 'X']
        ]
        checker = BoardChecker(board)
        self.assertTrue(checker.check_for_win('O'), "Should detect a win in Anti-Diagonal")

    # Test case 5: Game is ongoing (no win yet)
    def test_no_win_yet(self):
        board = [
            ['X', 'O', 'X'],
            ['O', 'X', 'O'],
            [' ', ' ', ' ']
        ]
        checker = BoardChecker(board)
        self.assertFalse(checker.check_for_win('X'), "Should not detect a win for X")
        self.assertFalse(checker.check_for_win('O'), "Should not detect a win for O")

    # Test case 6: Game ends in a draw
    def test_draw(self):
        board = [
            ['X', 'O', 'X'],
            ['O', 'X', 'X'],
            ['O', 'X', 'O']
        ]
        checker = BoardChecker(board)
        self.assertFalse(checker.check_for_win('X'), "Should not detect a win for X")
        self.assertTrue(checker.check_for_draw(), "Should detect a Draw")

# This line runs the tests when the script is executed
if __name__ == '__main__':
    unittest.main()