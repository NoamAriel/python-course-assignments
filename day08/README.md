need to eaplain here things

first, i have to apologize, but since i worked hard on it and it might be published, i make this represotery privete.

libraries
tic toc

index of the dataset for convinet
anayliszing by SXn (new- library, i can use it for another data set, and filters are new) + plots

create phylogentec tree (totaly new, also library) + plots

each function can be control by filtering system (
    taxonomy_terms = ["trichoptera"]       # or [] / None
protein_types = ["heavy chain"]        # or [] / None 
partial_full = "full"                  # "full", "partial", or None
length_range = None                    # e.g.,(100, 2450) or None
length_threshold = None                # e.g., 1500 or None
length_mode = "ge"                     # optional, default is "ge". ge: greater equal, le: less equal
longest_factor = 2.0                  # optional default is 2.0 which means shorest sequence can be at least half as long as longest one.
longest_factor_scope = "species"       # "species" (per organism) or "global" (all records)
)
and sxn controled by n mini and and max (269- 270 rows)

new ideas:

libraries
fixed color map to each amino acids
error bars