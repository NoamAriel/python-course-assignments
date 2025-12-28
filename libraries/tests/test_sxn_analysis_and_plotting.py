from pathlib import Path
import sys

BASE = Path(__file__).resolve().parent
LIB_ROOT = BASE / "libraries"
if str(LIB_ROOT) not in sys.path:
    sys.path.insert(0, str(LIB_ROOT))

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
)

# do not change anything above this line and in the run_plots function.
# You can modify the main function as needed.

def run_plots(json_path: Path, min_n: int, max_n: int) -> None:
    """Generate all plots using the serine_sxn_plot_lib helpers."""
    summary = load_summary(json_path)
    out_dir = ensure_out_dir(json_path)
    records = summary.get("analyzed_records", [])
    if not records:
        print("No records to plot; skipping plotting.")
        return

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
        plot_serine(sub_summary, cat_out_dir, min_n, max_n, suffix=label)
        plot_total_sxn(sub_summary, cat_out_dir, min_n, max_n, suffix=label)
        plot_motif_counts_and_fraction(sub_summary, cat_out_dir, min_n, max_n, suffix=label)
        plot_x_composition(sub_summary, cat_out_dir, min_n, max_n, suffix=label)
        plot_phylo_types(sub_summary, cat_out_dir, min_n, max_n, suffix=label)
    print(f"Plots written under: {out_dir}")

# Path to your serine_sxn_analysis JSON (or .md)
analysis_path = Path(r"caddisfly/ncbi_fibroin_sequences/serine_sxn_analysis.json")

# --- Filters (edit to taste) ---
taxonomy_terms = ["trichoptera"]       # or [] / None
protein_types = ["heavy chain"]        # or [] / None
partial_full = "full"                  # "full", "partial", or None
length_range = None                    # e.g.,(100, 2450) or None
length_threshold = None                # e.g., 1500 or None
length_mode = "ge"                     # "ge" or "le" where "ge" means >= threshold and "le" means <= threshold.
longest_factor = 2.0                   # float > 1 or None


def run_example() -> None:
    argv = [str(analysis_path)]
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

    # serine_sxn_plot_lib.main parses sys.argv; set it temporarily
    sys.argv = ["serine_sxn_plot_lib.py", *argv]
    plot_main()



def main() -> None:
    min_n = 3
    max_n = 60
    # 1) Analyze serine + [SX]_n motifs in the downloaded folder
    # here you should modify the motif length range (min_n, max_n) as you interest.
    #  for example, if you want to analyze motifs with length between 2 and 50, you can set min_n=2 and max_n=50.
    # if you modify  these values, make sure to use the same values in the run_plots function below.
    base = BASE
    root = (base / analysis_path.parent).resolve()
    json_path, md_path = analyze_from_root(root, max_n=max_n, min_n=min_n)
    print(f"Analysis JSON: {json_path}")
    print(f"Analysis MD  : {md_path}")

    # 2) Generate plots automatically
    run_plots(json_path, min_n=min_n, max_n=max_n)


if __name__ == "__main__":
    main()
