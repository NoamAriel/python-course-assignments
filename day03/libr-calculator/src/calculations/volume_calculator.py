def LiBr_con_volume_H2O(LiBr_mass, wanted_concentration):
    """
    Calculate the required H2O volume to achieve a desired LiBr concentration.
    
    Formula: V = (mols of LiBr / wanted_concentration)
    mols of LiBr = LiBr_mass / Molar mass of LiBr (86.845 g/mol)
    
    Args:
        LiBr_mass (float): Mass of LiBr in grams
        wanted_concentration (float): Desired concentration in mol/L
    
    Returns:
        float: The required volume of H2O in mL
    """
    try:
        LiBr_mass = float(LiBr_mass) 
        wanted_concentration = float(wanted_concentration)
    except ValueError:
        print("Invalid input: Please enter numeric values for LiBr mass and wanted concentration.")
        return None

    Molar_mass_of_LiBr = 86.845  # g/mol
    mols_of_LiBr = LiBr_mass / Molar_mass_of_LiBr
    volume_H2O = mols_of_LiBr / wanted_concentration
    volume_H2O = volume_H2O * 1000  # Convert L to mL

    return volume_H2O