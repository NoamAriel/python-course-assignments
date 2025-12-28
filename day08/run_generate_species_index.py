# Wrapper script for species index generation.
# run_generate_species_index.py

from pathlib import Path
import sys
import time

BASE = Path(__file__).resolve().parent
PROJECT_ROOT = BASE.parent
if PROJECT_ROOT.exists() and str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from libraries.generate_species_index import build_counts, write_index



tic = time.perf_counter()
# Optional overrides (absolute or relative to this file)
# - data_root: where the ncbi_fibroin_sequences live
# - output_path: directory or full path for the index output
# - output_filename: used when output_path is a directory

data_root: Path | None = Path(r"D:\python\course\python-course-assignments\day08\ncbi_fibroin_sequences\trichoptera")
output_path: Path | None = Path(r"D:\python\course\python-course-assignments\day08")
output_filename = "Species_Index.md"

resolved_root = data_root if data_root and data_root.is_absolute() else (BASE / (data_root or "ncbi_fibroin_sequences"))
root = resolved_root.resolve()

resolved_output = None
if output_path:
    resolved_output = output_path if output_path.is_absolute() else (BASE / output_path)
    resolved_output = resolved_output.resolve()

if resolved_output:
    if resolved_output.exists() and resolved_output.is_dir():
        index_path = resolved_output / output_filename
    elif resolved_output.suffix.lower() != ".md":
        index_path = resolved_output / output_filename
    else:
        index_path = resolved_output
else:
    index_path = (root / output_filename).resolve()

counts = build_counts(root)
if not counts:
    raise SystemExit("No data found under the provided root.")

write_index(root, index_path, counts)
print(f"Index written to: {index_path}")

toc = time.perf_counter()
print(f"Elapsed: {toc - tic:0.3f} seconds")
