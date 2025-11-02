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
    except ValueError: print("Invalid input: Please enter numeric values for H2O volume and wanted concentration.")
    
   
    print("Please confirm that the H2O volume is in mL and the wanted concentration is in mol/L.")
    intuitive_input = input("Type 'Y' to confirm or 'N' to try again: ").strip().lower()
    if intuitive_input != 'Y':
        print("Operation cancelled. Please provide the correct inputs.")
    elif intuitive_input == 'N': 
        return LiBr_con_mass_LiBr(input("Enter the volume of H2O (g): "), input("Enter the wanted concentration (mol/L): "))
   
   

    Molar_mass_of_LiBr = 86.845  # g/mol
    volume_H2O = volume_H2O * 0.001  # Convert mL to L
    mols_of_LiBr = volume_H2O * wanted_concetration
    LiBr_mass =  mols_of_LiBr * Molar_mass_of_LiBr
     
    return  print("Required mass of LiBr (g):", LiBr_mass)

volume =input("Enter the volume of H2O (mL): ")
concentration = input("Enter the wanted concentration (mol/L): ")
LiBr_con_mass_LiBr(volume, concentration)
