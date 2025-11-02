class PyramidVolumeGUI:
    def __init__(self, master):
        self.master = master
        master.title("Pyramid Volume Calculator")

        self.label_base_area = Label(master, text="Base Area:")
        self.label_base_area.pack()

        self.entry_base_area = Entry(master)
        self.entry_base_area.pack()

        self.label_height = Label(master, text="Height:")
        self.label_height.pack()

        self.entry_height = Entry(master)
        self.entry_height.pack()

        self.calculate_button = Button(master, text="Calculate Volume", command=self.calculate_volume)
        self.calculate_button.pack()

        self.result_label = Label(master, text="")
        self.result_label.pack()

    def calculate_volume(self):
        try:
            base_area = float(self.entry_base_area.get())
            height = float(self.entry_height.get())
            volume = (1/3) * base_area * height
            self.result_label.config(text=f"Volume: {volume:.2f}")
        except ValueError:
            self.result_label.config(text="Please enter valid numbers.")