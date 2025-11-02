print("Hello World from Noam Ariel [:")

try:
    with open("assiments/day02/hello_world.py", "r") as file:
        content = file.read()
        print("File content successfully read.")
except FileNotFoundError:
    print("The file was not found.")
except Exception as e:
    print(f"An error occurred: {e}")

    pass
...

if __name__ == "__main__":
    pass  # Placeholder for future code 

# to run this program, write uv run .\day02\hello_world.py  in the terminal