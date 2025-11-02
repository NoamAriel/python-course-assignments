# filepath: pyramid-volume-gui/src/main.py
import tkinter as tk
from gui import PyramidVolumeGUI

def main():
    root = tk.Tk()
    root.title("Pyramid Volume Calculator")
    app = PyramidVolumeGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()