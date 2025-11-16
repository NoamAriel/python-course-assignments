def LiBr_con_mass_LiBr(volume_H2O,wanted_concetration):
      
    """
Calculate the required LiBr mass to achieve a desired LiBr concentration.
    
    Formula: V = (mols of LiBr/ wanted_concetration)
    mols of LiBr= LiBr_mass / Molar mass of LiBr (86.845 g/mol)
    
    Args:
        volume_H2O(float): Volume in mL
        LiBr_mass (float): Mass of LiBr in grams
        wanted_concetration (float): Desired concentration in mol/L
    
    Returns:
        the required volume of H2O in mL
    """
   
    try:
       volume_H2O = float(volume_H2O) 
       wanted_concetration = float(wanted_concetration)
    except ValueError: 
        print("Invalid input: Please enter numeric values for H2O volume and wanted concentration.")
        return # Exit the function on non-numeric input
    
    while True:
        # --- NEW VALIDATION CHECK ---
        if volume_H2O <= 0 or wanted_concetration <= 0:
            print("Invalid input: Volume and concentration must be positive values (greater than zero).")
            intuitive_input = 'n' # Force the user to re-enter
        # --- END NEW VALIDATION CHECK ---
        else:
            print("Please confirm that the H2O volume is in mL and the wanted concentration is in mol/L.")
            intuitive_input = input("Type 'Y' to confirm or 'N' to try again: ").strip().lower()
        
        if intuitive_input == 'y':
            break 
            
        elif intuitive_input == 'n': 
            print("Please provide the correct inputs.")
            
            new_volume = input("Enter the volume of H2O (mL): ") 
            new_concentration = input("Enter the wanted concentration (mol/L): ")
            
            try:
                volume_H2O = float(new_volume)
                wanted_concetration = float(new_concentration)

                # Re-validate the new numeric inputs immediately
                if volume_H2O <= 0 or wanted_concetration <= 0:
                    print("Invalid input: The new values must be positive. Let's try again.")
                    continue 
                    
            except ValueError:
                print("Invalid input, The new values must be numeric. Let's try again.")
                continue 
        
        else:
             print("Invalid choice. Please type 'Y' or 'N'.")
   

    Molar_mass_of_LiBr = 86.845  # g/mol
    volume_H2O = volume_H2O * 0.001  # Convert mL to L
    mols_of_LiBr = volume_H2O * wanted_concetration
    LiBr_mass =  mols_of_LiBr * Molar_mass_of_LiBr
     
    return  print("Required mass of LiBr (g):", LiBr_mass)

volume =input("Enter the volume of H2O (mL): ")
concentration = input("Enter the wanted concentration (mol/L): ")
LiBr_con_mass_LiBr(volume, concentration)
