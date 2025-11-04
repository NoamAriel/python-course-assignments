import tkinter as tk
from gui.app import LiBrCalculator

if __name__ == "__main__":
    root = tk.Tk()
    app = LiBrCalculator(root)
    root.mainloop()