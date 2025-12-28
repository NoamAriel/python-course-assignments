"""
Plotting utilities for serine_sxn_analysis_lib outputs.

Given a serine_sxn_analysis JSON (or the companion MD path), this script
produces:
- Serine content plots (counts and fractions).
- Total [SX]_n coverage plots.
- Motif count/fraction plots per protein type.
- X-residue composition plots per protein type.
- A simple phylogenetic tree annotated with available protein types.

Plots are written to a sibling directory named `plots` next to the input file.
File names include the analysed n-range.
"""

from __future__ import annotations

import argparse
import csv
import json
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

AMINO_ORDER = [
    # non-polar
    "A",
    "V",
    "L",
    "I",
    "M",
    "F",
    "W",
    "P",
    "G",
    # polar
    "S",
    "T",
    "C",
    "Y",
    "N",
    "Q",
    # charged
    "D",
    "E",
    "K",
    "R",
    "H",
]

# Fixed amino-acid color map (tab20-inspired), aligned to AMINO_ORDER.
AA_COLORS: Dict[str, str] = {
    "A": "#1f77b4",
    "V": "#aec7e8",
    "L": "#ff7f0e",
    "I": "#ffbb78",
    "M": "#2ca02c",
    "F": "#98df8a",
    "W": "#d62728",
    "P": "#ff9896",
    "G": "#9467bd",
    "S": "#c5b0d5",
    "T": "#8c564b",
    "C": "#c49c94",
    "Y": "#e377c2",
    "N": "#f7b6d2",
    "Q": "#7f7f7f",
    "D": "#c7c7c7",
    "E": "#bcbd22",
    "K": "#dbdb8d",
    "R": "#17becf",
    "H": "#9edae5",
}


# ---------- Data loading ---------- #


def _slugify(text: str) -> str:
    """Make a filesystem-friendly slug."""
    return "".join(ch if ch.isalnum() else "_" for ch in text).strip("_") or "none"


def load_summary(path: Path) -> Dict[str, Any]:
    """Load analysis summary from JSON; if a Markdown path is provided, swap to JSON."""
    if path.suffix.lower() == ".md":
        path = path.with_suffix(".json")
    if not path.exists():
        raise FileNotFoundError(f"Analysis file not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def ensure_out_dir(base: Path) -> Path:
    out_dir = base.parent / "plots" / "sxn_plots"
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir


def _tables_output_dir(
    out_dir: Path,
    tables_dir: Optional[Path],
    taxonomy_terms: Optional[Iterable[str]],
    partial_full: Optional[str],
    protein_types: Optional[Iterable[str]],
    length_range: Optional[Tuple[int, int]],
    length_threshold: Optional[int],
    length_mode: str,
    longest_factor: Optional[float],
) -> Path:
    if tables_dir is None:
        root = out_dir.parents[3] if len(out_dir.parents) >= 4 else out_dir.parent
        base = root / "tables"
    else:
        base = tables_dir

    if taxonomy_terms:
        tax_part = "__".join(_slugify(str(t)) for t in taxonomy_terms)
    else:
        tax_part = "all_taxonomy"

    pf_part = _slugify(partial_full or "all_partial_full")

    if protein_types:
        type_part = "__".join(_slugify(str(t)) for t in protein_types)
    else:
        type_part = "all_types"

    length_parts: List[str] = []
    if length_range is not None:
        length_parts.append(f"{length_range[0]}-{length_range[1]}")
    if length_threshold is not None:
        length_parts.append(f"{length_mode}_{length_threshold}")
    if longest_factor is not None:
        length_parts.append(f"longest_factor_{longest_factor}")
    if not length_parts:
        length_parts = ["all_lengths"]

    out_path = base / "sxn_plots" / tax_part / pf_part / type_part
    for part in length_parts:
        out_path = out_path / part
    out_path.mkdir(parents=True, exist_ok=True)
    return out_path


def _write_table_files(header: Sequence[str], rows: Sequence[Sequence[str]], base_path: Path) -> None:
    base_path.parent.mkdir(parents=True, exist_ok=True)

    csv_path = base_path.with_suffix(".csv")
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(header)
        for row in rows:
            writer.writerow(row)

    md_path = base_path.with_suffix(".md")
    md_lines = [
        "| " + " | ".join(header) + " |",
        "| " + " | ".join(["---"] * len(header)) + " |",
    ]
    for row in rows:
        md_lines.append("| " + " | ".join(str(x) for x in row) + " |")
    md_path.write_text("\n".join(md_lines), encoding="utf-8")

    return


def category_out_dir(base_out: Path, category: str, min_n: int, max_n: int) -> Path:
    """
    Return per-category output folder (partial/full/unknown), with a nested
    n-range folder (e.g., n_2_to_50) for disambiguating different analyses.
    """
    if category == "partial":
        root = base_out / "partial_sequence"
    elif category == "full":
        root = base_out / "full_sequence"
    else:
        root = base_out / "unknown_sequence"
    root.mkdir(parents=True, exist_ok=True)
    range_dir = root / f"n_{min_n}_to_{max_n}"
    range_dir.mkdir(parents=True, exist_ok=True)
    return range_dir


# ---------- Helpers ---------- #


def _type_colors(types: Iterable[str]) -> Dict[str, str]:
    palette = plt.colormaps.get_cmap("tab20")
    types_list = sorted(set(types))
    return {t: palette(i / max(1, len(types_list))) for i, t in enumerate(types_list)}


def _taxonomy_lineage(rec: Dict[str, Any]) -> List[str]:
    return (
        rec.get("taxonomy_from_order")
        or rec.get("taxonomy_from_araneae")
        or rec.get("taxonomy_full")
        or []
    )


def _axis_label_rotate(ax: plt.Axes, rotation: int = 45) -> None:
    for label in ax.get_xticklabels():
        label.set_rotation(rotation)
        label.set_horizontalalignment("right")


def _species_order(records: List[Dict[str, Any]], order_anchor: str = "") -> List[str]:
    """
    Derive a lineage-based ordering of organisms based on their taxonomy_from_order (or fallbacks).
    Falls back to alphabetical if no lineage is available.
    """
    anchor_lc = order_anchor.lower() if order_anchor else ""
    seen: set = set()
    lineage_pairs: List[Tuple[Tuple[str, ...], str]] = []

    for rec in records:
        org = rec.get("organism", "Unknown")
        if org in seen:
            continue
        lineage = rec.get("taxonomy_from_order") or rec.get("taxonomy_from_araneae") or rec.get("taxonomy_full") or []
        if not lineage:
            continue
        if anchor_lc:
            for i, name in enumerate(lineage):
                if name.lower() == anchor_lc:
                    lineage = lineage[i:]
                    break
        lineage_pairs.append((tuple(lineage), org))
        seen.add(org)

    if lineage_pairs:
        lineage_pairs.sort(key=lambda x: x[0])
        ordered = [org for _, org in lineage_pairs]
    else:
        ordered = sorted(seen)
    return ordered


def _flatten_motif_records(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Flatten motif_runs into per-n rows, skipping zero counts."""
    flat: List[Dict[str, Any]] = []
    for rec in records:
        motif_runs: Dict[str, Any] = rec.get("motif_runs", {})
        length = rec.get("length", 0) or 0
        for n, count in motif_runs.items():
            if count:
                n_int = int(n)
                residues = 2 * n_int * count
                percent = (residues / length * 100) if length else 0.0
                flat.append(
                    {
                        "Organism": rec.get("organism", "Unknown"),
                        "Type": rec.get("type", "Unknown"),
                        "Partial": rec.get("partial_full", "unknown"),
                        "Accession": rec.get("accession", ""),
                        "n": n_int,
                        "Count": count,
                        "Residues_Covered": residues,
                        "Percent": percent,
                        "Length": length,
                    }
                )
    return flat


def _aggregate_mean(rows: List[Dict[str, Any]], keys: List[str], value_keys: List[str]) -> List[Dict[str, Any]]:
    grouped: Dict[Tuple, List[Dict[str, Any]]] = defaultdict(list)
    for r in rows:
        grouped[tuple(r[k] for k in keys)].append(r)
    out: List[Dict[str, Any]] = []
    for key, items in grouped.items():
        base = dict(zip(keys, key))
        for v in value_keys:
            base[v] = sum(item.get(v, 0) for item in items) / len(items)
        out.append(base)
    return out


def _stdev(values: List[float]) -> float:
    return statistics.stdev(values) if len(values) > 1 else 0.0


def _aggregate_stats(
    rows: List[Dict[str, Any]],
    keys: List[str],
    value_keys: List[str],
) -> List[Dict[str, Any]]:
    grouped: Dict[Tuple, List[Dict[str, Any]]] = defaultdict(list)
    for r in rows:
        grouped[tuple(r[k] for k in keys)].append(r)
    out: List[Dict[str, Any]] = []
    for key, items in grouped.items():
        base = dict(zip(keys, key))
        for v in value_keys:
            vals = [item.get(v, 0) for item in items]
            base[v] = sum(vals) / len(items)
            base[f"{v}_sd"] = _stdev(vals)
        base["n"] = len(items)
        out.append(base)
    return out


def _aa_color_map(letters: Iterable[str], cmap: Any) -> Dict[str, Any]:
    """
    Build a consistent amino-acid -> color map following AMINO_ORDER using the
    fixed AA_COLORS palette; fall back to the provided cmap for unknown letters.
    """
    colors: Dict[str, Any] = {}
    missing: List[str] = []
    for aa in letters:
        if aa in AA_COLORS:
            colors[aa] = AA_COLORS[aa]
        else:
            missing.append(aa)
    denom = max(1, len(missing))
    for idx, aa in enumerate(missing):
        colors[aa] = cmap(idx / denom)
    return colors


def _legend_outside_right(fig: plt.Figure, handles: List[Any], title: str, n_items: int) -> None:
    """
    Place legend to the right of the plot area while dynamically reserving space.
    """
    extra = min(0.35, 0.02 + 0.00005 * max(1, n_items))
    right_margin = 1.0 - extra
    fig.tight_layout(rect=[0, 0, right_margin, 1])
    legend_x = right_margin + extra / 2.0
    fig.legend(
        handles=handles,
        title=title,
        loc="center left",
        bbox_to_anchor=(legend_x, 0.5),
        fontsize=9,
    )


def filter_records(
    records: Sequence[Dict[str, Any]],
    taxonomy_terms: Optional[Iterable[str]] = None,
    protein_types: Optional[Iterable[str]] = None,
    partial_full: Optional[str] = None,
    length_range: Optional[Tuple[int, int]] = None,
    length_threshold: Optional[int] = None,
    length_mode: str = "ge",
    longest_factor: Optional[float] = None,
    longest_factor_scope: str = "species",
) -> List[Dict[str, Any]]:
    filtered = list(records)

    if taxonomy_terms:
        terms_lower = {str(t).strip().lower() for t in taxonomy_terms if str(t).strip()}
        tmp: List[Dict[str, Any]] = []
        for rec in filtered:
            lineage_lower = {str(x).lower() for x in _taxonomy_lineage(rec)}
            if lineage_lower.intersection(terms_lower):
                tmp.append(rec)
        filtered = tmp

    if protein_types:
        type_terms = [str(t).strip().lower() for t in protein_types if str(t).strip()]
        tmp = []
        for rec in filtered:
            rec_type = str(rec.get("type", "")).strip().lower()
            if any(term in rec_type for term in type_terms):
                tmp.append(rec)
        filtered = tmp

    if partial_full is not None:
        pf_target = partial_full.lower()
        filtered = [rec for rec in filtered if str(rec.get("partial_full", "")).lower() == pf_target]

    if length_range is not None:
        min_len, max_len = length_range
        tmp = []
        for rec in filtered:
            L = rec.get("length", 0) or 0
            if (min_len is None or L >= min_len) and (max_len is None or L <= max_len):
                tmp.append(rec)
        filtered = tmp

    if length_threshold is not None:
        mode = length_mode.lower()
        tmp = []
        for rec in filtered:
            L = rec.get("length", 0) or 0
            if mode == "ge" and L >= length_threshold:
                tmp.append(rec)
            elif mode == "le" and L <= length_threshold:
                tmp.append(rec)
        filtered = tmp

    if longest_factor is not None and longest_factor > 1 and filtered:
        scope = (longest_factor_scope or "species").lower()
        if scope not in {"species", "global"}:
            raise ValueError("longest_factor_scope must be 'species' or 'global'.")
        if scope == "global":
            max_len = max(rec.get("length", 0) or 0 for rec in filtered)
            cutoff = max_len / float(longest_factor)
            filtered = [rec for rec in filtered if (rec.get("length", 0) or 0) >= cutoff]
        else:
            max_by_org: Dict[str, int] = {}
            for rec in filtered:
                org = str(rec.get("organism", "Unknown"))
                L = rec.get("length", 0) or 0
                if L > max_by_org.get(org, 0):
                    max_by_org[org] = L
            tmp = []
            for rec in filtered:
                org = str(rec.get("organism", "Unknown"))
                L = rec.get("length", 0) or 0
                cutoff = max_by_org.get(org, 0) / float(longest_factor)
                if L >= cutoff:
                    tmp.append(rec)
            filtered = tmp

    return filtered


def _aggregate_sum(rows: List[Dict[str, Any]], keys: List[str], value_keys: List[str]) -> List[Dict[str, Any]]:
    grouped: Dict[Tuple, List[Dict[str, Any]]] = defaultdict(list)
    for r in rows:
        grouped[tuple(r[k] for k in keys)].append(r)
    out: List[Dict[str, Any]] = []
    for key, items in grouped.items():
        base = dict(zip(keys, key))
        for v in value_keys:
            base[v] = sum(item.get(v, 0) for item in items)
        out.append(base)
    return out


# ---------- Plotters ---------- #


def plot_serine(
    summary: Dict[str, Any],
    out_dir: Path,
    min_n: int,
    max_n: int,
    suffix: str = "",
    order_anchor: str = "",
    tables_dir: Optional[Path] = None,
    taxonomy_terms: Optional[Iterable[str]] = None,
    protein_types: Optional[Iterable[str]] = None,
    partial_full: Optional[str] = None,
    length_range: Optional[Tuple[int, int]] = None,
    length_threshold: Optional[int] = None,
    length_mode: str = "ge",
    longest_factor: Optional[float] = None,
) -> None:
    records = summary.get("analyzed_records", [])
    if not records:
        return

    rows = [
        {
            "Organism": r.get("organism", "Unknown"),
            "Type": r.get("type", "Unknown"),
            "Serine_Count": r.get("serine_count", 0),
            "Serine_Fraction": r.get("serine_fraction", 0.0),
            "Length": r.get("length", 0),
        }
        for r in records
    ]
    agg = _aggregate_stats(rows, ["Organism", "Type"], ["Serine_Count", "Serine_Fraction", "Length"])
    agg.sort(key=lambda x: (x["Organism"], x["Type"]))

    types = {r["Type"] for r in agg}
    colors = _type_colors(types)
    order_list = _species_order(records, order_anchor)
    organisms = [org for org in order_list if any(a["Organism"] == org for a in agg)]
    if not organisms:
        organisms = sorted({r["Organism"] for r in agg})
    x_map = {org: i for i, org in enumerate(organisms)}

    fig, (ax_count, ax_frac) = plt.subplots(2, 1, figsize=(max(10, len(organisms) * 0.4), 10), sharex=True)

    width = 0.8 / max(1, len(types))
    for j, t in enumerate(sorted(types)):
        subset = [r for r in agg if r["Type"] == t]
        xs = [x_map[r["Organism"]] + (j - len(types) / 2) * width + width / 2 for r in subset]
        count_bars = ax_count.bar(
            xs,
            [r["Serine_Count"] for r in subset],
            width=width,
            color=colors[t],
            label=t,
            edgecolor="black",
            linewidth=0.5,
            yerr=[(sd if sd > 0 else float("nan")) for sd in (r.get("Serine_Count_sd", 0.0) for r in subset)],
            capsize=2,
        )
        frac_bars = ax_frac.bar(
            xs,
            [r["Serine_Fraction"] for r in subset],
            width=width,
            color=colors[t],
            edgecolor="black",
            linewidth=0.5,
            yerr=[(sd if sd > 0 else float("nan")) for sd in (r.get("Serine_Fraction_sd", 0.0) for r in subset)],
            capsize=2,
        )

        # Annotations: sequence length on count plot, fraction % on fraction plot
        for bar, row in zip(count_bars, subset):
            length = row.get("Length", 0)
            length_sd = row.get("Length_sd", 0.0)
            if length_sd:
                length_label = f"L={length:.0f}\u00b1{length_sd:.0f}"
            else:
                length_label = f"L={length:.0f}"
            ax_count.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + max(1.5, bar.get_height() * 0.02),
                length_label,
                ha="center",
                va="bottom",
                fontsize=7,
                color="gray",
            )
        for bar, row in zip(frac_bars, subset):
            ax_frac.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + max(0.5, bar.get_height() * 0.02),
                f"{row.get('Serine_Fraction', 0):.1f}%",
                ha="center",
                va="bottom",
                fontsize=7,
                color="gray",
            )

    ax_count.set_ylabel("Serine count")
    ax_frac.set_ylabel("Serine fraction (%)")
    ax_count.set_title("Serine content by protein type")
    ax_frac.set_title("Serine fraction by protein type")
    _axis_label_rotate(ax_frac)
    ax_frac.set_xticks(list(x_map.values()))
    ax_frac.set_xticklabels([org.replace("_", " ").title() for org in organisms], fontsize=8, rotation=45, ha="right")
    ax_count.grid(axis="y", linestyle="--", alpha=0.6)
    ax_frac.grid(axis="y", linestyle="--", alpha=0.6)
    handles = [mpatches.Patch(color=colors[t], label=t) for t in sorted(types)]
    _legend_outside_right(fig, handles, "Protein type", len(handles))
    suffix_str = f"_{suffix}" if suffix else ""
    fig.savefig(out_dir / f"serine_content_n{min_n}-{max_n}{suffix_str}.png", dpi=300, bbox_inches="tight")
    plt.close(fig)

    tables_dir = _tables_output_dir(
        out_dir,
        tables_dir,
        taxonomy_terms=taxonomy_terms,
        partial_full=partial_full,
        protein_types=protein_types,
        length_range=length_range,
        length_threshold=length_threshold,
        length_mode=length_mode,
        longest_factor=longest_factor,
    )
    header = [
        "organism",
        "type",
        "serine_count_mean",
        "serine_count_sd",
        "serine_fraction_mean",
        "serine_fraction_sd",
        "length_mean",
        "length_sd",
    ]
    rows = [
        [
            row["Organism"],
            row["Type"],
            f"{row.get('Serine_Count', 0.0):.3f}",
            f"{row.get('Serine_Count_sd', 0.0):.3f}",
            f"{row.get('Serine_Fraction', 0.0):.3f}",
            f"{row.get('Serine_Fraction_sd', 0.0):.3f}",
            f"{row.get('Length', 0.0):.3f}",
            f"{row.get('Length_sd', 0.0):.3f}",
        ]
        for row in agg
    ]
    _write_table_files(header, rows, tables_dir / f"serine_content_n{min_n}-{max_n}{suffix_str}")


def plot_total_sxn(
    summary: Dict[str, Any],
    out_dir: Path,
    min_n: int,
    max_n: int,
    suffix: str = "",
    order_anchor: str = "",
    tables_dir: Optional[Path] = None,
    taxonomy_terms: Optional[Iterable[str]] = None,
    protein_types: Optional[Iterable[str]] = None,
    partial_full: Optional[str] = None,
    length_range: Optional[Tuple[int, int]] = None,
    length_threshold: Optional[int] = None,
    length_mode: str = "ge",
    longest_factor: Optional[float] = None,
) -> None:
    records = summary.get("analyzed_records", [])
    if not records:
        return

    rows = [
        {
            "Organism": r.get("organism", "Unknown"),
            "Type": r.get("type", "Unknown"),
            "Fraction": r.get("fraction_motif_residues", 0.0),
            "Length": r.get("length", 0),
        }
        for r in records
    ]
    agg = _aggregate_stats(rows, ["Organism", "Type"], ["Fraction", "Length"])
    agg = [r for r in agg if r.get("Fraction", 0) > 0]
    agg.sort(key=lambda x: (x["Organism"], x["Type"]))

    types = {r["Type"] for r in agg}
    colors = _type_colors(types)
    order_list = _species_order(records, order_anchor)
    organisms = [org for org in order_list if any(a["Organism"] == org for a in agg)]
    if not organisms:
        organisms = sorted({r["Organism"] for r in agg})
    if not organisms:
        return

    def plot_chunk(ax: plt.Axes, orgs: List[str]) -> None:
        width = 0.8 / max(1, len(types))
        x_map = {org: i for i, org in enumerate(orgs)}
        for j, t in enumerate(sorted(types)):
            subset = [r for r in agg if r["Type"] == t and r["Organism"] in orgs]
            if not subset:
                continue
            xs = [x_map[r["Organism"]] + (j - len(types) / 2) * width + width / 2 for r in subset]
            bars = ax.bar(
                xs,
                [r["Fraction"] for r in subset],
                width=width,
                color=colors[t],
                edgecolor="black",
                linewidth=0.5,
                label=t,
                yerr=[(sd if sd > 0 else float("nan")) for sd in (r.get("Fraction_sd", 0.0) for r in subset)],
                capsize=2,
            )
            for bar, row in zip(bars, subset):
                length = row.get("Length", 0)
                length_sd = row.get("Length_sd", 0.0)
                if length_sd:
                    length_label = f"L={length:.0f}\u00b1{length_sd:.0f}"
                else:
                    length_label = f"L={length:.0f}"
                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    bar.get_height() + max(0.5, bar.get_height() * 0.02),
                    length_label,
                    ha="center",
                    va="bottom",
                    fontsize=7,
                    color="gray",
                )
        ax.set_ylabel("% of sequence in [SX]_n")
        ax.set_xticks(list(x_map.values()))
        ax.set_xticklabels([org.replace("_", " ").title() for org in orgs], fontsize=8, rotation=45, ha="right")
        ax.grid(axis="y", linestyle="--", alpha=0.6)

    y_max = max((r["Fraction"] for r in agg), default=0) * 1.1

    if len(organisms) > 30:
        split = len(organisms) // 2
        top_orgs = organisms[:split]
        bottom_orgs = organisms[split:]
        fig, (ax_top, ax_bot) = plt.subplots(
            2,
            1,
            figsize=(max(12, max(len(top_orgs), len(bottom_orgs)) * 0.4), 10),
            sharey=True,
        )
        plot_chunk(ax_top, top_orgs)
        plot_chunk(ax_bot, bottom_orgs)
        ax_top.set_title("Total [SX]_n coverage by protein type (top)")
        ax_bot.set_title("Total [SX]_n coverage by protein type (bottom)")
        ax_top.set_ylim(0, y_max)
        ax_bot.set_ylim(0, y_max)
        handles = [mpatches.Patch(color=colors[t], label=t) for t in sorted(types)]
        _legend_outside_right(fig, handles, "Protein type", len(handles))
        suffix_str = f"_{suffix}" if suffix else ""
        fig.savefig(out_dir / f"total_sxn_coverage_n{min_n}-{max_n}{suffix_str}.png", dpi=300, bbox_inches="tight")
        plt.close(fig)
    else:
        fig, ax = plt.subplots(figsize=(max(10, len(organisms) * 0.4), 6))
        plot_chunk(ax, organisms)
        ax.set_title("Total [SX]_n coverage by protein type")
        ax.set_ylim(0, y_max)
        handles = [mpatches.Patch(color=colors[t], label=t) for t in sorted(types)]
        _legend_outside_right(fig, handles, "Protein type", len(handles))
        suffix_str = f"_{suffix}" if suffix else ""
        fig.savefig(out_dir / f"total_sxn_coverage_n{min_n}-{max_n}{suffix_str}.png", dpi=300, bbox_inches="tight")
        plt.close(fig)

    tables_dir = _tables_output_dir(
        out_dir,
        tables_dir,
        taxonomy_terms=taxonomy_terms,
        partial_full=partial_full,
        protein_types=protein_types,
        length_range=length_range,
        length_threshold=length_threshold,
        length_mode=length_mode,
        longest_factor=longest_factor,
    )
    header = ["organism", "type", "fraction_mean", "fraction_sd", "length_mean", "length_sd"]
    rows = [
        [
            row["Organism"],
            row["Type"],
            f"{row.get('Fraction', 0.0):.3f}",
            f"{row.get('Fraction_sd', 0.0):.3f}",
            f"{row.get('Length', 0.0):.3f}",
            f"{row.get('Length_sd', 0.0):.3f}",
        ]
        for row in agg
    ]
    _write_table_files(header, rows, tables_dir / f"total_sxn_coverage_n{min_n}-{max_n}{suffix_str}")


def plot_motif_counts_and_fraction(
    summary: Dict[str, Any],
    out_dir: Path,
    min_n: int,
    max_n: int,
    suffix: str = "",
    order_anchor: str = "",
    tables_dir: Optional[Path] = None,
    taxonomy_terms: Optional[Iterable[str]] = None,
    protein_types: Optional[Iterable[str]] = None,
    partial_full: Optional[str] = None,
    length_range: Optional[Tuple[int, int]] = None,
    length_threshold: Optional[int] = None,
    length_mode: str = "ge",
    longest_factor: Optional[float] = None,
) -> None:
    records = summary.get("analyzed_records", [])
    if not records:
        return

    flat = _flatten_motif_records(records)
    if not flat:
        return

    # Average over duplicate accessions/species by Organism/Type/n
    grouped: Dict[Tuple[Any, ...], List[Dict[str, Any]]] = defaultdict(list)
    for r in flat:
        grouped[(r["Organism"], r["Type"], r["n"])].append(r)

    agg: List[Dict[str, Any]] = []
    for key, items in grouped.items():
        organism, ptype, n_val = key
        count_vals = [i["Count"] for i in items]
        residues_vals = [i["Residues_Covered"] for i in items]
        percent_vals = [i["Percent"] for i in items]
        length_vals = [i["Length"] for i in items]
        agg.append(
            {
                "Organism": organism,
                "Type": ptype,
                "n": n_val,
                "Count": sum(count_vals) / len(count_vals),
                "Residues_Covered": sum(residues_vals) / len(residues_vals),
                "Percent": sum(percent_vals) / len(percent_vals),
                "Length": sum(length_vals) / len(length_vals),
                "Count_sd": _stdev(count_vals),
                "Percent_sd": _stdev(percent_vals),
            }
        )

    types = sorted({r["Type"] for r in agg})

    for t in types:
        subset = [r for r in agg if r["Type"] == t]
        order_list = _species_order(records, order_anchor)
        organisms = [org for org in order_list if any(r["Organism"] == org for r in subset)]
        if not organisms:
            organisms = sorted({r["Organism"] for r in subset})
        x_map = {org: i for i, org in enumerate(organisms)}
        n_values = sorted({r["n"] for r in subset})
        colors = plt.colormaps.get_cmap("viridis")
        width = 0.8 / max(1, len(n_values))

        fig, (ax_count, ax_frac) = plt.subplots(2, 1, figsize=(max(10, len(organisms) * 0.4), 10), sharex=True)
        for i, n in enumerate(n_values):
            n_rows = [r for r in subset if r["n"] == n]
            xs = [x_map[r["Organism"]] + (i - len(n_values) / 2) * width + width / 2 for r in n_rows]
            ax_count.bar(
                xs,
                [r["Count"] for r in n_rows],
                width=width,
                color=colors(i / max(1, len(n_values))),
                edgecolor="black",
                linewidth=0.5,
                label=f"n={n}",
                yerr=[(sd if sd > 0 else float("nan")) for sd in (r.get("Count_sd", 0.0) for r in n_rows)],
                capsize=2,
            )
            ax_frac.bar(
                xs,
                [r["Percent"] for r in n_rows],
                width=width,
                color=colors(i / max(1, len(n_values))),
                edgecolor="black",
                linewidth=0.5,
                yerr=[(sd if sd > 0 else float("nan")) for sd in (r.get("Percent_sd", 0.0) for r in n_rows)],
                capsize=2,
            )

        ax_count.set_ylabel("[SX]_n count")
        ax_frac.set_ylabel("[SX]_n fraction per motif (%)")
        ax_count.set_title(f"[SX]_n motif counts - {t}")
        ax_frac.set_title(f"[SX]_n motif fraction - {t}")
        ax_frac.set_xticks(list(x_map.values()))
        ax_frac.set_xticklabels([org.replace("_", " ").title() for org in organisms], fontsize=8, rotation=45, ha="right")
        ax_count.grid(axis="y", linestyle="--", alpha=0.6)
        ax_frac.grid(axis="y", linestyle="--", alpha=0.6)
        handles, labels = ax_count.get_legend_handles_labels()
        _legend_outside_right(fig, handles, "Motif length", len(handles))
        suffix_str = f"_{suffix}" if suffix else ""
        fig.savefig(out_dir / f"sxn_motifs_{t.replace(' ', '_')}_n{min_n}-{max_n}{suffix_str}.png", dpi=300, bbox_inches="tight")
        plt.close(fig)

        tables_dir = _tables_output_dir(
            out_dir,
            tables_dir,
            taxonomy_terms=taxonomy_terms,
            partial_full=partial_full,
            protein_types=protein_types,
            length_range=length_range,
            length_threshold=length_threshold,
            length_mode=length_mode,
            longest_factor=longest_factor,
        )
        header = [
            "organism",
            "type",
            "n",
            "count_mean",
            "count_sd",
            "percent_mean",
            "percent_sd",
            "length_mean",
        ]
        rows = [
            [
                row["Organism"],
                row["Type"],
                row["n"],
                f"{row.get('Count', 0.0):.3f}",
                f"{row.get('Count_sd', 0.0):.3f}",
                f"{row.get('Percent', 0.0):.3f}",
                f"{row.get('Percent_sd', 0.0):.3f}",
                f"{row.get('Length', 0.0):.3f}",
            ]
            for row in subset
        ]
        _write_table_files(
            header,
            rows,
            tables_dir / f"sxn_motifs_{t.replace(' ', '_')}_n{min_n}-{max_n}{suffix_str}",
        )


def plot_x_composition(
    summary: Dict[str, Any],
    out_dir: Path,
    min_n: int,
    max_n: int,
    suffix: str = "",
    order_anchor: str = "",
    tables_dir: Optional[Path] = None,
    taxonomy_terms: Optional[Iterable[str]] = None,
    protein_types: Optional[Iterable[str]] = None,
    partial_full: Optional[str] = None,
    length_range: Optional[Tuple[int, int]] = None,
    length_threshold: Optional[int] = None,
    length_mode: str = "ge",
    longest_factor: Optional[float] = None,
) -> None:
    records = summary.get("analyzed_records", [])
    if not records:
        return

    # Flatten X composition per record
    comp_rows: List[Dict[str, Any]] = []
    for rec in records:
        x_counts_by_n: Dict[str, Dict[str, int]] = rec.get("x_residue_counts", {})
        total_counts: Dict[str, int] = defaultdict(int)
        for x_counts in x_counts_by_n.values():
            for aa, cnt in x_counts.items():
                total_counts[aa] += cnt
        total = sum(total_counts.values())
        if total == 0:
            continue
        row = {
            "Organism": rec.get("organism", "Unknown"),
            "Type": rec.get("type", "Unknown"),
            "Total": total,
        }
        for aa, cnt in total_counts.items():
            row[aa] = (cnt / total) * 100
        comp_rows.append(row)

    if not comp_rows:
        return

    # Average percentages per Organism/Type
    all_aas = {k for r in comp_rows for k in r.keys() if k not in {"Organism", "Type", "Total"}}
    aa_keys = [aa for aa in AMINO_ORDER if aa in all_aas] + [aa for aa in sorted(all_aas) if aa not in AMINO_ORDER]
    agg = _aggregate_mean(comp_rows, ["Organism", "Type"], aa_keys + ["Total"])

    types = sorted({r["Type"] for r in agg})
    cmap = plt.colormaps.get_cmap("tab20")
    colors_map = _aa_color_map(aa_keys, cmap)
    for t in types:
        subset = [r for r in agg if r["Type"] == t]
        if not subset:
            continue

        order_list = _species_order(records, order_anchor)
        organisms = [org for org in order_list if any(r["Organism"] == org for r in subset)]
        if not organisms:
            organisms = [r["Organism"] for r in subset]
        # Keep only AA columns that have data for this type
        present_aa = [aa for aa in aa_keys if any(r.get(aa, 0) > 0 for r in subset)]
        if not present_aa:
            continue
        # Build value matrix aligned to ordered organisms
        plot_matrix: List[List[float]] = []
        for org in organisms:
            row_rec = next((r for r in subset if r["Organism"] == org), None)
            if not row_rec:
                row_vals = [0.0 for _ in present_aa]
            else:
                row_vals = [row_rec.get(aa, 0.0) for aa in present_aa]
            plot_matrix.append(row_vals)
        fig, ax = plt.subplots(figsize=(10, max(6, len(organisms) * 0.35)))
        bottoms = [0.0] * len(organisms)
        for i, aa in enumerate(present_aa):
            vals = [row[i] for row in plot_matrix]
            ax.barh(
                organisms,
                vals,
                left=bottoms,
                color=colors_map.get(aa),
                edgecolor="black",
                linewidth=0.4,
                label=f"X={aa}",
            )
            bottoms = [b + v for b, v in zip(bottoms, vals)]
        ax.set_xlabel("Percentage of X residues (%)")
        ax.set_title(f"X-residue composition in [SX]_n motifs (n={min_n}..{max_n}) – {t}")
        ax.invert_yaxis()
        handles, labels = ax.get_legend_handles_labels()
        _legend_outside_right(fig, handles, "Residue", len(handles))
        ax.grid(axis="x", linestyle="--", alpha=0.6)
        ax.set_yticks(range(len(organisms)))
        ax.set_yticklabels([org.replace("_", " ").title() for org in organisms])
        suffix_str = f"_{suffix}" if suffix else ""
        fig.savefig(out_dir / f"x_composition_{t.replace(' ', '_')}_n{min_n}-{max_n}{suffix_str}.png", dpi=300, bbox_inches="tight")
        plt.close(fig)

        tables_dir = _tables_output_dir(
            out_dir,
            tables_dir,
            taxonomy_terms=taxonomy_terms,
            partial_full=partial_full,
            protein_types=protein_types,
            length_range=length_range,
            length_threshold=length_threshold,
            length_mode=length_mode,
            longest_factor=longest_factor,
        )
        header = ["organism", "type"] + [f"x_{aa}" for aa in present_aa]
        rows = [
            [row["Organism"], row["Type"], *[f"{row.get(aa, 0.0):.3f}" for aa in present_aa]]
            for row in subset
        ]
        _write_table_files(
            header,
            rows,
            tables_dir / f"x_composition_{t.replace(' ', '_')}_n{min_n}-{max_n}{suffix_str}",
        )


def plot_phylo_types(
    summary: Dict[str, Any],
    out_dir: Path,
    min_n: int,
    max_n: int,
    suffix: str = "",
    order_anchor: str = "",
) -> None:
    records = summary.get("analyzed_records", [])
    if not records:
        return

    # Build taxonomy paths and type presence (order -> ... -> genus -> organism)
    target_ranks = [
        "order",
        "suborder",
        "infraorder",
        "superfamily",
        "family",
        "subfamily",
        "tribe",
        "genus",
    ]
    anchor_lc = order_anchor.lower() if order_anchor else ""

    paths: List[Tuple[Tuple[str, ...], str]] = []
    type_by_org: Dict[str, set] = defaultdict(set)

    for rec in records:
        lineage = rec.get("taxonomy_from_order") or rec.get("taxonomy_from_araneae") or rec.get("taxonomy_full") or []
        if not lineage:
            continue
        if anchor_lc:
            for i, name in enumerate(lineage):
                if name.lower() == anchor_lc:
                    lineage = lineage[i:]
                    break
        lineage = lineage[: len(target_ranks)]
        if anchor_lc and (not lineage or lineage[0].lower() != anchor_lc):
            continue

        org = rec.get("organism", "Unknown")
        type_by_org[org].add(rec.get("type", "Unknown"))
        paths.append((tuple(lineage), org))

    if not paths:
        return

    paths = sorted(set(paths))
    types = sorted({t for ts in type_by_org.values() for t in ts})
    colors = _type_colors(types)

    depth_map = {rank: idx for idx, rank in enumerate(target_ranks)}
    organism_depth = len(target_ranks)

    fig, ax = plt.subplots(figsize=(10, max(6, len(paths) * 0.4)))
    y = 0.0
    y_min = 0.0
    node_y: Dict[Tuple[str, ...], float] = {}

    for lineage, org in paths:
        current_y = y
        levels = list(lineage) + [org]
        ranks = target_ranks[: len(lineage)] + ["organism"]

        for idx, (level_name, rank) in enumerate(zip(levels, ranks)):
            key = tuple(levels[: idx + 1])
            if key in node_y:
                continue

            if rank == "order":
                ax.hlines(current_y, depth_map[rank], depth_map[rank] + 0.4, color="black", linewidth=0.8)
                ax.text(depth_map[rank] - 0.1, current_y, level_name, ha="right", va="center", fontsize=10, fontweight="bold")
            elif rank == "organism":
                parent_key = key[:-1]
                parent_y = node_y.get(parent_key, current_y)
                ax.vlines(organism_depth - 0.5, parent_y, current_y, color="black", linewidth=0.8)
                ax.hlines(current_y, organism_depth - 0.5, organism_depth, color="black", linewidth=0.8)
                ax.text(organism_depth + 0.05, current_y, level_name, ha="left", va="center", fontsize=9, fontstyle="italic")
            else:
                parent_key = key[:-1]
                parent_y = node_y.get(parent_key, current_y)
                x_pos = depth_map.get(rank, len(target_ranks) - 1)
                ax.vlines(x_pos - 0.5, parent_y, current_y, color="black", linewidth=0.8)
                ax.hlines(current_y, x_pos - 0.5, x_pos, color="black", linewidth=0.8)
                ax.text(x_pos + 0.05, current_y, level_name, ha="left", va="center", fontsize=9)

            node_y[key] = current_y
        y_min = min(y_min, current_y)
        y -= 1.5

    # Protein type markers
    for org, types_set in type_by_org.items():
        org_key = None
        for key in node_y:
            if key and key[-1] == org:
                org_key = key
                break
        if not org_key:
            continue
        org_y = node_y[org_key]
        for i, t in enumerate(sorted(types_set)):
            ax.plot(organism_depth + 0.4 + 0.12 * i, org_y, marker="s", color=colors[t], markersize=6, label=t)

    handles = [mpatches.Patch(color=colors[t], label=t) for t in sorted(types)]
    by_label = {h.get_label(): h for h in handles}
    _legend_outside_right(fig, list(by_label.values()), "Protein type", len(by_label))

    # Rank headers
    rank_labels = target_ranks + ["organism"]
    for idx, rank in enumerate(rank_labels):
        ax.text(idx, 0.6, rank.title(), ha="center", va="bottom", fontsize=9, fontweight="bold")

    ax.set_ylim(y, 1)
    ax.set_xlim(-0.3, organism_depth + 1.5)
    ax.axis("off")
    ax.set_title(f"Taxonomy with protein types (n range {min_n}..{max_n})")
    fig.tight_layout()
    suffix_str = f"_{suffix}" if suffix else ""
    fig.savefig(out_dir / f"phylo_types_n{min_n}-{max_n}{suffix_str}.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


# ---------- CLI ---------- #


def main() -> None:
    parser = argparse.ArgumentParser(description="Plot outputs of serine_sxn_analysis_lib.")
    parser.add_argument("path", type=Path, help="Path to serine_sxn_analysis.json (or the .md).")
    parser.add_argument(
        "--taxonomy",
        nargs="*",
        default=None,
        help="Optional taxonomy names to filter by (e.g. Annulipalpia Hydropsychoidea).",
    )
    parser.add_argument(
        "--type",
        dest="protein_types",
        nargs="*",
        default=None,
        help="Optional protein type substrings to filter by (e.g. 'light chain').",
    )
    parser.add_argument(
        "--partial-full",
        dest="partial_full",
        choices=["full", "partial", "none"],
        default="full",
        help="Filter by partial/full sequences (default: full). Use 'none' to disable.",
    )
    parser.add_argument(
        "--length-range",
        nargs=2,
        type=int,
        metavar=("MIN", "MAX"),
        default=None,
        help="Optional inclusive length range filter, e.g. --length-range 100 2450.",
    )
    parser.add_argument(
        "--length-threshold",
        type=int,
        default=None,
        help="Optional length threshold used with --length-mode.",
    )
    parser.add_argument(
        "--length-mode",
        choices=["ge", "le"],
        default="ge",
        help="If --length-threshold is set, use '>=' (ge) or '<=' (le). Default: ge.",
    )
    parser.add_argument(
        "--longest-factor",
        type=float,
        default=None,
        help=(
            "If set, sequences shorter than (longest_length / longest_factor) "
            "are excluded AFTER other filters. E.g. '--longest-factor 2' keeps only "
            "sequences at least half as long as the longest one."
        ),
    )
    parser.add_argument(
        "--longest-factor-scope",
        choices=["species", "global"],
        default="species",
        help="Apply longest-factor per species (default) or globally across all records.",
    )
    args = parser.parse_args()

    summary = load_summary(args.path)
    out_dir = ensure_out_dir(args.path)
    min_n = summary.get("min_n", 0)
    max_n = summary.get("max_n", 0)
    order_anchor = summary.get("order_name", "")
    if not order_anchor:
        # try to infer from first record
        recs = summary.get("analyzed_records", [])
        if recs:
            tax = recs[0].get("taxonomy_from_order") or recs[0].get("taxonomy_full") or []
            if tax:
                order_anchor = tax[0]

    all_records = summary.get("analyzed_records", [])
    pf = None if args.partial_full == "none" else args.partial_full
    filtered_records = filter_records(
        all_records,
        taxonomy_terms=args.taxonomy,
        protein_types=args.protein_types,
        partial_full=pf,
        length_range=tuple(args.length_range) if args.length_range else None,
        length_threshold=args.length_threshold,
        length_mode=args.length_mode,
        longest_factor=args.longest_factor,
        longest_factor_scope=args.longest_factor_scope,
    )

    if not filtered_records:
        return

    categories = ["full", "partial", "unknown"]
    present = {r.get("partial_full", "unknown") for r in filtered_records}
    for cat in categories:
        if cat not in present:
            continue
        subset = [r for r in filtered_records if r.get("partial_full", "unknown") == cat]
        if not subset:
            continue
        label = cat
        cat_out_dir = category_out_dir(out_dir, cat, min_n, max_n)
        sub_summary = {
            **summary,
            "analyzed_records": subset,
        }
        plot_serine(sub_summary, cat_out_dir, min_n, max_n, suffix=label, order_anchor=order_anchor)
        plot_total_sxn(sub_summary, cat_out_dir, min_n, max_n, suffix=label, order_anchor=order_anchor)
        plot_motif_counts_and_fraction(sub_summary, cat_out_dir, min_n, max_n, suffix=label, order_anchor=order_anchor)
        plot_x_composition(sub_summary, cat_out_dir, min_n, max_n, suffix=label, order_anchor=order_anchor)
        plot_phylo_types(sub_summary, cat_out_dir, min_n, max_n, suffix=label, order_anchor=order_anchor)


if __name__ == "__main__":
    main()
