import argparse
from collections import defaultdict
from pathlib import Path
from typing import Dict, Optional, Tuple

FULL_DIR_NAMES = {"full", "full_sequence"}
PARTIAL_DIR_NAMES = {"partial", "partial_sequence"}

CHAIN_TYPES = ("Heavy", "Light", "Other")


def format_species(name: str) -> str:
    return name.replace("_", " ")


def normalize_chain(name: str) -> str:
    lowered = name.lower()
    if "heavy" in lowered:
        return "Heavy"
    if "light" in lowered:
        return "Light"
    return "Other"


def normalize_type(name: str) -> str:
    lowered = name.lower()
    if "heavy" in lowered:
        return "Heavy"
    if "light" in lowered:
        return "Light"
    return name


def find_partial_full(chain_dir: Path) -> Tuple[Optional[str], Optional[Path]]:
    for parent in chain_dir.parents:
        pname = parent.name.lower()
        if pname in FULL_DIR_NAMES:
            return "full", parent
        if pname in PARTIAL_DIR_NAMES:
            return "partial", parent
    return None, None


def count_unique_records(chain_dir: Path) -> int:
    stems = set()
    for item in chain_dir.iterdir():
        if not item.is_file():
            continue
        if item.name.startswith("."):
            continue
        stems.add(item.stem)
    return len(stems)


def build_counts(root: Path) -> Dict[str, Dict[str, Dict[str, int]]]:
    counts: Dict[str, Dict[str, Dict[str, int]]] = defaultdict(
        lambda: {"full": defaultdict(int), "partial": defaultdict(int)}
    )

    for data_dir in root.rglob("*"):
        if not data_dir.is_dir():
            continue

        record_count = count_unique_records(data_dir)
        if record_count == 0:
            continue

        partial_full, full_dir = find_partial_full(data_dir)
        if not partial_full or not full_dir:
            continue

        organism_dir = full_dir.parent
        species_label = format_species(organism_dir.name)
        if data_dir == full_dir:
            data_type = "Other"
        else:
            data_type = normalize_type(data_dir.name)

        counts[species_label][partial_full][data_type] += record_count

    return counts


def write_index(root: Path, output_path: Path, counts: Dict[str, Dict[str, Dict[str, int]]]) -> None:
    lines = []
    lines.append("# NCBI Caddisfly Fibroin Species Index")
    lines.append("")
    lines.append(
        "This file summarizes the results from the NCBI protein database search for 'Fibroin' "
        "grouped by species and data type."
    )
    lines.append("**NOTE:** Counts are unique per record stem; .md/.json pairs are counted once.")
    lines.append("")
    lines.append("## Detailed Sequence Counts by Species and Type")

    all_types = set()
    for species_data in counts.values():
        for band in ("full", "partial"):
            all_types.update(species_data.get(band, {}).keys())

    if all_types.issubset(set(CHAIN_TYPES)):
        type_order = list(CHAIN_TYPES)
    else:
        type_order = sorted(all_types, key=lambda t: str(t).lower())

    header_cols = ["Species Name", "Total Found"]
    for t in type_order:
        header_cols.append(f"Full ({t})")
    for t in type_order:
        header_cols.append(f"Partial ({t})")
    lines.append("| " + " | ".join(header_cols) + " |")
    lines.append("| " + " | ".join([":---"] + [":---:"] * (len(header_cols) - 1)) + " |")

    grand_total = 0
    for species in sorted(counts.keys(), key=lambda s: s.lower()):
        full = counts[species].get("full", {})
        partial = counts[species].get("partial", {})
        row = {
            "Full": {k: full.get(k, 0) for k in type_order},
            "Partial": {k: partial.get(k, 0) for k in type_order},
        }
        total = sum(row["Full"].values()) + sum(row["Partial"].values())
        grand_total += total

        row_values = [f"| {species} | **{total}**"]
        row_values.extend(str(row["Full"][t]) for t in type_order)
        row_values.extend(str(row["Partial"][t]) for t in type_order)
        lines.append(" | ".join(row_values) + " |")

    lines.append("")
    lines.append("---")
    lines.append(f"## GRAND TOTAL SEQUENCES DOWNLOADED: **{grand_total}**")
    lines.append("")
    lines.append(
        "All sequences are saved in the database folder, organized hierarchically by taxonomy, "
        "Organism, Sequence Type, and Chain Type."
    )

    output_path.write_text("\n".join(lines), encoding="ascii")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate a species-level index for a nested fibroin database."
    )
    parser.add_argument(
        "root",
        nargs="?",
        default="ncbi_fibroin_sequences",
        help="Root folder of the nested database.",
    )
    parser.add_argument(
        "--output",
        default="Species_Index.md",
        help="Output Markdown filename (relative to root unless absolute).",
    )
    parser.add_argument(
        "--output-path",
        default=None,
        help="Directory or full file path for the index output.",
    )

    args = parser.parse_args()
    root = Path(args.root)
    if not root.exists():
        raise SystemExit(f"Root directory not found: {root}")

    if args.output_path:
        output_path = Path(args.output_path)
        if output_path.exists() and output_path.is_dir():
            output_path = output_path / args.output
        elif output_path.suffix.lower() != ".md":
            output_path = output_path / args.output
    else:
        output_path = Path(args.output)
        if not output_path.is_absolute():
            output_path = root / output_path

    counts = build_counts(root)
    if not counts:
        raise SystemExit("No data found under the provided root.")

    write_index(root, output_path, counts)
    print(f"Index written to: {output_path}")


if __name__ == "__main__":
    main()
