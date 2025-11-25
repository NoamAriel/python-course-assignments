# ⚙️ GitHub Copilot Instructions

This file serves as a context provider and instruction set for GitHub Copilot when working within this repository. Adhering to these guidelines ensures more consistent, accurate, and contextually relevant code suggestions.

## 🎯 Project Overview & Goal

* **Primary Goal:** program the Tic-Tac-Toe game with 2 players.
* **Key Technology Stack:** Python (3.10+), No external frameworks or complex libraries.
* **Target Environment:** Local Console/Terminal execution.

## 📜 Coding Style and Conventions

1.  **Language:** All core logic must be written in **Python**.
2.  **Formatting:** Maintain clear readability and use simple, direct logic
3.  **Naming:**
    * Use descriptive variable names that clearly indicate their purpose (e.g., board_size, current_player).
4.  **Type Hinting:** **Always** include type hints for function parameters and return values (e.g., `def calculate_area(length: float, width: float) -> float:`).
5.  **Docstrings:** No formal docstrings are required, but simple comments explaining non-obvious blocks are acceptable.
6
## 🛡️ Security and Best Practices

* **Input Validation:** Input is handled via basic try-except blocks to catch non-integer input and if/else checks for boundary limits (1, 2, 3).

* **Dependencies:** No external dependencies are used in this project.
* **Global Variables:** Minimize the use of global variables; prefer to pass data structures like the board matrix directly.

## 📝 Specific Request for Copilot

* **Priority on Existing Code:** When suggesting code, **always prioritize matching the style, variable names, and patterns of the surrounding or existing code** in the file.
* **Win Logic:** When asked to check for a win, use the explicit, hardcoded checks for all 8 possible 3-in-a-row combinations
* **Testing:** When asked to write a test, use the **`pytest`** framework and follow the `arrange/act/assert` structure.

## 🚫 What to AVOID

* Avoid using **f-strings for SQL query construction** to prevent SQL injection (use parameterized queries instead).
* Avoid importing large, unnecessary libraries for simple tasks (prefer standard library modules when possible).