"""
Business logic for LiBr mass or H2O volume calculation:
Calculate the required LiBr mass to achieve a desired LiBr concentration.
    
    Formula: V = (mols of LiBr / wanted_concentration)
    mols of LiBr = LiBr_mass / Molar mass of LiBr (86.845 g/mol)
"""

MOLAR_MASS_LiBr = 86.845  # g/mol


def calculate_LiBr_mass(volume_H2O: float, wanted_concentration: float) -> float:
    """
    Calculate the required LiBr mass to achieve a desired concentration.
    
    Args:
        volume_H2O: Volume of water in liters
        wanted_concentration: Desired LiBr concentration in mol/L
    
    Returns:
        Required LiBr mass in grams
        
    Raises:
        ValueError: If volume_H2O or wanted_concentration is zero or negative.
    """
    # --- INPUT VALIDATION: Must be strictly positive ---
    if volume_H2O <= 0:
        raise ValueError("Volume of water must be a positive number (greater than zero).")
    if wanted_concentration <= 0:
        raise ValueError("Concentration must be a positive number (greater than zero).")
    # ----------------------------------------------------

    mols_of_LiBr = volume_H2O * wanted_concentration
    LiBr_mass = mols_of_LiBr * MOLAR_MASS_LiBr
    return LiBr_mass


def calculate_volume_H2O(LiBr_mass: float, wanted_concentration: float) -> float:
    """
    Calculate the required H2O volume to achieve a desired LiBr concentration.
    
    Args:
        LiBr_mass: Mass of LiBr in grams
        wanted_concentration: Desired LiBr concentration in mol/L
    
    Returns:
        Required H2O volume in milliliters
        
    Raises:
        ValueError: If LiBr_mass or wanted_concentration is zero or negative.
    """
    # --- INPUT VALIDATION: Must be strictly positive ---
    if LiBr_mass <= 0:
        raise ValueError("LiBr mass must be a positive number (greater than zero).")
    if wanted_concentration <= 0:
        raise ValueError("Concentration must be a positive number (greater than zero).")
    # ----------------------------------------------------
    
    mols_of_LiBr = LiBr_mass / MOLAR_MASS_LiBr
    volume_H2O = mols_of_LiBr / wanted_concentration
    volume_H2O_mL = volume_H2O * 1000  # Convert L to mL
    return volume_H2O_mL