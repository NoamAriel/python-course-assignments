# Setific introduction

Silk fibers are known for their unique combination of mechanical characteristics of strength, extensibility, and toughness. These features result from silk’s highly hierarchical structure, shaped by the protein’s self-assembly during the natural fiber’s spinning. (https://www.nature.com/articles/s41467-024-50879-9)

In our laboratory, we aim to learn from nature how to synthesize silk. To achieve this, we need to break down natural silk to obtain its basic building blocks. We start by degumming silkworm silk and then dissolve it in a lithium bromide (LiBr) solution at a concentration of 9.3 M.

# libr-calculator

This project is a GUI application that allows users to calculate the required volume of water for a known mass of LiBr to achieve a desired concentration or to calculate the required mass of LiBr for a known volume of water to achieve a desired concentration.

## Project Structure

```
libr-calculator
├── src
│   ├── main.py                # Entry point for the GUI application
│   ├── calculations           # Contains calculation functions
│   │   ├── __init__.py
│   │   ├── volume_calculator.py  # Function to calculate required volume of H2O
│   │   └── mass_calculator.py    # Function to calculate required mass of LiBr
│   ├── gui                    # Contains GUI implementation
│   │   ├── __init__.py
│   │   └── app.py             # GUI application code
│   └── utils                  # Contains utility functions and constants
│       ├── __init__.py
│       └── constants.py       # Constants used in calculations
├── requirements.txt           # Dependencies for the project
└── README.md                  # Project documentation
```

## Installation

1. Clone the repository:
   ```
   git clone <https://github.com/NoamAriel/python-course-assignments/tree/main/day03>
   cd libr-calculator
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage

To run the application, execute the following command:
```
uv run .\libr-calculator\src\main.py
```

Otherwise, if you want to run the program in a terminal and not in a GUI application
Follow the next steps:
1. Make sure that the direction is correct and you are in the folder day03
```
 <https://github.com/NoamAriel/python-course-assignments/tree/main/day03>
```

2. Type the following command in your terminal
```
uv run .\main.py
```

Follow the on-screen instructions to perform the calculations.

We wish you succed in your research and have a fun (:
