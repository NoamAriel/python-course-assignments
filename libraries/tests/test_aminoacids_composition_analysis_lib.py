from pathlib import Path
from libraries.aminoacids_composition_analysis_lib import analyze_from_root

root = Path(r"D:\python\Lab\caddisfly\ncbi_fibroin_sequences")

json_path, md_path = analyze_from_root(
    root=root,
    letters="s",                    # letters you care about
    taxonomy_terms=["trichoptera"],  # optional
    protein_types=["heavy chain"],    # optional
    partial_full="full",              # default is "full"
    # length_range=(100, 2450),         # or None
    # length_threshold=1500, length_mode="ge",
     longest_factor=2.0,
)
print(json_path, md_path)
