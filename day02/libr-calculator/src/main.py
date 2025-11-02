def main():
    import tkinter as tk
    from tkinter import messagebox
    from calculations.volume_calculator import LiBr_con_volume_H2O
    from calculations.mass_calculator import LiBr_con_mass_LiBr

    def calculate_volume():
        try:
            mass = float(mass_entry.get())
            concentration = float(concentration_entry.get())
            volume = LiBr_con_volume_H2O(mass, concentration)
            messagebox.showinfo("Result", f"Required volume of H2O (mL): {volume}")
        except ValueError:
            messagebox.showerror("Input Error", "Please enter valid numeric values.")

    def calculate_mass():
        try:
            volume = float(volume_entry.get())
            concentration = float(concentration_entry.get())
            mass = LiBr_con_mass_LiBr(volume, concentration)
            messagebox.showinfo("Result", f"Required mass of LiBr (g): {mass}")
        except ValueError:
            messagebox.showerror("Input Error", "Please enter valid numeric values.")

    app = tk.Tk()
    app.title("LiBr Concentration Calculator")

    tk.Label(app, text="Mass of LiBr (g):").grid(row=0, column=0)
    mass_entry = tk.Entry(app)
    mass_entry.grid(row=0, column=1)

    tk.Label(app, text="Desired Concentration (mol/L):").grid(row=1, column=0)
    concentration_entry = tk.Entry(app)
    concentration_entry.grid(row=1, column=1)

    tk.Button(app, text="Calculate Volume of H2O", command=calculate_volume).grid(row=2, columnspan=2)

    tk.Label(app, text="Volume of H2O (mL):").grid(row=3, column=0)
    volume_entry = tk.Entry(app)
    volume_entry.grid(row=3, column=1)

    tk.Button(app, text="Calculate Mass of LiBr", command=calculate_mass).grid(row=4, columnspan=2)

    app.mainloop()

if __name__ == "__main__":
    main()