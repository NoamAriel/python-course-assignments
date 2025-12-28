# ncbi_protein_scraper_lib: Quick Guide

This library provides a generic NCBI Protein scraper for building an ordered, phylogenetically nested dataset from search terms like `<family> <protein term>`. It pulls taxonomy, sequence, and metadata, then organizes outputs into directories and a simple tree JSON.

## Function

```python
run_ncbi_protein_scraper(
    order_name: str,
    family_names: List[str],
    protein_terms: Optional[List[str]] = None,
    expected_types: Optional[List[str]] = None,
    api_key: Optional[str] = None,
    output_root: str = "ncbi_sequences",
    sleep_time: float = 0.7,
) -> None
```

### Parameters
- `order_name`: Taxonomic anchor (e.g., `"Araneae"`, `"Trichoptera"`).
- `family_names`: List of family names to search (e.g., `['Limnephilidae', 'Hydropsychidae']`).
- `protein_terms`: Search tokens appended to family (default `['fibroin']`; e.g., `['spidroin']`).
- `expected_types`: Substrings used to bucket records into type folders (default `['Heavy Chain', 'Light Chain']`; unmatched go to `others`).
- `api_key`: NCBI API key string (optional but recommended for higher limits).
- `output_root`: Directory where results are stored.
- `sleep_time`: Delay between GenBank fetches to be polite to NCBI.

## What It Saves
- JSON and Markdown per record under: `output_root/order/...taxonomy.../species/partial|full/<type>/`.
  - Partial vs full decided by whether the title contains "partial".
  - Type decided by first match in `expected_types`, else `others`.
- `phylo_tree.json` under `output_root` mirroring the nested structure with record references.

## Minimal Example
```python
from ncbi_protein_scraper_lib import run_ncbi_protein_scraper

families = ["Ctenizidae", "Theraphosidae"]
run_ncbi_protein_scraper(
    order_name="Araneae",
    family_names=families,
    protein_terms=["spidroin"],
    expected_types=["MaSp1", "MaSp2", "AcSp"],
    api_key=None,  # or your NCBI API key
    output_root="ncbi_spider_spidroin_sequences",
    sleep_time=0.7,
)
```

## Notes
- Uses ESearch → ESummary (chunked to avoid 414s) → EFetch (GenBank text) per accession.
- `taxonomy_from_order` anchors the lineage at `order_name`; if not found, the order is prepended.
- Sequences are stored unwrapped; length is in the JSON. Adjust `sleep_time` or `retmax` inside the code if needed.
- Unmatched types are placed in `others` under the type level.

## Tips
- Set `NCBI_API_KEY` in your environment and pass it in for better throughput.
- Customize `expected_types` with the substrings you care about; first match wins.
- Run in a virtual environment to isolate dependencies (`requests`).
