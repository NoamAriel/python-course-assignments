# Setific introduction

Silk fibers are known for their unique combination of mechanical characteristics of strength, extensibility, and toughness. These features result from silk’s highly hierarchical structure, shaped by the protein’s self-assembly during the natural fiber’s spinning. (https://www.nature.com/articles/s41467-024-50879-9)

In our laboratory, we aim to learn from nature how to synthesize silk. To achieve this, we need to break down natural silk to obtain its basic building blocks. We start by degumming silkworm silk and then dissolve it in a lithium bromide (LiBr) solution at a concentration of 9.3 M.

# Please notice the app direction

Notice that the main.py file is found in the src folder.

 uv run .\day03\libr-calculator\src\main.py


if you wants to use run the calculator without using the GUI application, you may type the following in the terminal:

 uv run .\day03\main.py

 ## Dependencies

For installing dependencies, type 
"
uv pip install pytest
"
in the terminal

## Tests

The tests verify whether the program generates errors when the user enters text instead of numbers, and what happens when the user enters inputs less than or equal to zero. We expect to get errors in those cases, and the program should alert the user for invalid inputs.

If you wants to run the test, pls type in terminal one of the following commands: 

uv run pytest
uv run pytest -v
uv run pytest -v -rA
uv run pytest --tb=no


## Test example

For example, I type the command " uv run pytest -v "
and Python returned the following as a result:

================================================== test session starts ===================================================
platform win32 -- Python 3.13.9, pytest-9.0.1, pluggy-1.6.0 -- C:\python\course\assiments\python-course-assignments\day03\.venv\Scripts\python.exe
cachedir: .pytest_cache
rootdir: C:\python\course\assiments\python-course-assignments\day03
configfile: pyproject.toml
collected 20 items

test_bus_log.py::test_calculate_LiBr_mass_standard PASSED                                                           [  5%]
test_bus_log.py::test_calculate_volume_H2O_standard PASSED                                                          [ 10%]
test_bus_log.py::test_calculate_LiBr_mass_text_input[text-1.0] PASSED                                               [ 15%]
test_bus_log.py::test_calculate_LiBr_mass_text_input[0.5-text] PASSED                                               [ 20%]
test_bus_log.py::test_calculate_LiBr_mass_text_input[text-text] PASSED                                              [ 25%]
test_bus_log.py::test_calculate_volume_H2O_text_input[text-1.0] PASSED                                              [ 30%]
test_bus_log.py::test_calculate_volume_H2O_text_input[43.4225-text] PASSED                                          [ 35%]
test_bus_log.py::test_calculate_volume_H2O_text_input[text-text] PASSED                                             [ 40%]
test_bus_log.py::test_calculate_LiBr_mass_zero_values_raises_error[0.0-1.0] PASSED                                  [ 45%]
test_bus_log.py::test_calculate_LiBr_mass_zero_values_raises_error[0.5-0.0] PASSED                                  [ 50%]
test_bus_log.py::test_calculate_LiBr_mass_zero_values_raises_error[0.0-0.0] PASSED                                  [ 55%]
test_bus_log.py::test_calculate_volume_H2O_zero_values_raises_error[0.0-1.0] PASSED                                 [ 60%]
test_bus_log.py::test_calculate_volume_H2O_zero_values_raises_error[43.4225-0.0] PASSED                             [ 65%]
test_bus_log.py::test_calculate_volume_H2O_zero_values_raises_error[0.0-0.0] PASSED                                 [ 70%]
test_bus_log.py::test_calculate_LiBr_mass_negative_values_raises_error[-0.5-1.0] PASSED                             [ 75%]
test_bus_log.py::test_calculate_LiBr_mass_negative_values_raises_error[0.5--1.0] PASSED                             [ 80%]
test_bus_log.py::test_calculate_LiBr_mass_negative_values_raises_error[-0.5--1.0] PASSED                            [ 85%] 
test_bus_log.py::test_calculate_volume_H2O_negative_values_raises_error[-43.4225-1.0] PASSED                        [ 90%] 
test_bus_log.py::test_calculate_volume_H2O_negative_values_raises_error[43.4225--1.0] PASSED                        [ 95%] 
test_bus_log.py::test_calculate_volume_H2O_negative_values_raises_error[-43.4225--1.0] PASSED                       [100%] 

=================================================== 20 passed in 0.05s ===================================================


# The promots

## asking for craeting program that merge the two functions, and asking the user which calculation he wants to use- Copilot (free version)

Hi,
I want to create a new program that asking from the user to choose which calculation he wants to do, in meaning of programs, he will chosse between "LiBr_con_mass_LiBr.py" and "LiBr_con_volume_H2O.py"
pls help me.

## asking for creating "business logic" file -Copilot (free version)

Hi,
I wants to copy the business logic from the files "LiBr_con_mass_LiBr.py" and"LiBr_con_volume_H2O.py"
into new file.
could you pls creates this for me?

## asking for creating tests file - Gemini (free version)

pls creates a pytest file that test the "business logic".
for expamle, test each parameter input (sepertlly), what will happen if the input is text.
then, test each parameter what will happen with zero value
then test each parameter with negative value
