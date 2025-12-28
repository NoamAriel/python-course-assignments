import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

import matplotlib.pyplot as plt
from matplotlib.patches import Patch


MARK_ORDER = [
    ("Full (Heavy)", "F-H"),
    ("Full (Light)", "F-L"),
    ("Full (Other)", "F-O"),
    ("Partial (Heavy)", "P-H"),
    ("Partial (Light)", "P-L"),
    ("Partial (Other)", "P-O"),
]

RANK_ORDER = [
    "Order",
    "Suborder",
    "Infraorder",
    "Superfamily",
    "Family",
    "Subfamily",
    "Tribe",
    "Genus",
    "Species",
]

RANK_ORDER_MAP = {rank.lower(): idx for idx, rank in enumerate(RANK_ORDER)}


def _parse_int(value: str) -> int:
    cleaned = value.replace("**", "").strip()
    return int(cleaned) if cleaned.isdigit() else 0


def parse_species_index(md_path: Path) -> dict[str, list[str]]:
    text = md_path.read_text(encoding="utf-8")
    lines = text.splitlines()

    rows: list[dict[str, object]] = []
    in_table = False

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("|") and "Species Name" in stripped:
            in_table = True
            continue
        if not in_table:
            continue
        if stripped.startswith("---"):
            break
        if stripped.startswith("|") and "---" in stripped:
            continue
        if not stripped.startswith("|"):
            continue

        cells = [c.strip() for c in stripped.strip("|").split("|")]
        if len(cells) < 8:
            continue

        species = cells[0]
        counts = {
            "Full (Heavy)": _parse_int(cells[2]),
            "Full (Light)": _parse_int(cells[3]),
            "Full (Other)": _parse_int(cells[4]),
            "Partial (Heavy)": _parse_int(cells[5]),
            "Partial (Light)": _parse_int(cells[6]),
            "Partial (Other)": _parse_int(cells[7]),
        }

        rows.append({"Species Name": species, **counts})

    if not rows:
        return {}

    df = pd.DataFrame(rows).fillna(0)
    species_marks: dict[str, list[str]] = {}
    for _, row in df.iterrows():
        counts_array = np.array([int(row[key]) for key, _ in MARK_ORDER], dtype=int)
        marks = [abbr for (key, abbr), val in zip(MARK_ORDER, counts_array) if val > 0]
        species_marks[str(row["Species Name"]).lower()] = marks

    return species_marks


def parse_taxonomy_tree(tree: dict) -> dict:
    def build_node(name: str, payload: object) -> dict:
        rank = None
        children: list[dict] = []
        if isinstance(payload, dict):
            rank = payload.get("__rank__")
            if isinstance(rank, str):
                rank = rank.strip().lower()
            for child_name, child_data in payload.items():
                if child_name in ("__rank__", "full", "partial"):
                    continue
                if str(child_name).startswith("__"):
                    continue
                children.append(build_node(child_name, child_data))
        return {"name": name, "rank": rank, "children": children, "key": ""}

    roots = [
        build_node(name, payload)
        for name, payload in tree.items()
        if not str(name).startswith("__")
    ]
    if not roots:
        raise ValueError("No taxonomy nodes found in tree.")

    root = roots[0] if len(roots) == 1 else {"name": "ROOT", "rank": None, "children": roots, "key": ""}
    assign_keys(root)
    return root


def assign_keys(node: dict, parent_key: str = "") -> None:
    key = node["name"] if not parent_key else f"{parent_key}/{node['name']}"
    node["key"] = key
    for child in node["children"]:
        assign_keys(child, key)


def gather_rank_labels(root: dict) -> dict[int, str]:
    present = set()
    for node in iter_nodes(root):
        rank = node.get("rank")
        if isinstance(rank, str) and rank in RANK_ORDER_MAP:
            present.add(RANK_ORDER_MAP[rank])
    return {idx: RANK_ORDER[idx] for idx in sorted(present)}


def layout_tree(root: dict) -> tuple[dict[str, tuple[float, float]], int, int, int]:
    positions: dict[str, tuple[float, float]] = {}
    leaf_index = 0
    max_depth = 0
    min_rank_index: int | None = None

    def walk(node: dict, depth: int) -> float:
        nonlocal leaf_index, max_depth
        max_depth = max(max_depth, depth)
        children = node["children"]
        if not children:
            x = float(leaf_index)
            leaf_index += 1
            positions[node["key"]] = (x, -float(depth))
            return x

        child_xs = [walk(child, depth + 1) for child in children]
        x = sum(child_xs) / len(child_xs)
        positions[node["key"]] = (x, -float(depth))
        return x

    walk(root, 0)

    max_rank_index = -1
    for node in iter_nodes(root):
        rank = node.get("rank")
        if isinstance(rank, str) and rank in RANK_ORDER_MAP:
            x, _ = positions[node["key"]]
            rank_idx = RANK_ORDER_MAP[rank]
            positions[node["key"]] = (x, -float(rank_idx))
            max_rank_index = max(max_rank_index, RANK_ORDER_MAP[rank])
            if min_rank_index is None:
                min_rank_index = rank_idx
            else:
                min_rank_index = min(min_rank_index, rank_idx)

    rank_offset = min_rank_index or 0
    if rank_offset:
        for key, (x, y) in positions.items():
            positions[key] = (x, y + rank_offset)

    depth_count = max(max_depth + 1 - rank_offset, max_rank_index - rank_offset + 1)
    return positions, leaf_index, depth_count, rank_offset


def iter_nodes(root: dict) -> list[dict]:
    nodes: list[dict] = []

    def walk(node: dict) -> None:
        nodes.append(node)
        for child in node["children"]:
            walk(child)

    walk(root)
    return nodes


def draw_edges(ax, node: dict, positions: dict[str, tuple[float, float]]) -> None:
    parent_key = node["key"]
    x1, y1 = positions[parent_key]
    for child in node["children"]:
        child_key = child["key"]
        x2, y2 = positions[child_key]
        ax.plot([x1, x2], [y1, y2], color="#4a4a4a", linewidth=1.0)
        draw_edges(ax, child, positions)


def draw_labels(
    ax,
    node: dict,
    positions: dict[str, tuple[float, float]],
    species_marks: dict[str, list[str]],
    species_label_offset: float,
    name_rank_map: dict[str, str],
    label_seen: set[tuple[str, str]],
) -> None:
    key = node["key"]
    name = node["name"]
    x, y = positions[key]
    is_leaf = not node["children"]
    label = name
    is_species = is_leaf or node.get("rank") == "species" or name.lower() in species_marks
    if is_species:
        marks = species_marks.get(name.lower(), [])
        if marks:
            label = f"{name}\n[{', '.join(marks)}]"
    name_key = name.lower()
    rank_key = node.get("rank") or name_rank_map.get(name_key)
    if rank_key:
        label_group = f"rank:{rank_key}"
    else:
        label_group = f"node:{key}"
    label_key = (label_group, name_key)
    if label_key not in label_seen:
        label_seen.add(label_key)
        if is_species:
            ax.text(
                x,
                y - species_label_offset,
                label,
                ha="right",
                va="center",
                fontsize=8,
                rotation=45,
            )
        else:
            ax.text(x, y, label, ha="center", va="center", fontsize=8)
    for child in node["children"]:
        draw_labels(
            ax,
            child,
            positions,
            species_marks,
            species_label_offset,
            name_rank_map,
            label_seen,
        )


def render_tree(
    root: dict,
    species_marks: dict[str, list[str]],
    outpath: Path,
    fmt: str = "png",
) -> Path:
    positions, leaf_count, depth_count, rank_offset = layout_tree(root)
    depth_labels = gather_rank_labels(root)
    name_rank_map: dict[str, str] = {}
    for node in iter_nodes(root):
        rank = node.get("rank")
        name = node.get("name", "")
        if not rank or not name:
            continue
        key = name.strip().lower()
        if key in name_rank_map and name_rank_map[key] != rank:
            name_rank_map[key] = ""
        elif key not in name_rank_map:
            name_rank_map[key] = rank
    name_rank_map = {k: v for k, v in name_rank_map.items() if v}
    width = max(8.0, leaf_count * 1.4)
    height = max(4.5, depth_count * 1.3)
    species_label_offset = 0.6

    fig, ax = plt.subplots(figsize=(width, height))
    draw_edges(ax, root, positions)
    draw_labels(ax, root, positions, species_marks, species_label_offset, name_rank_map, set())

    min_x = min(x for x, _ in positions.values())
    max_x = max(x for x, _ in positions.values())
    min_y = min(y for _, y in positions.values())
    max_y = max(y for _, y in positions.values())
    rank_x = min_x - 1.2

    for depth in range(depth_count):
        label = depth_labels.get(depth + rank_offset)
        if not label:
            continue
        ax.text(rank_x, -float(depth), label, ha="right", va="center", fontsize=8, color="#2f2f2f")

    species_names = {
        node.get("name", "").strip().lower()
        for node in iter_nodes(root)
        if node.get("rank") == "species"
    }
    if species_names:
        used_marks = {
            mark
            for name, marks in species_marks.items()
            if name in species_names
            for mark in marks
        }
        legend_handles = []
        for label, abbr in MARK_ORDER:
            if abbr not in used_marks:
                continue
            legend_handles.append(Patch(facecolor="white", edgecolor="#4a4a4a", label=f"{abbr} = {label}"))
        if legend_handles:
            ax.legend(
                handles=legend_handles,
                loc="upper right",
                bbox_to_anchor=(1.0, 1.0),
                borderaxespad=0.0,
                frameon=False,
                fontsize=8,
            )

    ax.set_xlim(rank_x - 0.8, max_x + 0.8)
    ax.set_ylim(min_y - 0.8 - species_label_offset, max_y + 0.8)
    ax.set_axis_off()

    output_file = outpath.with_suffix(f".{fmt}")
    fig.savefig(output_file, dpi=200, bbox_inches="tight")
    plt.close(fig)
    return output_file


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build a taxonomy hierarchy graph from phylo_tree.json with protein-type marks."
    )
    parser.add_argument(
        "--tree",
        type=Path,
        default=Path("caddisfly/phylo_tree.json"),
        help="Path to phylo_tree.json",
    )
    parser.add_argument(
        "--index",
        type=Path,
        default=Path("caddisfly/Species_Index.md"),
        help="Path to Species_Index.md",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("caddisfly/taxonomy_tree_with_protein_marks"),
        help="Output path without extension",
    )
    parser.add_argument(
        "--format",
        default="png",
        choices=["png", "svg", "pdf"],
        help="Output format",
    )

    args = parser.parse_args()
    tree = json.loads(args.tree.read_text(encoding="utf-8"))
    species_marks = parse_species_index(args.index)
    root = parse_taxonomy_tree(tree)
    output_file = render_tree(
        root=root,
        species_marks=species_marks,
        outpath=args.out,
        fmt=args.format,
    )
    print(f"Wrote: {output_file}")


if __name__ == "__main__":
    main()
