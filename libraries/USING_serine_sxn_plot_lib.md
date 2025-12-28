# Quick Guide: serine_sxn_plot_lib.py

## What this script does
- Reads `serine_sxn_analysis.json` (or a sibling `.md`; it auto-switches to the `.json`).
- Generates plots in `plots/<partial|full|unknown>_sequence/n_<min>_to_<max>/` next to the input:
  - Serine content (count + fraction) across species, grouped by protein type.
  - Total [SX]_n coverage (% of sequence) across species, grouped by protein type (auto-splits into two panels if >30 species).
  - Motif counts and per-motif fractions per protein type (separate figure per type, grouped by n).
  - X-residue composition per protein type (stacked bar per species; legend only shows residues present for that type).
  - Taxonomy/phylogeny annotated with the protein types found per species.
- Filenames include the analysed n-range and category suffix (e.g., `..._n2-50_full.png`).

## How to run
```bash
uv run python serine_sxn_plot_lib.py path/to/serine_sxn_analysis.json
# You can also point at the .md; it will resolve to the .json automatically.
Example (from the repo root):
uv run python serine_sxn_plot_lib.py ncbi_spider_spidroin_sequences/serine_sxn_analysis.json
```

## Inputs
- A valid `serine_sxn_analysis.json` produced by `serine_sxn_analysis_lib.analyze_from_root(...)`.
- The script infers everything from that JSON (organism, type, partial/full, motif runs, X counts, serine stats, n-range).

## Outputs
- A `plots/` directory placed alongside the input file (created if needed; files overwrite) with subfolders per category and n-range.
- PNGs:
  - `serine_content_n{min}-{max}_{full|partial|unknown}.png`
  - `total_sxn_coverage_n{min}-{max}_{full|partial|unknown}.png`
  - `sxn_motifs_{type}_n{min}-{max}_{full|partial|unknown}.png` (one per protein type)
  - `x_composition_{type}_n{min}-{max}_{full|partial|unknown}.png` (one per protein type)
  - `phylo_types_n{min}-{max}_{full|partial|unknown}.png`

## Notes
- Plots are generated separately for full, partial, and unknown sequences (if present).
- Protein types come from the JSON (`type` field); all distinct types get plotted.
- Organism names are title-cased on the x-axis; bars are grouped by protein type.
- Species with no data for a given plot are omitted automatically.
- If the JSON has no records, the script exits quietly without writing plots.
