import subprocess
import sys

def main():
    print("=" * 50)
    print("LiBr Solution Calculator")
    print("=" * 50)
    print("\nChoose which calculation you want to perform:")
    print("1. Calculate H2O Volume (given LiBr mass)")
    print("2. Calculate LiBr Mass (given H2O volume)")
    print("3. Exit")
    print("-" * 50)
    
    choice = input("Enter your choice (1, 2, or 3): ").strip()
    
    if choice == '1':
        print("\nRunning H2O Volume Calculator...\n")
        subprocess.run([sys.executable, "LiBr_con_volume_H2O.py"])
    elif choice == '2':
        print("\nRunning LiBr Mass Calculator...\n")
        subprocess.run([sys.executable, "LiBr_con_mass_LiBr.py"])
    elif choice == '3':
        print("Exiting the application. Goodbye!")
        sys.exit()
    else:
        print("Invalid choice. Please enter 1, 2, or 3.")
        main()  # Ask again

if __name__ == "__main__":
    main()