# this script does serine and serine-X motif analysis and plotting, without ncbi sequence download.
# hence, for each run, you need to have the sequences already downloaded in a folder, and make sure to set the path to that folder.


# format_sxn_analysis_and_plotting.py
# This script performs serine and serine-X motif analysis on protein sequences
# and generates plots based on the analysis results. 
# It uses helper functions from serine_sxn_analysis_lib and serine_sxn_plot_lib.
# Adjust the filter parameters and motif length range as needed.
# Import necessary modules and set up the library path for custom libraries.
# Make sure to have the required libraries in the 'libraries' directory.
# You can modify the main function as needed.
# The script performs two main tasks:
# 1) Analyze serine and serine-X motifs in protein sequences from a specified root directory.
# 2) Generate plots based on the analysis results.  


from pathlib import Path
import sys
import time

BASE = Path(__file__).resolve().parent
PROJECT_ROOT = BASE.parent
LIB_ROOT = PROJECT_ROOT / "libraries"
for path in (PROJECT_ROOT, LIB_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from serine_sxn_plot_lib import main as plot_main
from serine_sxn_analysis_lib import analyze_from_root
from serine_sxn_plot_lib import (
    category_out_dir,
    ensure_out_dir,
    load_summary,
    plot_motif_counts_and_fraction,
    plot_phylo_types,
    plot_serine,
    plot_total_sxn,
    plot_x_composition,
    filter_records,
)

tic = time.perf_counter()

# do not change anything above this line and in the run_plots function.
# You can modify the main function as needed.

def _plot_records(
    records,
    summary,
    json_path: Path,
    min_n: int,
    max_n: int,
    *,
    out_dir_override: Path | None = None,
    tables_dir: Path | None = None,
) -> None:
    """Shared plotting core."""
    out_dir = out_dir_override or ensure_out_dir(json_path)
    categories = ["full", "partial", "unknown"]
    present = {r.get("partial_full", "unknown") for r in records}
    for cat in categories:
        if cat not in present:
            continue
        subset = [r for r in records if r.get("partial_full", "unknown") == cat]
        if not subset:
            continue
        label = cat
        cat_out_dir = category_out_dir(out_dir, cat, min_n, max_n)
        sub_summary = {**summary, "analyzed_records": subset}
        plot_serine(sub_summary, cat_out_dir, min_n, max_n, suffix=label, tables_dir=tables_dir)
        plot_total_sxn(sub_summary, cat_out_dir, min_n, max_n, suffix=label, tables_dir=tables_dir)
        plot_motif_counts_and_fraction(sub_summary, cat_out_dir, min_n, max_n, suffix=label, tables_dir=tables_dir)
        plot_x_composition(sub_summary, cat_out_dir, min_n, max_n, suffix=label, tables_dir=tables_dir)
        plot_phylo_types(sub_summary, cat_out_dir, min_n, max_n, suffix=label)
    print(f"Plots written under: {out_dir}")


def run_plots(
    json_path: Path,
    min_n: int,
    max_n: int,
    *,
    out_dir_override: Path | None = None,
    tables_dir: Path | None = None,
) -> None:
    """Generate all plots using the serine_sxn_plot_lib helpers."""
    summary = load_summary(json_path)
    records = summary.get("analyzed_records", [])
    if not records:
        print("No records to plot; skipping plotting.")
        return
    _plot_records(
        records,
        summary,
        json_path,
        min_n,
        max_n,
        out_dir_override=out_dir_override,
        tables_dir=tables_dir,
    )


def run_filtered_plots(
    json_path: Path,
    min_n: int,
    max_n: int,
    *,
    taxonomy_terms=None,
    protein_types=None,
    partial_full=None,
    length_range=None,
    length_threshold=None,
    length_mode="ge",
    longest_factor=None,
    longest_factor_scope="species",
    out_dir_override: Path | None = None,
    tables_dir: Path | None = None,
) -> None:
    """Load summary, apply filters, then plot."""
    summary = load_summary(json_path)
    records = summary.get("analyzed_records", [])
    filtered = filter_records(
        records,
        taxonomy_terms=taxonomy_terms,
        protein_types=protein_types,
        partial_full=partial_full,
        length_range=length_range,
        length_threshold=length_threshold,
        length_mode=length_mode,
        longest_factor=longest_factor,
        longest_factor_scope=longest_factor_scope,
    )
    if not filtered:
        print("No records remain after filtering; skipping plotting.")
        return
    filtered_summary = {**summary, "analyzed_records": filtered}
    _plot_records(
        filtered,
        filtered_summary,
        json_path,
        min_n,
        max_n,
        out_dir_override=out_dir_override,
        tables_dir=tables_dir,
    )

# Path to your serine_sxn_analysis JSON (or .md)
analysis_path = Path("ncbi_fibroin_sequences/serine_sxn_analysis.json")

# Optional overrides:
# - data_root: where the ncbi_fibroin_sequences live (absolute or relative to this file).
# - plots_root: where plots should be written (absolute or relative). Leave as None to use default next to analysis JSON.
data_root: Path | None = None#Path(r"D:\python\LHuge_data_for_bioinformatic_project\moths_and_butterflies\ncbi_fibroin_sequences") # or None for default
plots_root: Path | None = None #Path(r"D:\python\Lab\moths_and_butterflies\ncbi_fibroin_sequences") # or None for default
tables_root: Path | None = None #Path(r"D:\python\Lab\caddisfly\ncbi_fibroin_sequences\tables") # or None for default

# --- Filters (edit to taste) ---
taxonomy_terms = ["trichoptera"]       # or [] / None
protein_types = ["heavy chain"]        # or [] / None 
partial_full = "full"                  # "full", "partial", or None
length_range = None                    # e.g.,(100, 2450) or None
length_threshold = None                # e.g., 1500 or None
length_mode = "ge"                     # optional, default is "ge". ge: greater equal, le: less equal
longest_factor = 2.0                  # optional default is 2.0 which means shorest sequence can be at least half as long as longest one.
longest_factor_scope = "species"       # "species" (per organism) or "global" (all records)


def run_example() -> None:
    argv = [str(BASE / analysis_path)]
    if taxonomy_terms:
        argv += ["--taxonomy", *taxonomy_terms]
    if protein_types:
        argv += ["--type", *protein_types]
    if partial_full is not None:
        argv += ["--partial-full", partial_full]
    if length_range:
        argv += ["--length-range", str(length_range[0]), str(length_range[1])]
    if length_threshold is not None:
        argv += ["--length-threshold", str(length_threshold), "--length-mode", length_mode]
    if longest_factor is not None:
        argv += ["--longest-factor", str(longest_factor)]
    if longest_factor_scope:
        argv += ["--longest-factor-scope", str(longest_factor_scope)]

    # serine_sxn_plot_lib.main parses sys.argv; set it temporarily
    sys.argv = ["serine_sxn_plot_lib.py", *argv]
    plot_main()



def main() -> None:

    # 1) Analyze serine + [SX]_n motifs in the downloaded folder
    # here you should modify the motif length range (min_n, max_n) as you interest.
    #  for example, if you want to analyze motifs with length between 2 and 50, you can set min_n=2 and max_n=50.
    # if you modify  these values, make sure to use the same values in the run_plots function below.
    
    min_n = 3 # minimum motif length
    max_n = 50 # maximum motif length

    resolved_data_root = data_root if data_root and data_root.is_absolute() else (BASE / (data_root or "ncbi_fibroin_sequences"))
    root = resolved_data_root.resolve()
    resolved_plots_root = None
    if plots_root:
        resolved_plots_root = plots_root if plots_root.is_absolute() else (BASE / plots_root)
        resolved_plots_root = resolved_plots_root.resolve()
    resolved_tables_root = None
    if tables_root:
        resolved_tables_root = tables_root if tables_root.is_absolute() else (BASE / tables_root)
        resolved_tables_root = resolved_tables_root.resolve()

    json_path, md_path = analyze_from_root(root, max_n=max_n, min_n=min_n)
    print(f"Analysis JSON: {json_path}")
    print(f"Analysis MD  : {md_path}")

    # 2) Generate plots automatically with filters applied here
    run_filtered_plots(
        json_path,
        min_n=min_n,
        max_n=max_n,
        taxonomy_terms=taxonomy_terms,
        protein_types=protein_types,
        partial_full=partial_full,
        length_range=length_range,
        length_threshold=length_threshold,
        length_mode=length_mode,
        longest_factor=longest_factor,
        longest_factor_scope=longest_factor_scope,
        out_dir_override=resolved_plots_root,
        tables_dir=resolved_tables_root or (root / "tables"),
    )


if __name__ == "__main__":
    main()

toc = time.perf_counter()
print(f"Elapsed: {toc - tic:0.3f} seconds")
