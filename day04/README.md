# The NCBI fibroin scapper

In the phylogenetic tree, there is an order called "Trichoptera" (caddisfly). 
Those insects living in the larva stage in fresh/creek waters, and in the adult stage they become moths.
My study focuses on them due to their special silk, which, in addition to the special properties of silk, including strength, extensibility, and toughness, is stable and adhesive in an aquatic environment.

Since there are many species of caddisfly, which all produce silk with the same properties, it will be interesting to look in the protein sequence of the fibroin (heavy chain and light chain) and compare the sequences. by thisw comparing we will be able to indicates which amino acids coserve and importent for creating the silk and which amino acids are not conserve, and there is some freedom of which amino acidsd can be in the spesific location, which motifs are importent for the silk etc.

To do so, the code searches each family of caddisfly (extracted from wikipedia), plus the word "fibroin," on the NCBI website and saves the data sequence folder (ncbi_fibroin_sequences) in a nested structure (suborder -> superfamily -> family -> species). The code also indicates whether the sequence is full or partial, whether the data pertains to a heavy chain, a light chain, or another sequence (which is not relevant to our purpose). For convenience, the code saves the data in two file types: "fasta" for future analysis and "md" for user readability.


# deleting __pycache__ folders

I was unable to create a ".gitignore" file that automatically removes the "__pycache__" folder when it is created. Both Gemini and ChatGPT informed me that Gitignore is only able to ignore files, not delete them.
in order to delete this folder, I created the file ".git/hooks/pre-commit" with the following code:

"
#!/bin/bash
echo "Deleting __pycache__ folders before commit..."
find . -type d -name "__pycache__" -exec rm -r {} +
"

Now, by typing the following command in the terminal

"
 git commit -m "message" 
"

the "__pycache__" folder will be removed.


## promots (chatGPT free version)

hi i am using Visual Studio Code for writing code in python. when I am using "pytest", a new folder called "__pycache__" is created. I want to creates a ".gitignore" file that will delete the folder "__pycache__" every time it created. could you help me pls?

# promots (Gemini free)

## asking for Web Scraping from wikipedia- to got the data about the animals I want to know their fibroin sequence.

hi

I want to write a program that know to extract the all familiy names in the order Trichoptera.

to extract the data, the program should etract it from the following website:

https://en.wikipedia.org/wiki/Caddisfly

## Then, the program didn't succeed, so the AI and I did debugging in that way. I copied the code the AI wrote, ran it, and sent the output I received from Python back to the AI. We performed 10 cycles of debugging in this manner until we achieved the final version, which is now working.

## Requesting code to extract fibroin data from NCBI for each caddisfly species obtained from Wikipedia, and to construct the nest structure.

"
hi
Now, after we succeeded in achieving this, I want to go to the next level.
I want to do website scarpering in the website "www.ncbi.nlm.nih.gov"
 I want the code will select "protein" instead  of "All Databases"
Then, I want the code to search the name of caddisfly + fibroin, and then click on "Search".
The name of the caddisfly should be taken from the output of the script "caddisfly_scraper.py" that we created. For example, the code will search the terms: 
Hydropsychidae fibroin and  Limnephilidae fibroin (separately).
Then, I want the code to open a new folder for each term search (like Limnephilidae fibroin). 
 Then I want the code will click on all items that are found in the search, and will download or copy the protein sequence (this data is found after the subtitle "ORIGIN")
The download file (or the copied data) will be called the item name (the name that we click on before arriving on the data sheet page)
Then, I want the code to separate between files with the word 'partial' and files without this word.
The separation will be in the sense of saving the files with 'partial' word in their name, into a folder called 'partial sequence', and all other files will be saved in another folder called ' full sequence'.

can you do so for me?
"

## Then, I did debugging with the AI. I copied the code, wrote it, ran it, and sent back the output I got from Python until I got the code that downloads the data as I wanted.

## When I received the results I wanted, I discovered that the code downloads data from silkworms, which do not belong to the caddisfly order. I noted that sometimes, even when our search does not yield the expected results, NCBI still provides some outcomes. I then instructed that this information should be overlooked.

I found a logic bug in the code.
I need an improvment that in case the searching claims the following:
"
The following term was not found in Protein:
"
that is mean, there is no result for my searching purpose
and the code should not download the data