import pytest
from bus_log import calculate_LiBr_mass, calculate_volume_H2O, MOLAR_MASS_LiBr

# --- Fixtures for Test Data ---

@pytest.fixture
def standard_inputs():
    """Standard, valid inputs for both functions."""
    return {
        "volume_L": 0.5,
        "volume_mL": 500.0,
        "mass_g": 43.4225,  # Calculated mass for 0.5 L and 1.0 mol/L
        "concentration": 1.0
    }

# --- 1. Basic Functionality Tests (Unchanged) ---

def test_calculate_LiBr_mass_standard(standard_inputs):
    """Test mass calculation with standard, positive inputs."""
    expected_mass = standard_inputs["volume_L"] * standard_inputs["concentration"] * MOLAR_MASS_LiBr
    actual_mass = calculate_LiBr_mass(standard_inputs["volume_L"], standard_inputs["concentration"])
    assert actual_mass == pytest.approx(expected_mass)
    assert actual_mass == pytest.approx(standard_inputs["mass_g"])

def test_calculate_volume_H2O_standard(standard_inputs):
    """Test volume calculation with standard, positive inputs."""
    mols = standard_inputs["mass_g"] / MOLAR_MASS_LiBr
    expected_volume_L = mols / standard_inputs["concentration"]
    expected_volume_mL = expected_volume_L * 1000
    
    actual_volume_mL = calculate_volume_H2O(standard_inputs["mass_g"], standard_inputs["concentration"])
    assert actual_volume_mL == pytest.approx(expected_volume_mL)
    assert actual_volume_mL == pytest.approx(standard_inputs["volume_mL"])

# --- 2. Input Type Tests (Unchanged) ---

@pytest.mark.parametrize("volume, concentration", [
    ("text", 1.0),
    (0.5, "text"),
    ("text", "text")
])
def test_calculate_LiBr_mass_text_input(volume, concentration):
    """Test mass calculation when non-numeric (text) input is provided."""
    # These still expect TypeError as arithmetic on strings fails
    with pytest.raises(TypeError):
        calculate_LiBr_mass(volume, concentration)

@pytest.mark.parametrize("mass, concentration", [
    ("text", 1.0),
    (43.4225, "text"),
    ("text", "text")
])
def test_calculate_volume_H2O_text_input(mass, concentration):
    """Test volume calculation when non-numeric (text) input is provided."""
    # These still expect TypeError as arithmetic on strings fails
    with pytest.raises(TypeError):
        calculate_volume_H2O(mass, concentration)

# ----------------------------------------------------
# --- 3. UPDATED: Zero Value Tests (Expecting ValueError) ---

# Test Cases for calculate_LiBr_mass(volume_H2O, wanted_concentration)
@pytest.mark.parametrize("volume, concentration", [
    (0.0, 1.0),       # Zero volume
    (0.5, 0.0),       # Zero concentration
    (0.0, 0.0),       # Zero volume and concentration
])
def test_calculate_LiBr_mass_zero_values_raises_error(volume, concentration):
    """Test mass calculation with zero values, expecting ValueError due to validation."""
    with pytest.raises(ValueError):
        calculate_LiBr_mass(volume, concentration)

# Test Cases for calculate_volume_H2O(LiBr_mass, wanted_concentration)
@pytest.mark.parametrize("mass, concentration", [
    (0.0, 1.0),       # Zero mass
    (43.4225, 0.0),   # Zero concentration
    (0.0, 0.0),       # Zero mass and concentration
])
def test_calculate_volume_H2O_zero_values_raises_error(mass, concentration):
    """Test volume calculation with zero values, expecting ValueError due to validation."""
    with pytest.raises(ValueError):
        calculate_volume_H2O(mass, concentration)

# ----------------------------------------------------
# --- 4. UPDATED: Negative Value Tests (Expecting ValueError) ---

# Test Cases for calculate_LiBr_mass(volume_H2O, wanted_concentration)
@pytest.mark.parametrize("volume, concentration", [
    (-0.5, 1.0),      # Negative volume
    (0.5, -1.0),      # Negative concentration
    (-0.5, -1.0)      # Both negative
])
def test_calculate_LiBr_mass_negative_values_raises_error(volume, concentration):
    """Test mass calculation with negative volume or concentration, expecting ValueError."""
    with pytest.raises(ValueError):
        calculate_LiBr_mass(volume, concentration)

# Test Cases for calculate_volume_H2O(LiBr_mass, wanted_concentration)
@pytest.mark.parametrize("mass, concentration", [
    (-43.4225, 1.0),      # Negative mass
    (43.4225, -1.0),      # Negative concentration
    (-43.4225, -1.0)       # Both negative
])
def test_calculate_volume_H2O_negative_values_raises_error(mass, concentration):
    """Test volume calculation with negative mass or concentration, expecting ValueError."""
    with pytest.raises(ValueError):
        calculate_volume_H2O(mass, concentration)