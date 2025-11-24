# ⚙️ GitHub Copilot Instructions

This file serves as a context provider and instruction set for GitHub Copilot when working within this repository. Adhering to these guidelines ensures more consistent, accurate, and contextually relevant code suggestions.

## 🎯 Project Overview & Goal

* **Primary Goal:** [**Describe the main purpose of your project in one sentence.** E.g., A Python-based FastAPI web service for managing user accounts.]
* **Key Technology Stack:** Python (3.10+), [Main Framework/Library, e.g., Django, Flask, FastAPI], [Database, e.g., PostgreSQL, SQLite].
* **Target Environment:** [E.g., Linux container (Docker), Serverless (AWS Lambda), etc.]

## 📜 Coding Style and Conventions

1.  **Language:** All core logic must be written in **Python**.
2.  **Formatting:** Adhere strictly to **PEP 8** standards. Use **Black** for auto-formatting.
3.  **Naming:**
    * Variables and functions: `snake_case`.
    * Classes: `PascalCase`.
    * Constants: `UPPER_SNAKE_CASE`.
4.  **Type Hinting:** **Always** include type hints for function parameters and return values (e.g., `def calculate_area(length: float, width: float) -> float:`).
5.  **Docstrings:** Use **Google Style** docstrings for all public functions, methods, and classes.

## 🛡️ Security and Best Practices

* **Input Validation:** Always sanitize and validate all external input (especially from HTTP requests or user input).
* **Secrets:** Never hardcode secrets, API keys, or credentials. Use **environment variables** (e.g., via `os.environ` or a library like `python-dotenv`).
* **Dependencies:** Prefer widely-used, well-maintained libraries. Check for security vulnerabilities when adding new packages.

## 📝 Specific Request for Copilot

* **Priority on Existing Code:** When suggesting code, **always prioritize matching the style, variable names, and patterns of the surrounding or existing code** in the file.
* **Use X/Y/Z Library:** When suggesting database interactions, use the **[Specific Library Name, e.g., `SQLAlchemy ORM`]** pattern.
* **Testing:** When asked to write a test, use the **`pytest`** framework and follow the `arrange/act/assert` structure.

## 🚫 What to AVOID

* Avoid using **f-strings for SQL query construction** to prevent SQL injection (use parameterized queries instead).
* Avoid importing large, unnecessary libraries for simple tasks (prefer standard library modules when possible).