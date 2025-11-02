import tkinter as tk
from tkinter import ttk, messagebox

class LiBrCalculator:
    def __init__(self, root):
        self.root = root
        self.root.title("LiBr Solution Calculator")
        
        # Create main frame
        self.frame = ttk.Frame(root, padding="10")
        self.frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Calculator type selection
        ttk.Label(self.frame, text="Select calculation type:").grid(row=0, column=0, columnspan=2)
        self.calc_type = tk.StringVar()
        ttk.Radiobutton(self.frame, text="Calculate H₂O Volume", variable=self.calc_type, 
                       value="volume", command=self.switch_mode).grid(row=1, column=0)
        ttk.Radiobutton(self.frame, text="Calculate LiBr Mass", variable=self.calc_type, 
                       value="mass", command=self.switch_mode).grid(row=1, column=1)
        
        # Input fields
        self.input1_label = ttk.Label(self.frame, text="LiBr mass (g):")
        self.input1_label.grid(row=2, column=0)
        self.input1 = ttk.Entry(self.frame)
        self.input1.grid(row=2, column=1)
        
        ttk.Label(self.frame, text="Concentration (mol/L):").grid(row=3, column=0)
        self.concentration = ttk.Entry(self.frame)
        self.concentration.grid(row=3, column=1)
        
        # Calculate button
        ttk.Button(self.frame, text="Calculate", command=self.calculate).grid(row=4, column=0, columnspan=2)
        
        # Result label
        self.result_var = tk.StringVar()
        ttk.Label(self.frame, textvariable=self.result_var).grid(row=5, column=0, columnspan=2)
        
        # Set default calculation type
        self.calc_type.set("volume")
        
    def switch_mode(self):
        if self.calc_type.get() == "volume":
            self.input1_label["text"] = "LiBr mass (g):"
        else:
            self.input1_label["text"] = "H₂O volume (mL):"
        self.result_var.set("")
        
    def calculate(self):
        try:
            value1 = float(self.input1.get())
            concentration = float(self.concentration.get())
            
            if self.calc_type.get() == "volume":
                # Calculate H2O volume
                mols_of_LiBr = value1 / 86.845  # LiBr molar mass
                volume_H2O = (mols_of_LiBr / concentration) * 1000  # Convert to mL
                self.result_var.set(f"Required H₂O volume: {volume_H2O:.2f} mL")
            else:
                # Calculate LiBr mass
                volume_L = value1 * 0.001  # Convert mL to L
                mols_of_LiBr = volume_L * concentration
                mass_LiBr = mols_of_LiBr * 86.845
                self.result_var.set(f"Required LiBr mass: {mass_LiBr:.2f} g")
                
        except ValueError:
            messagebox.showerror("Error", "Please enter valid numeric values")

if __name__ == "__main__":
    root = tk.Tk()
    app = LiBrCalculator(root)
    root.mainloop()