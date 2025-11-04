# Writing the Functions


I created a function that determines the required water volume for preparing a solution based on the desired concentration and known mass of LiBr.

I wrote this calculator independently, with help from Gabor to resolve the errors I encountered during the coding process.

I used Chat Copilot in Visual Studio Code to create the application

## Writing the calculator

First, I outlined the program's logic in my notes. 
As we learned in the lecture, I added a "try" block to ensure that the values input by the user are numbers.

Since people can often confuse units, I asked the user to confirm that they noticed the units being used. To achieve this, I used a while loop that continues to prompt the user to confirm until they type 'Y' (yes) to confirm their input.

The program then checks if the user has entered valid values before proceeding.

Once the inputs are verified, the program performs the calculations and returns the desired volume of water to the user.

## Replicate and adapt for the opposite situation

Next, I duplicated the script and modified the parameters and equations so that the program calculates the required mass of LiBr needed to prepare a solution with a desired concentration, given a known volume.

## Creating the application.

Finally, I used Chat Copilot in Visual Studio Code to merge the two scripts into a single application. In this application, users can choose whether they want to determine the required water volume for a given mass or the required mass for a known volume.

# The promots

## asking for creating the application

hi, I created 2 programs, which calculated the required mass or volume for wanted concetration. i want that them both to be in application gui, so the user of this application will be able to chose if he wants to know the required water volume to use known mass of LiBr to get the wanted concetration or if he wants to know the required mass of LiBr to use known H2O to get wanted concetration.

one program called "LiBr_con_mass_LiBr.py" and "LiBr_con_volume_H2O.py"

and here attached the codes:
[Here I sent the whole two files I wrote]

pls, create that gui application file for me at this folder

## asking how to initiate the application

how I can initiate this gui application? means, what I need to write in the terminal to operate this application?

## asking for including the confirming message in the app

HI
I noticed when I initiates the application, before the calculation, I am not getting conferming massege the I am confirm that I noticed the units..
can you fix it?

## Please notice the app direction

Notice that the main.py file is found in the src folder.

 uv run .\day02\libr-calculator\src\main.py