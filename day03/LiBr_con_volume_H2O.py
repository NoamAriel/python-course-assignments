def LiBr_con_volume_H2O(LiBr_mass,wanted_concetration):
      
    """
Calculate the required H2O volume to achieve a desired LiBr concentration.
    
    Formula: V = (mols of LiBr/ wanted_concetration)
    mols of LiBr= LiBr_mass / Molar mass of LiBr (86.845 g/mol)
    
    Args:
        LiBr_mass (float): Mass of LiBr in grams
        wanted_concetration (float): Desired concentration in mol/L
    
    Returns:
        the required volume of H2O in mL
    """
   
    try:
       LiBr_mass = float(LiBr_mass) 
       wanted_concetration = float(wanted_concetration)
    except ValueError: print("Invalid input: Please enter numeric values for LiBr mass and wanted concentration.")
    
   
    while True:
        print("Please confirm that the LiBr mass is in g and the wanted concentration is in mol/L.")
        intuitive_input = input("Type 'Y' to confirm or 'N' to try again: ").strip().lower()
        
        if intuitive_input == 'y':
            break 
            
        elif intuitive_input == 'n': 
            print("Please provide the correct inputs.")
            
            new_mass = input("Enter the mass of LiBr (g): ") 
            new_concentration = input("Enter the wanted concentration (mol/L): ")
            
            try:
                volume_H2O = float(new_mass)
                wanted_concetration = float(new_concentration)
            except ValueError:
                print("Invalid input, The new values must be numeric. Let's try again.")
                continue 
        
        else:
             print("Invalid choice. Please type 'Y' or 'N'.")
   

   

    Molar_mass_of_LiBr = 86.845  # g/mol
    mols_of_LiBr= LiBr_mass / Molar_mass_of_LiBr
    volume_H2O = mols_of_LiBr / wanted_concetration
    volume_H2O = volume_H2O * 1000  # Convert L to mL
   
    return  print("Required volume of H2O (mL):", volume_H2O)

mass =input("Enter the mass of LiBr (g): ")
concentration = input("Enter the wanted concentration (mol/L): ")
LiBr_con_volume_H2O(mass, concentration)