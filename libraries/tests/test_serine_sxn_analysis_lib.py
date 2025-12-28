from pathlib import Path
from serine_sxn_analysis_lib import analyze_from_root

base = Path(__file__).resolve().parent  # folder containing lib_test.py
root = (base / "ncbi_spider_spidroin_sequences").resolve()
json_path, md_path = analyze_from_root(root, max_n=50, min_n=2)
print(json_path, md_path)
