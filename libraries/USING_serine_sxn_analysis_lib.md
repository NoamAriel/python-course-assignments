# Serine + [SX]_n Analysis Library

`serine_sxn_analysis_lib.py` provides helpers to compute serine content and [SX]_n motif stats on the JSON records created by your scraper.

## Typical Use
```python
from pathlib import Path
from serine_sxn_analysis_lib import analyze_from_root

root = Path("ncbi_spider_spidroin_sequences")  # folder with all per-record JSONs
json_path, md_path = analyze_from_root(root, max_n=50, min_n=2)
print("Saved:", json_path, md_path)
```
- `max_n`/`min_n` are clamped to 1..100 (defaults 50..2).
- Records are loaded automatically from all JSON files under `root` that contain `origin_sequence` (skips `phylo_tree.json`).

## Advanced
- To supply your own record list: `analyze_and_save(records, Path(...), max_n=..., min_n=...)`.
- To just run the motif search: use `greedy_sxn_runs(seq, max_n, min_n)`.
- Serine counts: `serine_stats(seq)`.

## Outputs
- JSON summary (default `serine_sxn_analysis.json`) with per-record metrics, type/species info, serine stats, motif runs, and X composition by n.
- Markdown summary (default `serine_sxn_analysis.md`) with totals, species coverage, and top records by motif residues.

## Notes
- Input records should include fields: `origin_sequence`, `accession`, `organism_name`, taxonomy (`taxonomy_from_araneae` or `taxonomy_full`), `partial_full`, `type`.
- Motif search is greedy longest-first and non-overlapping.

- Ensure the root directory exists; the analysis will create output files there.


