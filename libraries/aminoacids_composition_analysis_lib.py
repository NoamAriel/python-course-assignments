import csv
import json
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple, Union

import pandas as pd

def _slugify(text: str) -> str:
    """Make a filesystem-friendly slug."""
    return "".join(ch if ch.isalnum() else "_" for ch in text).strip("_") or "none"


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


def _aa_color_map(letters: Sequence[str], cmap: Any) -> Dict[str, Any]:
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
    # assign fallback colors for any unexpected amino-acid symbols
    denom = max(1, len(missing))
    for idx, aa in enumerate(missing):
        colors[aa] = cmap(idx / denom)
    return colors


def normalize_letters(letters: Union[str, Iterable[str]]) -> List[str]:
    """
    Normalize a user-provided collection of letters (amino acids).

    - Accepts a string like "SGP" or an iterable of single-character strings.
    - Filters out non-alphabetic characters.
    - Returns unique uppercase letters, ordered by AMINO_ORDER; any others keep
      their first-seen order at the end.
    """
    if isinstance(letters, str):
        raw = letters
    else:
        raw = "".join(str(x) for x in letters)

    seen = set()
    seen_in_order: List[str] = []
    for ch in raw:
        if not ch.isalpha():
            continue
        up = ch.upper()
        if up in seen:
            continue
        seen.add(up)
        seen_in_order.append(up)
    if not seen_in_order:
        raise ValueError("No valid amino-acid letters were provided.")
    ordered = [aa for aa in AMINO_ORDER if aa in seen]
    ordered += [aa for aa in seen_in_order if aa not in AMINO_ORDER]
    return ordered


def _is_species_leaf(node: Any) -> bool:
    """Heuristic to identify a species node inside the phylogenetic tree JSON."""
    if isinstance(node, dict):
        keys = set(node.keys())
        if "full" in keys or "partial" in keys:
            return True
        if any(isinstance(val, list) for val in node.values()):
            return True
    return False


def _collect_species_order_from_tree(tree: Any) -> List[str]:
    """Traverse the phylogenetic tree structure and return species in order."""
    order: List[str] = []
    seen: set[str] = set()

    def walk(node: Any) -> None:
        if not isinstance(node, dict):
            return
        for name, child in node.items():
            if _is_species_leaf(child) and name not in seen:
                seen.add(name)
                order.append(name)
            walk(child)

    walk(tree)
    return order


def _collect_species_order_from_md(md_path: Path) -> List[str]:
    """
    Lightweight parser for phylo_tree.md to recover species order when JSON is
    unavailable. Uses indentation order and keeps entries that look like species
    names (contain at least one space).
    """
    order: List[str] = []
    seen: set[str] = set()
    for raw in md_path.read_text(encoding="utf-8").splitlines():
        stripped = raw.lstrip()
        if not stripped.startswith("- "):
            continue
        candidate = stripped[2:].strip()
        if not candidate:
            continue
        name = candidate.split("(", 1)[0].strip()
        if " " not in name:
            continue
        if name in seen:
            continue
        seen.add(name)
        order.append(name)
    return order


def _load_phylo_species_order(
    root: Optional[Path],
    phylo_tree_json: Optional[Union[str, Path]] = None,
    phylo_tree_md: Optional[Union[str, Path]] = None,
) -> List[str]:
    """
    Resolve species ordering from the phylogenetic tree files (JSON preferred,
    Markdown as a fallback). Returns an empty list if nothing could be loaded.
    """
    candidates: List[Path] = []
    if phylo_tree_json:
        candidates.append(Path(phylo_tree_json))
    if root:
        candidates.append(root / "phylo_tree.json")

    for path in candidates:
        if path and path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                continue
            return _collect_species_order_from_tree(data)

    md_candidates: List[Path] = []
    if phylo_tree_md:
        md_candidates.append(Path(phylo_tree_md))
    if root:
        md_candidates.append(root / "phylo_tree.md")

    for path in md_candidates:
        if path and path.exists():
            try:
                return _collect_species_order_from_md(path)
            except Exception:
                continue

    return []


def load_records_from_root(root: Path, skip_tree: bool = True) -> List[Dict[str, Any]]:
    """
    Recursively load all JSON files under `root` that look like record files
    (must contain origin_sequence). Skips phylo_tree.json by default.

    This is copied from the serine/SXn analysis module so that both tools can share
    the same input structure.
    """
    records: List[Dict[str, Any]] = []
    for json_path in root.rglob("*.json"):
        if skip_tree and json_path.name.lower() == "phylo_tree.json":
            continue
        try:
            data = json.loads(json_path.read_text(encoding="utf-8"))
        except Exception:
            continue
        candidates = data if isinstance(data, list) else [data]
        for rec in candidates:
            if not isinstance(rec, dict) or not rec.get("origin_sequence"):
                continue

            # Infer partial/type from path if missing: .../<partial|full>/<type>/<file.json>
            parts = json_path.parent.parts
            if len(parts) >= 2:
                partial_candidate = parts[-2]
                type_candidate = parts[-1]
                if partial_candidate in ("partial", "full") and not rec.get("partial_full"):
                    rec["partial_full"] = partial_candidate
                if partial_candidate in ("partial", "full") and not rec.get("type"):
                    rec["type"] = type_candidate

            records.append(rec)
    return records


def _taxonomy_lineage(rec: Dict[str, Any]) -> List[str]:
    """Return the 'best' taxonomy lineage list for a record."""
    lineage = (
        rec.get("taxonomy_from_order")
        or rec.get("taxonomy_from_araneae")
        or rec.get("taxonomy_full")
        or []
    )
    return lineage


def _basic_taxonomy_fields(rec: Dict[str, Any]) -> Tuple[str, str, str]:
    """
    Compute suborder / superfamily / family with fallbacks.
    Indexing assumes taxonomy_lineage:
      [Order, Suborder, Superfamily, Family, ...]
    """
    lineage = _taxonomy_lineage(rec)
    suborder = lineage[1] if len(lineage) > 1 else "Unknown suborder"
    superfamily = lineage[2] if len(lineage) > 2 else "Unknown superfamily"
    family = lineage[3] if len(lineage) > 3 else "Unknown family"
    return suborder, superfamily, family


def filter_records(
    records: Sequence[Dict[str, Any]],
    taxonomy_terms: Optional[Iterable[str]] = None,
    protein_types: Optional[Iterable[str]] = None,
    partial_full: Optional[str] = "full",
    length_range: Optional[Tuple[int, int]] = None,
    length_threshold: Optional[int] = None,
    length_mode: str = "ge",  # "ge" (>=) or "le" (<=)
    longest_factor: Optional[float] = None,
    longest_factor_scope: str = "species",
) -> List[Dict[str, Any]]:
    """
    Filter a list of fibroin records according to several criteria.

    Parameters
    ----------
    taxonomy_terms:
        Iterable of taxonomy names (e.g. ["Annulipalpia", "Hydropsychoidea"]).
        A record is kept if *any* of these terms (case-insensitive) appears in its
        best taxonomy lineage.
        If None or empty, no taxonomy filtering is applied.

    protein_types:
        Iterable of protein type substrings, e.g. ["light chain", "heavy chain"].
        Matching is case-insensitive and uses substring logic on the record's `type`
        field. If None or empty, no type filtering is applied.

    partial_full:
        Either "full", "partial", or None.
        - "full": keep only full sequences (DEFAULT).
        - "partial": keep only partial sequences.
        - None: do not filter on this dimension.

    length_range:
        Optional (min_len, max_len) inclusive range. If provided, only sequences
        whose length is within this range are kept.

    length_threshold:
        Optional integer threshold used with `length_mode`:
        - "ge": keep sequences with length >= threshold
        - "le": keep sequences with length <= threshold

    longest_factor:
        Optional float > 0.
        After all above filters are applied, the algorithm keeps only sequences
        whose length >= L_max / longest_factor.

        For example:
        - If L_max = 3000 and longest_factor = 2, only sequences with length
          >= 1500 are kept.
        - If longest_factor <= 1, this filter has no effect.

    longest_factor_scope:
        "species" (default) applies the longest-factor filter per organism.
        "global" applies the filter across all remaining records.
    """
    filtered = list(records)

    # --- taxonomy filter ---
    if taxonomy_terms:
        terms_lower = {t.lower() for t in taxonomy_terms}
        tmp: List[Dict[str, Any]] = []
        for rec in filtered:
            lineage = [str(x) for x in _taxonomy_lineage(rec)]
            lineage_lower = {x.lower() for x in lineage}
            if lineage_lower.intersection(terms_lower):
                tmp.append(rec)
        filtered = tmp

    # --- protein type filter ---
    if protein_types:
        type_terms = [t.lower() for t in protein_types]
        tmp = []
        for rec in filtered:
            rec_type = str(rec.get("type", "")).lower()
            if any(term in rec_type for term in type_terms):
                tmp.append(rec)
        filtered = tmp

    # --- full/partial filter ---
    if partial_full is not None:
        pf_target = partial_full.lower()
        if pf_target not in {"full", "partial"}:
            raise ValueError("partial_full must be 'full', 'partial', or None.")
        tmp = []
        for rec in filtered:
            pf = str(rec.get("partial_full", "") or "unknown").lower()
            if pf == pf_target:
                tmp.append(rec)
        filtered = tmp

    # --- length range filter ---
    if length_range is not None:
        min_len, max_len = length_range
        tmp = []
        for rec in filtered:
            seq = rec.get("origin_sequence", "") or ""
            L = len(seq)
            if (min_len is None or L >= min_len) and (max_len is None or L <= max_len):
                tmp.append(rec)
        filtered = tmp

    # --- threshold filter ---
    if length_threshold is not None:
        mode = length_mode.lower()
        if mode not in {"ge", "le"}:
            raise ValueError("length_mode must be 'ge' or 'le'.")
        tmp = []
        for rec in filtered:
            seq = rec.get("origin_sequence", "") or ""
            L = len(seq)
            if mode == "ge" and L >= length_threshold:
                tmp.append(rec)
            elif mode == "le" and L <= length_threshold:
                tmp.append(rec)
        filtered = tmp

    # --- longest-factor filter ---
    if longest_factor is not None and longest_factor > 1 and filtered:
        scope = (longest_factor_scope or "species").lower()
        if scope not in {"species", "global"}:
            raise ValueError("longest_factor_scope must be 'species' or 'global'.")

        def _org_name(rec: Dict[str, Any]) -> str:
            return rec.get("organism_name") or rec.get("organism") or "Unknown"

        if scope == "global":
            max_len = max(len(rec.get("origin_sequence", "") or "") for rec in filtered)
            cutoff = max_len / float(longest_factor)
            tmp = []
            for rec in filtered:
                L = len(rec.get("origin_sequence", "") or "")
                if L >= cutoff:
                    tmp.append(rec)
            filtered = tmp
        else:
            max_by_org: Dict[str, int] = {}
            for rec in filtered:
                org = _org_name(rec)
                L = len(rec.get("origin_sequence", "") or "")
                if L > max_by_org.get(org, 0):
                    max_by_org[org] = L
            tmp = []
            for rec in filtered:
                org = _org_name(rec)
                L = len(rec.get("origin_sequence", "") or "")
                cutoff = max_by_org.get(org, 0) / float(longest_factor)
                if L >= cutoff:
                    tmp.append(rec)
            filtered = tmp

    return filtered


def analyze_letter_composition(
    records: Sequence[Dict[str, Any]],
    letters: Union[str, Iterable[str]],
) -> Dict[str, Any]:
    """
    Analyze the occurrence and percentage of specified letters in each sequence.

    Parameters
    ----------
    records:
        Iterable of fibroin records (each must have an 'origin_sequence' field).
    letters:
        String or iterable of single-character amino-acid codes, e.g. "SGP" or
        ["S", "G", "P"].

    Returns
    -------
    Dict with keys:
        - letters: list of target letters (sorted, unique, uppercase)
        - analyzed_records: list of per-record dictionaries
        - global_counts: total count of each letter across all sequences
        - global_fractions: percentage of each letter relative to all residues
        - num_records: number of analyzed sequences
        - total_length: sum of sequence lengths
    """
    target_letters = normalize_letters(letters)
    analyzed: List[Dict[str, Any]] = []

    global_counts: Dict[str, int] = {aa: 0 for aa in target_letters}
    total_length = 0

    for rec in records:
        seq = rec.get("origin_sequence", "") or ""
        if not seq:
            continue
        seq_up = seq.upper()
        L = len(seq_up)
        total_length += L

        suborder, superfamily, family = _basic_taxonomy_fields(rec)

        # Per-letter counts and fractions
        letter_counts: Dict[str, int] = {}
        letter_fractions: Dict[str, float] = {}
        total_target = 0
        for aa in target_letters:
            c = seq_up.count(aa)
            letter_counts[aa] = c
            total_target += c
            frac = (c / L * 100.0) if L else 0.0
            letter_fractions[aa] = frac
            global_counts[aa] += c

        total_target_fraction = (total_target / L * 100.0) if L else 0.0

        result = {
            "accession": rec.get("accession", ""),
            "title": rec.get("title", ""),
            "organism": rec.get("organism_name", "Unknown organism"),
            "taxonomy_from_order": rec.get("taxonomy_from_order", []),
            "taxonomy_from_araneae": rec.get("taxonomy_from_araneae", []),
            "taxonomy_full": rec.get("taxonomy_full", []),
            "suborder": suborder,
            "superfamily": superfamily,
            "family": family,
            "partial_full": rec.get("partial_full", "") or "unknown",
            "type": rec.get("type", "") or "unknown",
            "length": L,
            "letters": target_letters,
            "letter_counts": letter_counts,
            "letter_fractions": letter_fractions,
            "total_target_count": total_target,
            "total_target_fraction": total_target_fraction,
        }
        analyzed.append(result)

    # Global percentages based on total length of all sequences
    global_fractions: Dict[str, float] = {}
    for aa in target_letters:
        if total_length:
            global_fractions[aa] = global_counts[aa] / total_length * 100.0
        else:
            global_fractions[aa] = 0.0

    summary: Dict[str, Any] = {
        "letters": target_letters,
        "analyzed_records": analyzed,
        "global_counts": global_counts,
        "global_fractions": global_fractions,
        "num_records": len(analyzed),
        "total_length": total_length,
    }
    return summary


def _aggregate_by_species(
    records: Sequence[Dict[str, Any]],
    letters: Sequence[str],
    species_order: Optional[Sequence[str]] = None,
) -> List[Dict[str, Any]]:
    """
    Aggregate per-record letter counts/fractions into per-species averages.
    """
    rows: List[Dict[str, Any]] = []
    for rec in records:
        org = rec.get("organism", "Unknown")
        rec_counts = rec.get("letter_counts", {}) or {}
        rec_fracs = rec.get("letter_fractions", {}) or {}
        row: Dict[str, Any] = {
            "organism": org,
            "length": float(rec.get("length", 0) or 0.0),
            "total_target_fraction": float(rec.get("total_target_fraction", 0.0)),
        }
        for aa in letters:
            row[f"{aa}_count"] = float(rec_counts.get(aa, 0))
            row[f"{aa}_fraction"] = float(rec_fracs.get(aa, 0.0))
        rows.append(row)

    if not rows:
        return []

    df = pd.DataFrame(rows)
    grouped = df.groupby("organism", sort=False)
    mean_df = grouped.mean(numeric_only=True)
    sd_df = grouped.std(ddof=1, numeric_only=True).fillna(0.0)

    out: List[Dict[str, Any]] = []
    for org, mean_row in mean_df.iterrows():
        sd_row = sd_df.loc[org] if org in sd_df.index else pd.Series(dtype=float)
        counts = {aa: float(mean_row.get(f"{aa}_count", 0.0)) for aa in letters}
        counts_sd = {aa: float(sd_row.get(f"{aa}_count", 0.0)) for aa in letters}
        fractions = {aa: float(mean_row.get(f"{aa}_fraction", 0.0)) for aa in letters}
        fractions_sd = {aa: float(sd_row.get(f"{aa}_fraction", 0.0)) for aa in letters}
        out.append(
            {
                "organism": org,
                "length": float(mean_row.get("length", 0.0)),
                "length_sd": float(sd_row.get("length", 0.0)),
                "counts": counts,
                "counts_sd": counts_sd,
                "fractions": fractions,
                "fractions_sd": fractions_sd,
                "total_fraction_mean": float(mean_row.get("total_target_fraction", 0.0)),
                "total_fraction_sd": float(sd_row.get("total_target_fraction", 0.0)),
            }
        )
    if species_order:
        order_lookup = {name: idx for idx, name in enumerate(species_order)}
        out.sort(key=lambda x: (order_lookup.get(x["organism"], float("inf")), x["organism"]))
    else:
        out.sort(key=lambda x: x["organism"])
    return out


def plot_letter_composition(
    summary: Dict[str, Any],
    out_dir: Path,
    taxonomy_terms: Optional[Iterable[str]] = None,
    protein_types: Optional[Iterable[str]] = None,
    species_order: Optional[Sequence[str]] = None,
    tables_dir: Optional[Path] = None,
    length_range: Optional[Tuple[int, int]] = None,
    length_threshold: Optional[int] = None,
    length_mode: str = "ge",
    longest_factor: Optional[float] = None,
) -> Optional[Path]:
    """
    Plot per-species counts and fractions (percentages) for the analyzed letters.
    Produces two stacked bar charts sharing the x-axis.
    """
    try:
        import matplotlib.pyplot as plt
        from matplotlib.patches import Patch
    except ImportError:
        return None

    records = summary.get("analyzed_records", [])
    letters: List[str] = summary.get("letters", [])
    if species_order is None:
        species_order = summary.get("species_order")
    if not records or not letters:
        return None

    out_dir.mkdir(parents=True, exist_ok=True)
    agg = _aggregate_by_species(records, letters, species_order=species_order)
    if not agg:
        return None

    organisms = [row["organism"] for row in agg]
    org_map = {row["organism"]: row for row in agg}
    x_positions = {org: i for i, org in enumerate(organisms)}

    cmap = plt.colormaps.get_cmap("tab20")
    colors = _aa_color_map(letters, cmap)
    width = 0.8 / max(1, len(letters))

    fig, (ax_count, ax_frac) = plt.subplots(
        2,
        1,
        figsize=(max(10, len(organisms) * 0.6), 8),
        sharex=True,
    )

    for idx, aa in enumerate(letters):
        xs = [x_positions[org] + (idx - len(letters) / 2) * width + width / 2 for org in organisms]
        counts = [org_map[org]["counts"].get(aa, 0.0) for org in organisms]
        fracs = [org_map[org]["fractions"].get(aa, 0.0) for org in organisms]
        count_errs = [
            (sd if sd > 0 else float("nan")) for sd in (org_map[org]["counts_sd"].get(aa, 0.0) for org in organisms)
        ]
        ax_count.bar(
            xs,
            counts,
            width=width,
            color=colors[aa],
            label=aa,
            edgecolor="black",
            linewidth=0.4,
            yerr=count_errs,
            capsize=2,
        )
        frac_errs = [
            (sd if sd > 0 else float("nan")) for sd in (org_map[org]["fractions_sd"].get(aa, 0.0) for org in organisms)
        ]
        frac_bars = ax_frac.bar(
            xs,
            fracs,
            width=width,
            color=colors[aa],
            edgecolor="black",
            linewidth=0.4,
            yerr=frac_errs,
            capsize=2,
        )
        for bar, frac in zip(frac_bars, fracs):
            ax_frac.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + max(0.5, bar.get_height() * 0.02),
                f"{frac:.1f}%",
                ha="center",
                va="bottom",
                fontsize=7,
                color="gray",
            )

    # Length annotations above the tallest bar per organism
    for org in organisms:
        x0 = x_positions[org]
        height = max(org_map[org]["counts"].values() or [0.0])
        length = org_map[org]["length"]
        length_sd = org_map[org].get("length_sd", 0.0)
        if length_sd:
            length_label = f"L={length:.0f}\u00b1{length_sd:.0f}"
        else:
            length_label = f"L={length:.0f}"
        ax_count.text(
            x0,
            height + max(1.0, height * 0.02),
            length_label,
            ha="center",
            va="bottom",
            fontsize=7,
            color="gray",
        )

    ax_count.set_ylabel("Count")
    ax_frac.set_ylabel("Fraction of sequence (%)")
    tax_desc = ", ".join(taxonomy_terms) if taxonomy_terms else "all taxonomy"
    type_desc = ", ".join(protein_types) if protein_types else "all protein types"
    subtitle = f"Taxonomy: {tax_desc} | Types: {type_desc}"
    ax_count.set_title(f"Amino-acid composition by species (counts)\n{subtitle}")
    ax_frac.set_title(f"Amino-acid composition by species (percent)\n{subtitle}")
    ax_count.grid(axis="y", linestyle="--", alpha=0.6)
    ax_frac.grid(axis="y", linestyle="--", alpha=0.6)

    ax_frac.set_xticks(list(x_positions.values()))
    ax_frac.set_xticklabels([org.replace("_", " ").title() for org in organisms], rotation=45, ha="right", fontsize=8)
    legend_handles = [
        Patch(facecolor=colors[aa], edgecolor="black", linewidth=0.4, label=aa) for aa in letters
    ]

    # --- Dynamically reserve space on the right for the legend ---
    # Here we base the extra space on how many letters (legend entries) we have.
    # More letters → wider legend → reserve a bit more space.
    extra = min(0.35, 0.02 + 0.00005 * len(letters))  # between ~0.12 and 0.35
    right_margin = 1.0 - extra                      # part of the width used by the axes

    # Lay out the axes inside [0, 0, right_margin, 1]
    fig.tight_layout(rect=[0, 0, right_margin, 1])

    # Put the legend in the middle of the reserved right-side area
    legend_x = right_margin + extra / 2.0           # center of the right band
    fig.legend(
        handles=legend_handles,
        title="Amino acid",
        loc="center left",
        bbox_to_anchor=(legend_x, 0.5),
        fontsize=9,
    )


    letters_slug = "_".join(letters)
    out_path = out_dir / f"{letters_slug}_composition_plot.png"
    fig.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close(fig)

    if tables_dir is None:
        tables_dir = out_dir.parent / "tables" / "aa_composition"
        tables_dir.mkdir(parents=True, exist_ok=True)
    header = ["organism", "length_mean", "length_sd"]
    for aa in letters:
        header.extend([f"{aa}_count_mean", f"{aa}_count_sd", f"{aa}_fraction_mean", f"{aa}_fraction_sd"])
    rows = []
    for row in agg:
        out_row = [row["organism"], f"{row['length']:.3f}", f"{row.get('length_sd', 0.0):.3f}"]
        for aa in letters:
            out_row.append(f"{row['counts'].get(aa, 0.0):.3f}")
            out_row.append(f"{row['counts_sd'].get(aa, 0.0):.3f}")
            out_row.append(f"{row['fractions'].get(aa, 0.0):.3f}")
            out_row.append(f"{row['fractions_sd'].get(aa, 0.0):.3f}")
        rows.append(out_row)
    _write_table_files(header, rows, tables_dir / f"{letters_slug}_composition_plot")

    return out_path


def plot_total_fraction_per_species(
    summary: Dict[str, Any],
    out_dir: Path,
    taxonomy_terms: Optional[Iterable[str]] = None,
    protein_types: Optional[Iterable[str]] = None,
    species_order: Optional[Sequence[str]] = None,
    tables_dir: Optional[Path] = None,
    length_range: Optional[Tuple[int, int]] = None,
    length_threshold: Optional[int] = None,
    length_mode: str = "ge",
    longest_factor: Optional[float] = None,
) -> Optional[Path]:
    """
    Plot, for each species, the total percentage covered by the target amino acids.
    Uses a single-color bar (distinct from fixed amino-acid palette) with length labels.
    """
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        return None

    records = summary.get("analyzed_records", [])
    letters: List[str] = summary.get("letters", [])
    if species_order is None:
        species_order = summary.get("species_order")
    if not records or not letters:
        return None

    out_dir.mkdir(parents=True, exist_ok=True)
    agg = _aggregate_by_species(records, letters, species_order=species_order)
    if not agg:
        return None

    organisms = [row["organism"] for row in agg]
    totals = [row.get("total_fraction_mean", 0.0) for row in agg]
    total_errs = [(sd if sd > 0 else float("nan")) for sd in (row.get("total_fraction_sd", 0.0) for row in agg)]
    lengths = [row["length"] for row in agg]
    length_sds = [row.get("length_sd", 0.0) for row in agg]
    x_positions = range(len(organisms))

    # Single color distinct from the fixed amino-acid palette
    bar_color = "#4c72b0"

    fig, ax = plt.subplots(figsize=(max(8, len(organisms) * 0.6), 5))
    bars = ax.bar(
        x_positions,
        totals,
        color=bar_color,
        edgecolor="black",
        linewidth=0.6,
        yerr=total_errs,
        capsize=3,
    )

    # Annotate total percent and sequence length with fixed vertical spacing
    pct_offset = 1.5
    len_gap = 4.0
    for bar, total, length, length_sd in zip(bars, totals, lengths, length_sds):
        pct_y = bar.get_height() + pct_offset
        len_y = pct_y + len_gap
        if length_sd:
            length_label = f"L={length:.0f}\u00b1{length_sd:.0f}"
        else:
            length_label = f"L={length:.0f}"
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            pct_y,
            f"{total:.1f}%",
            ha="center",
            va="bottom",
            fontsize=8,
            color="black",
        )
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            len_y,
            length_label,
            ha="center",
            va="bottom",
            fontsize=7,
            color="gray",
        )

    ax.set_ylabel("Total fraction of sequence (%)")
    tax_desc = ", ".join(taxonomy_terms) if taxonomy_terms else "all taxonomy"
    type_desc = ", ".join(protein_types) if protein_types else "all protein types"
    letters_title = " ".join(letters)
    ax.set_title(f"Total percentage of {letters_title} by species\nTaxonomy: {tax_desc} | Types: {type_desc}")
    ax.set_xticks(list(x_positions))
    ax.set_xticklabels([org.replace('_', ' ').title() for org in organisms], rotation=45, ha="right", fontsize=8)
    # Ensure enough headroom for labels even on short bars
    top = max(totals) + pct_offset + len_gap + 2.0 if totals else 100
    ax.set_ylim(0, max(100, top))
    ax.grid(axis="y", linestyle="--", alpha=0.6)

    letters_slug = "_".join(letters)
    out_path = out_dir / f"{letters_slug}_total_fraction_by_species.png"
    fig.tight_layout()
    fig.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close(fig)

    if tables_dir is None:
        tables_dir = out_dir.parent / "tables" / "aa_composition"
        tables_dir.mkdir(parents=True, exist_ok=True)
    header = ["organism", "total_fraction_mean", "total_fraction_sd", "length_mean", "length_sd"]
    rows = [
        [
            row["organism"],
            f"{row.get('total_fraction_mean', 0.0):.3f}",
            f"{row.get('total_fraction_sd', 0.0):.3f}",
            f"{row.get('length', 0.0):.3f}",
            f"{row.get('length_sd', 0.0):.3f}",
        ]
        for row in agg
    ]
    _write_table_files(header, rows, tables_dir / f"{letters_slug}_total_fraction_by_species")

    return out_path


def _resolve_output_names(
    normalized_letters: Sequence[str],
    json_out: Optional[str],
    md_out: Optional[str],
) -> Tuple[str, str]:
    """
    Build default output names based on the target letters if the caller did not
    supply explicit filenames.
    """
    base = "_".join(normalized_letters) + "_composition_analysis"
    resolved_json = json_out or f"{base}.json"
    resolved_md = md_out or f"{base}.md"
    return resolved_json, resolved_md


def _plot_output_dir(
    root: Path,
    plots_dir: Optional[Path],
    taxonomy_terms: Optional[Iterable[str]],
    partial_full: Optional[str],
    protein_types: Optional[Iterable[str]],
    length_range: Optional[Tuple[int, int]],
    length_threshold: Optional[int],
    length_mode: str,
    longest_factor: Optional[float],
) -> Path:
    base = plots_dir or (root / "plots")

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

    out_dir = base / "aa_composition" / tax_part / pf_part / type_part
    for part in length_parts:
        out_dir = out_dir / part
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir


def _tables_output_dir(
    root: Path,
    tables_dir: Optional[Path],
    taxonomy_terms: Optional[Iterable[str]],
    partial_full: Optional[str],
    protein_types: Optional[Iterable[str]],
    length_range: Optional[Tuple[int, int]],
    length_threshold: Optional[int],
    length_mode: str,
    longest_factor: Optional[float],
) -> Path:
    base = tables_dir or (root / "tables")

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

    out_dir = base / "aa_composition" / tax_part / pf_part / type_part
    for part in length_parts:
        out_dir = out_dir / part
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir


def write_json(root: Path, data: Dict[str, Any], out_name: str) -> Path:
    out_path = root / out_name
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return out_path


def write_md(
    root: Path,
    summary: Dict[str, Any],
    json_path: Path,
    out_name: str,
    filter_description: Optional[str] = None,
) -> Path:
    """
    Render a markdown report describing the letter-composition analysis.

    This is similar in spirit to the SXn motif report, but focused purely on
    counts and percentages of user-specified letters.
    """
    letters = summary.get("letters", [])
    letters_str = ", ".join(letters)

    lines: List[str] = []
    lines.append("# Letter Composition Analysis")
    lines.append("")
    lines.append(
        "This report quantifies the occurrence and percentage of selected amino-acid "
        "letters in each fibroin sequence."
    )
    lines.append(f"- JSON data: `{json_path.name}`")
    lines.append(f"- Target letters: **{letters_str}**")
    if filter_description:
        lines.append(f"- Filters: {filter_description}")
    lines.append("---")

    all_records = summary.get("analyzed_records", [])
    if not all_records:
        out_path = root / out_name
        lines.append("")
        lines.append("_No records remained after filtering._")
        out_path.write_text("\n".join(lines), encoding="utf-8")
        return out_path

    # Global summary
    lines.append("## Global Summary")
    lines.append("")
    lines.append(f"- Number of sequences analyzed: **{summary.get('num_records', 0)}**")
    lines.append(f"- Total residues across all sequences: **{summary.get('total_length', 0)}**")
    lines.append("")
    lines.append("| Letter | Total Count | Global Percentage |")
    lines.append("| :---: | ---: | ---: |")
    for aa in letters:
        count = summary["global_counts"].get(aa, 0)
        frac = summary["global_fractions"].get(aa, 0.0)
        lines.append(f"| **{aa}** | {count} | {frac:.2f}% |")
    lines.append("---")

    # Per-record tables grouped by taxonomy
    species_order = summary.get("species_order") or []
    order_lookup = {name: idx for idx, name in enumerate(species_order)}
    records_sorted = sorted(
        all_records,
        key=lambda r: (
            order_lookup.get(r.get("organism", ""), float("inf")),
            r.get("suborder", "Unknown suborder"),
            r.get("superfamily", "Unknown superfamily"),
            r.get("family", "Unknown family"),
            r.get("organism", ""),
            r.get("type", ""),
            r.get("partial_full", ""),
        ),
    )

    header_cols = [
        "Organism",
        "Type",
        "Partial/Full",
        "Accession ID",
        "Length",
    ]
    # For each letter, we add columns "X Count" and "X %"
    letter_cols: List[str] = []
    for aa in letters:
        letter_cols.append(f"{aa} Count")
        letter_cols.append(f"{aa} %")

    header_line = "| " + " | ".join(header_cols + letter_cols) + " |"
    align_line = "| " + " :--- |" * len(header_cols) + " ---: |" * len(letter_cols)

    current_suborder: Optional[str] = None
    current_superfamily: Optional[str] = None
    current_family: Optional[str] = None

    for rec in records_sorted:
        suborder = rec.get("suborder", "Unknown suborder")
        superfamily = rec.get("superfamily", "Unknown superfamily")
        family = rec.get("family", "Unknown family")

        if suborder != current_suborder:
            current_suborder = suborder
            lines.append(f"\n# Suborder: {suborder}\n")
            lines.append("===")
            current_superfamily = None

        if superfamily != current_superfamily:
            current_superfamily = superfamily
            lines.append(f"\n## Superfamily: {superfamily}\n")
            lines.append("---")
            current_family = None

        if family != current_family:
            current_family = family
            lines.append(f"\n### Family: {family}")
            lines.append(header_line)
            lines.append(align_line)

        row = [
            rec.get("organism", "Unknown"),
            rec.get("type", "Unknown"),
            rec.get("partial_full", "unknown"),
            f"`{rec.get('accession', '')}`",
            str(rec.get("length", 0)),
        ]
        for aa in letters:
            counts = rec.get("letter_counts", {})
            fracs = rec.get("letter_fractions", {})
            c = counts.get(aa, 0)
            f = fracs.get(aa, 0.0)
            row.append(str(c))
            row.append(f"{f:.2f}%")
        lines.append("| " + " | ".join(row) + " |")

    out_path = root / out_name
    out_path.write_text("\n".join(lines), encoding="utf-8")
    return out_path


def analyze_and_save(
    records: Sequence[Dict[str, Any]],
    letters: Union[str, Iterable[str]],
    root: Path,
    json_out: Optional[str] = None,
    md_out: Optional[str] = None,
    filter_description: Optional[str] = None,
    plot: bool = True,
    plots_dir: Optional[Path] = None,
    tables_dir: Optional[Path] = None,
    taxonomy_terms: Optional[Iterable[str]] = None,
    partial_full: Optional[str] = None,
    protein_types: Optional[Iterable[str]] = None,
    length_range: Optional[Tuple[int, int]] = None,
    length_threshold: Optional[int] = None,
    length_mode: str = "ge",
    longest_factor: Optional[float] = None,
    longest_factor_scope: str = "species",
    phylo_tree_json: Optional[Union[str, Path]] = None,
    phylo_tree_md: Optional[Union[str, Path]] = None,
) -> Tuple[Path, Path]:
    """
    Run letter-composition analysis on a set of records and write both JSON and
    Markdown reports to the given root directory.

    If plotting is enabled, plots are written under a nested folder structure:
    <plots>/<taxonomy|all>/<partial_full|all>/<protein_types|all>/<length_filter|all>/<LETTERS>_composition_plot.png
    Species in tables/plots follow the order defined in the provided phylogenetic
    tree when available; otherwise they fall back to alphabetical ordering.
    """
    normalized_letters = normalize_letters(letters)
    resolved_json, resolved_md = _resolve_output_names(normalized_letters, json_out, md_out)

    summary = analyze_letter_composition(records, normalized_letters)
    species_order = _load_phylo_species_order(root, phylo_tree_json=phylo_tree_json, phylo_tree_md=phylo_tree_md)
    if species_order:
        summary["species_order"] = species_order
    json_path = write_json(root, summary, resolved_json)
    md_path = write_md(root, summary, json_path, resolved_md, filter_description=filter_description)
    if plot:
        plot_root = _plot_output_dir(
            root,
            plots_dir,
            taxonomy_terms=taxonomy_terms,
            partial_full=partial_full,
            protein_types=protein_types,
            length_range=length_range,
            length_threshold=length_threshold,
            length_mode=length_mode,
            longest_factor=longest_factor,
        )
        tables_root = _tables_output_dir(
            root,
            tables_dir,
            taxonomy_terms=taxonomy_terms,
            partial_full=partial_full,
            protein_types=protein_types,
            length_range=length_range,
            length_threshold=length_threshold,
            length_mode=length_mode,
            longest_factor=longest_factor,
        )
        plot_letter_composition(
            summary,
            plot_root,
            taxonomy_terms=taxonomy_terms,
            protein_types=protein_types,
            species_order=species_order if species_order else None,
            tables_dir=tables_root,
            length_range=length_range,
            length_threshold=length_threshold,
            length_mode=length_mode,
            longest_factor=longest_factor,
        )
        plot_total_fraction_per_species(
            summary,
            plot_root,
            taxonomy_terms=taxonomy_terms,
            protein_types=protein_types,
            species_order=species_order if species_order else None,
            tables_dir=tables_root,
            length_range=length_range,
            length_threshold=length_threshold,
            length_mode=length_mode,
            longest_factor=longest_factor,
        )
    return json_path, md_path


def analyze_from_root(
    root: Union[str, Path],
    letters: Union[str, Iterable[str]],
    json_out: Optional[str] = None,
    md_out: Optional[str] = None,
    plot: bool = True,
    plots_dir: Optional[Path] = None,
    tables_dir: Optional[Path] = None,
    taxonomy_terms: Optional[Iterable[str]] = None,
    protein_types: Optional[Iterable[str]] = None,
    partial_full: Optional[str] = "full",
    length_range: Optional[Tuple[int, int]] = None,
    length_threshold: Optional[int] = None,
    length_mode: str = "ge",
    longest_factor: Optional[float] = None,
    longest_factor_scope: str = "species",
    skip_tree: bool = True,
    phylo_tree_json: Optional[Union[str, Path]] = None,
    phylo_tree_md: Optional[Union[str, Path]] = None,
) -> Tuple[Path, Path]:
    """
    High-level convenience function.

    Parameters
    ----------
    root:
        Full path to the `ncbi_fibroin_sequences` folder (string or Path).
    letters:
        Letters to analyse, e.g. "SGP" or ["S", "G", "P"].
    taxonomy_terms:
        Optional list of taxonomy names (e.g. ["Annulipalpia"]).
    protein_types:
        Optional list of protein type substrings (e.g. ["heavy chain"]).
    partial_full:
        "full" (default), "partial", or None.
    length_range:
        Optional (min_len, max_len) range.
    length_threshold:
        Optional threshold for >= or <= filtering.
    length_mode:
        Either "ge" (>=, default) or "le" (<=).
    longest_factor:
        Optional factor used to exclude very short sequences relative to the
        longest one, after the other filters are applied.
    longest_factor_scope:
        "species" (default) applies longest_factor per organism; "global" applies it
        across all remaining records.
    plot:
        If True (default), write a bar-plot PNG (counts and percentages) for the
        analyzed letters. Plots are grouped by species.
    plots_dir:
        Optional path for plot outputs. Defaults to `<root>/plots` when plotting.
    phylo_tree_json / phylo_tree_md:
        Optional paths to phylogenetic tree files used to order species in plots and
        markdown output. If omitted, the function looks for `phylo_tree.json` or
        `phylo_tree.md` under `root` and falls back to alphabetical ordering.
    json_out / md_out:
        Optional output filenames. If omitted, they are generated from the
        target letters, e.g. letters "SP" -> "S_P_composition_analysis.json".

    Returns
    -------
    (json_path, md_path)
        Paths to the JSON and Markdown output files.
    """
    root = Path(root)
    if not root.exists():
        raise FileNotFoundError(f"Root directory not found: {root}")

    records = load_records_from_root(root, skip_tree=skip_tree)
    filtered_records = filter_records(
        records,
        taxonomy_terms=taxonomy_terms,
        protein_types=protein_types,
        partial_full=partial_full,
        length_range=length_range,
        length_threshold=length_threshold,
        length_mode=length_mode,
        longest_factor=longest_factor,
        longest_factor_scope=longest_factor_scope,
    )

    # Build a human-readable filter description for the markdown header
    filter_parts: List[str] = []
    if taxonomy_terms:
        filter_parts.append(f"taxonomy in {{{', '.join(taxonomy_terms)}}}")
    if protein_types:
        filter_parts.append(f"type contains {{{', '.join(protein_types)}}}")
    if partial_full:
        filter_parts.append(f"partial_full == '{partial_full}'")
    if length_range:
        filter_parts.append(f"length in [{length_range[0]}, {length_range[1]}]")
    if length_threshold is not None:
        op = ">=" if length_mode.lower() == "ge" else "<="
        filter_parts.append(f"length {op} {length_threshold}")
    if longest_factor is not None and longest_factor > 1:
        scope = longest_factor_scope or "species"
        filter_parts.append(
            f"length >= (longest_length / {longest_factor}) "
            f"[scope: {scope}] (after all other filters)"
        )
    filter_description = "; ".join(filter_parts) if filter_parts else "none"

    return analyze_and_save(
        filtered_records,
        letters=letters,
        root=root,
        json_out=json_out,
        md_out=md_out,
        filter_description=filter_description,
        plot=plot,
        plots_dir=plots_dir,
        tables_dir=tables_dir,
        taxonomy_terms=taxonomy_terms,
        partial_full=partial_full,
        protein_types=protein_types,
        length_range=length_range,
        length_threshold=length_threshold,
        length_mode=length_mode,
        longest_factor=longest_factor,
        longest_factor_scope=longest_factor_scope,
        phylo_tree_json=phylo_tree_json,
        phylo_tree_md=phylo_tree_md,
    )


if __name__ == "__main__":
    # Small CLI for convenience. Example:
    #   python letter_composition_analysis.py /full/path/to/ncbi_fibroin_sequences SGP
    import argparse

    parser = argparse.ArgumentParser(
        description="Analyze fibroin sequences for the frequency of specified letters."
    )
    parser.add_argument(
        "root",
        type=str,
        help="Full path to the 'ncbi_fibroin_sequences' folder.",
    )
    parser.add_argument(
        "letters",
        type=str,
        help="Letters to analyze (e.g. 'SGP'). Non-alphabetic characters are ignored.",
    )
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
    parser.add_argument(
        "--json-out",
        type=str,
        default=None,
        help="Optional JSON output filename. Defaults to '<LETTERS>_composition_analysis.json'.",
    )
    parser.add_argument(
        "--md-out",
        type=str,
        default=None,
        help="Optional Markdown output filename. Defaults to '<LETTERS>_composition_analysis.md'.",
    )
    parser.add_argument(
        "--no-plot",
        action="store_false",
        dest="plot",
        default=True,
        help="Disable PNG plot creation (counts and percentages). Enabled by default.",
    )
    parser.add_argument(
        "--plots-dir",
        type=str,
        default=None,
        help="Optional directory for plot outputs (default: <root>/plots).",
    )
    parser.add_argument(
        "--phylo-tree-json",
        type=str,
        default=None,
        help="Optional full path to phylo_tree.json to order species in outputs.",
    )
    parser.add_argument(
        "--phylo-tree-md",
        type=str,
        default=None,
        help="Optional path to phylo_tree.md (fallback ordering if JSON is unavailable).",
    )
    parser.add_argument(
        "--no-skip-tree",
        action="store_true",
        help="If set, do NOT skip phylo_tree.json files.",
    )

    args = parser.parse_args()

    pf = None if args.partial_full == "none" else args.partial_full

    json_path, md_path = analyze_from_root(
        root=args.root,
        letters=args.letters,
        json_out=args.json_out,
        md_out=args.md_out,
        plot=args.plot,
        plots_dir=Path(args.plots_dir) if args.plots_dir else None,
        taxonomy_terms=args.taxonomy,
        protein_types=args.protein_types,
        partial_full=pf,
        length_range=tuple(args.length_range) if args.length_range else None,
        length_threshold=args.length_threshold,
        length_mode=args.length_mode,
        longest_factor=args.longest_factor,
        longest_factor_scope=args.longest_factor_scope,
        skip_tree=not args.no_skip_tree,
        phylo_tree_json=args.phylo_tree_json,
        phylo_tree_md=args.phylo_tree_md,
    )

    print(f"JSON written to: {json_path}")
    print(f"Markdown written to: {md_path}")
    if args.plot:
        plot_root = _plot_output_dir(
            Path(args.root),
            Path(args.plots_dir) if args.plots_dir else None,
            taxonomy_terms=args.taxonomy,
            partial_full=pf,
            protein_types=args.protein_types,
            length_range=tuple(args.length_range) if args.length_range else None,
            length_threshold=args.length_threshold,
            length_mode=args.length_mode,
            longest_factor=args.longest_factor,
        )
        letters_slug = "_".join(normalize_letters(args.letters))
        plot_path = plot_root / f"{letters_slug}_composition_plot.png"
        print(f"Plot written to: {plot_path}")
