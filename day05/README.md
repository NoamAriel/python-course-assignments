# ❌🅾️  Tic-Tac-Toe 

This is a Tic-Tac-Toe game. It includes basic input handling, win detection, and unit tests.

## 🚀 How to Run the Game

### 1. Requirements

This project uses **Python 3** and only relies on the **Python Standard Library** (no external dependencies are required).

### 2. Installation and Setup

1.  **Save the Game Code:**
    Save the main game logic into a file named `tictactoe_game.py`.


2.  **Run the Game:**
    Open your terminal or command prompt, navigate to the folder where you saved the file, and run:

    ```bash
    python tictactoe_game.py
    ```

### 3. Gameplay

* The game board is **3x3**.
* Players are **Player 1 ('X')** and **Player 2 ('O')**.
* You will be prompted to enter the **Row (1, 2, or 3)** and **Column (1, 2, or 3)** for your move.
* A win requires **three symbols in a row** (horizontal, vertical, or diagonal).


## 🔬 How to Run the Tests

To ensure the game logic (win and draw detection) is correct, you can run the included unit tests.

1.  **Save the Test Code:**
    Save the test script into a file named `test_tictactoe.py` in the *same folder* as `tictactoe_game.py`.

2.  **Run the Tests:**
    From your terminal, run the following command. The `unittest` module will automatically discover and run the tests.

    ```bash
    python -m unittest test_tictactoe.py
    ```

### Expected Output
If all logic is working correctly, you should see output similar to this: