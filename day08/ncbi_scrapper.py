from pathlib import Path
import sys
import time

BASE = Path(__file__).resolve().parent
LIB_ROOT = (BASE.parent / "libraries")
sys.path.insert(0, str(LIB_ROOT))

from ncbi_protein_scraper_lib import run_ncbi_protein_scraper
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
        tables_dir = json_path.parent / "tables"
        plot_serine(sub_summary, cat_out_dir, min_n, max_n, suffix=label, tables_dir=tables_dir, partial_full=cat)
        plot_total_sxn(sub_summary, cat_out_dir, min_n, max_n, suffix=label, tables_dir=tables_dir, partial_full=cat)
        # Plot per type to avoid table path duplication inside the plotting library.
        types = sorted({r.get("type", "Unknown") for r in subset})
        for ptype in types:
            type_subset = [r for r in subset if r.get("type", "Unknown") == ptype]
            if not type_subset:
                continue
            type_summary = {**summary, "analyzed_records": type_subset}
            plot_motif_counts_and_fraction(
                type_summary,
                cat_out_dir,
                min_n,
                max_n,
                suffix=label,
                tables_dir=tables_dir,
                partial_full=cat,
            )
            plot_x_composition(
                type_summary,
                cat_out_dir,
                min_n,
                max_n,
                suffix=label,
                tables_dir=tables_dir,
                partial_full=cat,
            )
        plot_phylo_types(sub_summary, cat_out_dir, min_n, max_n, suffix=label)
    print(f"Plots written under: {out_dir}")


def main() -> None:
    # 1) Scrape NCBI protein records (example: caddisfly fibroins)
    # Here, you should specify the order and families relevant to caddisflies and the protein of interest (protein_terms) 
    # and expected types that were found in the NCBI database.
    tic = time.perf_counter()
    expected_types = {
    "heavy chain": [
        "heavy chain", "fib-h", "h-fibroin", "h chain", "fibroin heavy chain"
                        ],
    "light chain": [
        "light chain", "fib-l", "l-fibroin", "l chain", "fibroin light chain"
                        ],
                            }
        

    run_ncbi_protein_scraper(
        order_name="Trichoptera",
        protein_terms=["fibroin"],
        expected_types=expected_types,
        output_root=str(BASE / "ncbi_fibroin_sequences"),
    )

    # 2) Analyze serine + [SX]_n motifs in the downloaded folder
    # here you should modify the motif length range (min_n, max_n) as you interest.
    #  for example, if you want to analyze motifs with length between 2 and 50, you can set min_n=2 and max_n=50.
    # if you modify  these values, make sure to use the same values in the run_plots function below.
    base = Path(__file__).resolve().parent
    root = (base / "ncbi_fibroin_sequences").resolve()
    json_path, md_path = analyze_from_root(root, max_n=50, min_n=2)
    print(f"Analysis JSON: {json_path}")
    print(f"Analysis MD  : {md_path}")

    # 3) Generate plots automatically
    run_plots(json_path, min_n=2, max_n=50)

    toc = time.perf_counter()
    print(f"Completed in {toc - tic:0.4f} seconds")

if __name__ == "__main__":
    main()
