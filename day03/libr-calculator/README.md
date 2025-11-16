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
   git clone <repository-url>
   cd libr-calculator
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage

To run the application, execute the following command:
```
python src/main.py
```

Follow the on-screen instructions to perform the calculations.