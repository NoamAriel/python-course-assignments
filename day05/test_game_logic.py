import pytest
from tic_tac_toe_business_logic import check_win_condition, check_draw_condition

# --- Fixtures for Board States ---

@pytest.fixture
def empty_board():
    """Returns an empty 3x3 board."""
    return [
        [' ', ' ', ' '],
        [' ', ' ', ' '],
        [' ', ' ', ' ']
    ]

@pytest.fixture
def draw_board():
    """Returns a full board that is a verified draw (no winner)."""
    # This configuration is a classic Tic-Tac-Toe draw
    return [
        ['X', 'O', 'X'],
        ['X', 'O', 'O'],  # Changed the middle row to break the X diagonal win
        ['O', 'X', 'X']
    ]

# --- Tests for Winning Conditions (X) ---

@pytest.mark.parametrize("board, expected_win", [
    # Win in Rows
    ([['X', 'X', 'X'], ['O', ' ', ' '], ['O', ' ', ' ']], True), # Row 1
    ([['O', ' ', ' '], ['X', 'X', 'X'], ['O', ' ', ' ']], True), # Row 2
    ([['O', ' ', ' '], ['O', ' ', ' '], ['X', 'X', 'X']], True), # Row 3

    # Win in Columns
    ([['X', 'O', ' '], ['X', ' ', ' '], ['X', 'O', ' ']], True), # Col 1
    ([['O', 'X', ' '], [' ', 'X', ' '], ['O', 'X', ' ']], True), # Col 2
    ([[' ', 'O', 'X'], [' ', ' ', 'X'], ['O', ' ', 'X']], True), # Col 3

    # Win Diagonals
    ([['X', 'O', ' '], ['O', 'X', ' '], ['O', ' ', 'X']], True), # Main Diagonal
    ([['O', 'O', 'X'], ['O', 'X', ' '], ['X', ' ', ' ']], True), # Anti-Diagonal
])
def test_x_wins(board, expected_win):
    """Tests all possible winning patterns for 'X'."""
    assert check_win_condition(board, 'X') == expected_win

# --- Tests for Winning Conditions (O) ---

@pytest.mark.parametrize("board, expected_win", [
    # Win in Rows
    ([['O', 'O', 'O'], ['X', ' ', ' '], ['X', ' ', ' ']], True), # Row 1
    
    # Win in Columns
    ([['X', 'O', 'X'], [' ', 'O', ' '], [' ', 'O', ' ']], True), # Col 2
    
    # Win Diagonals
    ([['O', 'X', 'X'], ['X', 'O', ' '], ['X', ' ', 'O']], True), # Main Diagonal
    ([['X', 'X', 'O'], ['X', 'O', ' '], ['O', ' ', ' ']], True), # Added Anti-Diagonal for 'O'
])
def test_o_wins(board, expected_win):
    """Tests a selection of winning patterns for 'O'."""
    assert check_win_condition(board, 'O') == expected_win

# --- Tests for Non-Winning States ---

def test_no_win_empty_board(empty_board):
    """Tests that an empty board has no winner."""
    assert not check_win_condition(empty_board, 'X')
    assert not check_win_condition(empty_board, 'O')

def test_no_win_in_progress():
    """Tests a game in progress where no win has occurred."""
    board = [
        ['X', 'O', ' '],
        ['X', 'O', ' '],
        [' ', ' ', 'X']
    ]
    assert not check_win_condition(board, 'X')
    assert not check_win_condition(board, 'O')
    
# --- Tests for Draw Condition ---

def test_is_draw(draw_board):
    """Tests that a full board with no winner is a draw."""
    # First, verify no winner
    assert not check_win_condition(draw_board, 'X')
    assert not check_win_condition(draw_board, 'O')
    # Then, check for draw condition
    assert check_draw_condition(draw_board)

def test_is_not_draw(empty_board):
    """Tests that an empty board is not a draw."""
    assert not check_draw_condition(empty_board)