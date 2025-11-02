# Pyramid Volume GUI Application

This project is a simple GUI application that calculates the volume of a pyramid based on user input for the base area and height.

## Project Structure

```
pyramid-volume-gui
├── src
│   ├── main.py          # Entry point of the application
│   ├── gui.py           # Contains the GUI layout and components
│   ├── calculations.py   # Function to calculate the pyramid volume
│   └── __init__.py      # Marks the directory as a Python package
├── tests
│   └── test_calculations.py  # Unit tests for the volume calculation function
├── requirements.txt      # Lists project dependencies
├── pyproject.toml        # Project configuration
├── .gitignore            # Specifies files to ignore in Git
└── README.md             # Documentation for the project
```

## Installation

To install the required dependencies, run the following command:

```
pip install -r requirements.txt
```

## Usage

To run the application, execute the following command:

```
python src/main.py
```

## How to Calculate Volume

1. Enter the base area of the pyramid in the designated input field.
2. Enter the height of the pyramid in the corresponding input field.
3. Click the "Calculate Volume" button to see the result displayed on the GUI.

## Example

- Base Area: 20
- Height: 10
- Volume: (1/3) * 20 * 10 = 66.67

## Contributing

Feel free to submit issues or pull requests for improvements or bug fixes.