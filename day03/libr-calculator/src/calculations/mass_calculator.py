def LiBr_con_mass_LiBr(volume_H2O, wanted_concentration):
    """
    Calculate the required mass of LiBr to achieve a desired concentration in a given volume of water.
    
    Formula: mass = V * wanted_concentration * Molar mass of LiBr
    where V is the volume of water in L and Molar mass of LiBr is 86.845 g/mol.
    
    Args:
        volume_H2O (float): Volume of water in mL
        wanted_concentration (float): Desired concentration in mol/L
    
    Returns:
        float: Required mass of LiBr in grams
    """
    
    Molar_mass_of_LiBr = 86.845  # g/mol
    volume_H2O_L = volume_H2O / 1000  # Convert mL to L
    mass_of_LiBr = volume_H2O_L * wanted_concentration * Molar_mass_of_LiBr
    
    return mass_of_LiBr