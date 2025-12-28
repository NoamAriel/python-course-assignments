First, I apologize, but since I worked hard on it and it may be published, I have made this repository private. Hence, I provided you with access to Gabor, Hodia, and Liron.

Disclaimer: I utilize the “Codex” extension for programming and connecting to ChatGPT 5.2. I do not add prompts because there are too many of them.

order of operating:

pls make sure you install the dependencies: ["requests", "pandas", "numpy", "matplotlib"]

pls make sure you download the libraries folder

pls make sure you have the files: 

1.	ncbi_scrapper.py, 

2.	run_generate_species_index.py, 

3.	run_generate_taxonomy_graph.py 

4.	sxn_analysis_and_plotting.py.

This is also the operating order. 


Now, I want to explain my code:

I used the dataset of fibroin proteins from the caddisfly, which was found in the NCBI database.

Previously, we successfully downloaded the data, saved it, and characterized it using both full and partial sequences, as well as heavy chain and light chain.

This time, I added some improvements:

The “ncbi_scrapper.py” (in day06 task, it is called “main.py”) script, in addition to downloading data from NCBI, saves the taxonomy for each species in MD and JSON files, named phylo_tree.

I used the logic behind the NCBI scrapper, the analyzing and plotting of [SX]n motifs, and created library files for more convenient use, and for the future, to do the same analysis and plotting for other proteins of other animals (like spiders, ants, bees, wasps, moths, butterflies, etc.).

Then, I created a fixed color map for each amino acid, so the X-residue composition graph and future plots will use the same color for each amino acid. That will help with an easier understanding of the different plots.

Then, I created library files to index the dataset downloaded from NCBI, for convenient handling of the data.
Then, based on the taxonomy that is known in the NCBI, I created library files that generate a phylogenetic tree. This is important for understanding the present data in the graphs.

To determine if the libraries are functioning as expected, I created test files (saved in the “tests” folder located within the libraries folder). Then, I created format files that call the library files for analysis and plotting.

Then, I added MD files into the libraries folder that explain how to use the library files.

Then, I added a filtering system to the file “run_generate_taxonomy_graph.py” (phylogenetic tree generation) and “sxn_analysis_and_plotting.py” (analysis of the sequences by finding [SX]n motifs). An explanation of the filtering system is attached at the end of this README.

Then, I add a “tic tac” method for each file to see how much time each file takes to run. That helped me, for example, to identify that the “ncbi_scrapper.py” and its related library run with a complexity of O(n^2), and I succeeded in reducing its complexity to O(n), which saved a lot of time.

Then, since some species have more than one data file for a protein type, I calculate the standard deviation and add error bars to the relevant graphs.

Then, I updated the code so that it will save the plot's data in tables. When publishing an article, it will be useful to have data support.

The filters are used to provide better control over presenting the data, resulting in more coherent, convenient, and understandable graphs. The specific filters are dependent on the graphs, since not all of them are relevant for all plots. 

The filters are:
taxonomy_terms		 # filtering by the taxonomy name (trichoptera, for example). could be used by any taxonomy rank.  Default is [] / None

protein_types			# filtering by the type of protein (heavy chain, for example), default is [] / None. 

partial_full 			# filtering by sequence, if it is reported as partial or full. 

length_range 			# filtering by range sequence that interests, e.g., (100, 2450). Default is None.

length_threshold 		# filtering by threshold sequence that interests, e.g., 1500. default is None.

length_mode 			# determining if the threshold is “ge”: greater equal or “le”: less equal. The default is "ge". 

longest_factor = 2.0                  # optional default is 2.0, which means the shortest sequence can be at least half as long as the longest one.

longest_factor_scope  	# determining if the above length filters correspond to each species by itself, or all length sequences, or are relevant, even though they are from different species. In short, "species" (per organism) or "global" (all records). The default is "species".

Special filters

In file” sxn_analysis_and_plotting”, in 273- 274 rows, there is an option to choose the range of n (min_n is the minimum motif length and max_n = 50 is the maximum motif length). There is not default. The user has to specify it.

In the file “run_generate_taxonomy_graph”, there is an option to choose the first and the last rank that the phylogenetic tree will present. Rank type (like superfamily) or ranks name (like Hydropsychoidea) are valid. The default is None.





