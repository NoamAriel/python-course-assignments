import json
import sys
import time
from pathlib import Path

import numpy as np
tic = time.perf_counter()

# Optional overrides (absolute or relative to this file)
# - tree_path: where phylo_tree.json lives
# - index_path: Species_Index.md for protein marks
# - out_path: output path without extension
# - data_root: where ncbi_fibroin_sequences live (for filters)
tree_path= Path(r"D:\python\course\python-course-assignments\day08\ncbi_fibroin_sequences\phylo_tree.json")
index_path= Path(r"D:\python\course\python-course-assignments\day08\Species_Index.md")
out_path= Path(r"D:\python\course\python-course-assignments\day08\taxonomy_tree_integripalpia")
data_root= Path(r"D:\python\course\python-course-assignments\day08\ncbi_fibroin_sequences")
output_format: str = "png"  # "png", "svg", or "pdf"

# Optional filters (match aa_composition_analysis style)
protein_types: list[str] | None = None                      # default: None; e.g., ["heavy chain"] or ["light chain"]
partial_full: str | None = None                             # default: None; "full", "partial", or None
length_range: tuple[int, int] | None = None                 # default: None; e.g., (100, 2450)
length_threshold: int | None = None                         # default: None; e.g., 1500
length_mode: str = "ge"                                     # default: "ge"; "ge" for >=, "le" for <=
longest_factor: float | None = None                         # default: None; e.g., 2.0 keeps >= (longest / 2.0)
longest_factor_scope: str = "species"                       # "species" (per organism) or "global" (all records)


# Optional rank range (can be rank type like "Family" or rank name like "Hydropsychoidea")
# If rank_from is a rank name, the graph is restricted to that branch.
rank_from: str | None = "integripalpia"                                # default: None; e.g., "Family" or "Hydropsychoidea"
rank_to: str | None = None                              # default: None; e.g., "Species" or "Hydropsychoidea"


# Optional rank name filter (applies to a specific rank)
# Use this to keep multiple names at one rank (e.g., several superfamilies).
rank_name_filter_rank: str | None = None                 # default: None; e.g., "Superfamily"
rank_name_filter: list[str] | None = None                # default: None; e.g., ["Hydropsychoidea"]


BASE = Path(__file__).resolve().parent
PROJECT_ROOT = BASE.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from libraries.aminoacids_composition_analysis_lib import (
    filter_records,
    load_records_from_root,
)
from libraries.generate_taxonomy_graph import (
    RANK_ORDER,
    RANK_ORDER_MAP,
    assign_keys,
    parse_species_index,
    parse_taxonomy_tree,
    render_tree,
)


def record_species_name(rec: dict) -> str:
    for key in ("organism_name", "organism", "species"):
        value = rec.get(key)
        if value:
            return str(value)
    return ""


def build_species_filter_set(
    data_root: Path,
    protein_types: list[str] | None,
    partial_full: str | None,
    length_range: tuple[int, int] | None,
    length_threshold: int | None,
    length_mode: str,
    longest_factor: float | None,
    longest_factor_scope: str,
) -> set[str]:
    records = load_records_from_root(data_root, skip_tree=True)
    filtered = filter_records(
        records,
        taxonomy_terms=None,
        protein_types=protein_types,
        partial_full=partial_full,
        length_range=length_range,
        length_threshold=length_threshold,
        length_mode=length_mode,
        longest_factor=longest_factor,
        longest_factor_scope=longest_factor_scope,
    )
    species = set()
    for rec in filtered:
        name = record_species_name(rec).strip()
        if name:
            species.add(name.lower())
    return species


def filter_tree_by_species(node: dict, species_set: set[str]) -> dict | None:
    filtered_children = []
    for child in node["children"]:
        kept = filter_tree_by_species(child, species_set)
        if kept:
            filtered_children.append(kept)

    is_species = node.get("rank") == "species"
    if is_species and node["name"].lower() in species_set:
        return {"name": node["name"], "rank": node.get("rank"), "children": filtered_children, "key": ""}
    if not is_species and filtered_children:
        return {"name": node["name"], "rank": node.get("rank"), "children": filtered_children, "key": ""}
    return None


def filter_tree_by_rank_range(node: dict, min_idx: int, max_idx: int) -> list[dict]:
    kept_children: list[dict] = []
    for child in node["children"]:
        kept_children.extend(filter_tree_by_rank_range(child, min_idx, max_idx))

    rank = node.get("rank")
    rank_idx = RANK_ORDER_MAP.get(rank) if isinstance(rank, str) else None
    if rank_idx is None:
        return kept_children
    if min_idx <= rank_idx <= max_idx:
        return [{"name": node["name"], "rank": rank, "children": kept_children, "key": ""}]
    return kept_children


def filter_tree_by_rank_names(node: dict, target_rank: str, names: set[str]) -> dict | None:
    filtered_children = []
    for child in node["children"]:
        kept = filter_tree_by_rank_names(child, target_rank, names)
        if kept:
            filtered_children.append(kept)

    rank = node.get("rank")
    if rank == target_rank:
        if node["name"].lower() in names:
            return {"name": node["name"], "rank": rank, "children": filtered_children, "key": ""}
        return None

    if filtered_children:
        return {"name": node["name"], "rank": rank, "children": filtered_children, "key": ""}
    return None


def find_rank_by_name(root: dict, name: str) -> str | None:
    matches = set()
    target = name.strip().lower()
    if not target:
        return None
    nodes = [root]
    while nodes:
        node = nodes.pop()
        if node.get("name", "").strip().lower() == target and node.get("rank"):
            matches.add(node["rank"])
        nodes.extend(node.get("children", []))
    if len(matches) > 1:
        raise ValueError(f"Ambiguous rank name '{name}'; found ranks: {', '.join(sorted(matches))}")
    return next(iter(matches)) if matches else None


def find_node_by_name(root: dict, name: str) -> dict | None:
    matches = []
    target = name.strip().lower()
    if not target:
        return None
    nodes = [root]
    while nodes:
        node = nodes.pop()
        if node.get("name", "").strip().lower() == target:
            matches.append(node)
        nodes.extend(node.get("children", []))
    if len(matches) > 1:
        ranks = sorted({node.get("rank") or "unknown" for node in matches})
        raise ValueError(f"Ambiguous rank name '{name}'; found ranks: {', '.join(ranks)}")
    return matches[0] if matches else None


def resolve_rank_range(root: dict, rank_from: str | None, rank_to: str | None) -> tuple[int, int] | None:
    if not rank_from and not rank_to:
        return None
    start = 0
    end = len(RANK_ORDER) - 1
    if rank_from:
        rank_key = rank_from.strip().lower()
        if rank_key not in RANK_ORDER_MAP:
            resolved = find_rank_by_name(root, rank_from)
            if not resolved:
                raise ValueError(
                    f"Unknown rank_from '{rank_from}'. Use a rank type from: {', '.join(RANK_ORDER)} "
                    "or a rank name from the tree."
                )
            rank_key = resolved
        if rank_key not in RANK_ORDER_MAP:
            raise ValueError(f"Unknown rank_from '{rank_from}'. Options: {', '.join(RANK_ORDER)}")
        start = RANK_ORDER_MAP[rank_key]
    if rank_to:
        rank_key = rank_to.strip().lower()
        if rank_key not in RANK_ORDER_MAP:
            resolved = find_rank_by_name(root, rank_to)
            if not resolved:
                raise ValueError(
                    f"Unknown rank_to '{rank_to}'. Use a rank type from: {', '.join(RANK_ORDER)} "
                    "or a rank name from the tree."
                )
            rank_key = resolved
        if rank_key not in RANK_ORDER_MAP:
            raise ValueError(f"Unknown rank_to '{rank_to}'. Options: {', '.join(RANK_ORDER)}")
        end = RANK_ORDER_MAP[rank_key]
    if start > end:
        raise ValueError("rank_from must be above or equal to rank_to in the rank order.")
    return start, end

resolved_tree = tree_path if tree_path and tree_path.is_absolute() else (BASE / (tree_path or "ncbi_fibroin_sequences/phylo_tree.json"))
resolved_tree = resolved_tree.resolve()

resolved_index = None
if index_path is not None:
    resolved_index = index_path if index_path.is_absolute() else (BASE / index_path)
    resolved_index = resolved_index.resolve()
else:
    default_index = BASE / "Species_Index.md"
    resolved_index = default_index if default_index.exists() else None

resolved_out = out_path if out_path and out_path.is_absolute() else (BASE / (out_path or "taxonomy_tree_with_protein_marks"))
resolved_out = resolved_out.resolve()

resolved_data_root = data_root if data_root and data_root.is_absolute() else (BASE / (data_root or "ncbi_fibroin_sequences"))
resolved_data_root = resolved_data_root.resolve()

tree = json.loads(resolved_tree.read_text(encoding="utf-8"))
root = parse_taxonomy_tree(tree)

species_marks = {}
if resolved_index and resolved_index.exists():
    species_marks = parse_species_index(resolved_index)

rank_from_key = rank_from
if rank_from:
    rank_key = rank_from.strip().lower()
    if rank_key not in RANK_ORDER_MAP:
        branch_root = find_node_by_name(root, rank_from)
        if not branch_root:
            raise SystemExit(
                f"Unknown rank_from '{rank_from}'. Use a rank type or a rank name from the tree."
            )
        root = branch_root
        rank_from_key = branch_root.get("rank")

apply_filters = bool(
    np.any(
        [
            protein_types,
            partial_full is not None,
            length_range is not None,
            length_threshold is not None,
            longest_factor is not None,
        ]
    )
)

if apply_filters:
    species_set = build_species_filter_set(
        data_root=resolved_data_root,
        protein_types=protein_types,
        partial_full=partial_full,
        length_range=length_range,
        length_threshold=length_threshold,
        length_mode=length_mode,
        longest_factor=longest_factor,
        longest_factor_scope=longest_factor_scope,
    )
    if not species_set:
        raise SystemExit("No species matched the provided filters.")
    filtered = filter_tree_by_species(root, species_set)
    if not filtered:
        raise SystemExit("No taxonomy nodes remained after species filtering.")
    root = filtered

if rank_name_filter_rank and rank_name_filter:
    target_rank = rank_name_filter_rank.strip().lower()
    if target_rank not in RANK_ORDER_MAP:
        raise SystemExit(
            f"Unknown rank_name_filter_rank '{rank_name_filter_rank}'. Options: {', '.join(RANK_ORDER)}"
        )
    name_set = {name.strip().lower() for name in rank_name_filter if name.strip()}
    if not name_set:
        raise SystemExit("rank_name_filter was provided but no valid names were found.")
    filtered = filter_tree_by_rank_names(root, target_rank, name_set)
    if not filtered:
        raise SystemExit("No taxonomy nodes remained after rank name filtering.")
    root = filtered

rank_range = resolve_rank_range(root, rank_from_key, rank_to)
if rank_range:
    min_idx, max_idx = rank_range
    roots = filter_tree_by_rank_range(root, min_idx, max_idx)
    if not roots:
        raise SystemExit("No taxonomy nodes remained after rank filtering.")
    if len(roots) == 1:
        root = roots[0]
    else:
        root = {"name": "", "rank": None, "children": roots, "key": ""}

assign_keys(root)
output_file = render_tree(root=root, species_marks=species_marks, outpath=resolved_out, fmt=output_format)
print(f"Wrote: {output_file}")

toc = time.perf_counter()
print(f"Elapsed: {toc - tic:0.3f} seconds")
