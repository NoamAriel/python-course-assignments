import json
import math
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib import cm
from matplotlib.colors import ListedColormap
from matplotlib.patches import Patch


INPUT_JSON = "submissions.json"
NAMES_PATH = "names.txt"
OUTPUT_IMAGE = "submission_matrix.png"
OUTPUT_TIMELINE = "submission_timeline.png"


def normalize_name_key(name: str) -> str:
    cleaned = " ".join(name.replace("-", " ").split()).strip().lower()
    return cleaned or "unknown"


def load_names(submissions: dict) -> tuple[list[str], dict[str, str]]:
    canonical: dict[str, str] = {}
    for entries in submissions.values():
        for entry in entries:
            name = entry.get("submitter") or "Unknown"
            key = normalize_name_key(name)
            if key not in canonical:
                canonical[key] = name.strip() or "Unknown"

    names_path = Path(NAMES_PATH)
    if names_path.exists():
        extra = [line.strip() for line in names_path.read_text(encoding="utf-8").splitlines()]
        for name in extra:
            if name:
                key = normalize_name_key(name)
                if key not in canonical:
                    canonical[key] = name

    names = sorted(canonical.values(), key=lambda value: value.lower())
    return names, canonical


def build_status_matrix(
    submissions: dict, projects: list[str], names: list[str], canonical: dict[str, str]
) -> list[list[int]]:
    matrix = []

    for project in projects:
        entries = submissions.get(project, [])
        status_by_name: dict[str, int] = {}
        for entry in entries:
            name = entry.get("submitter") or "Unknown"
            name = canonical.get(normalize_name_key(name), name)
            on_time = entry.get("on_time")
            if on_time is True:
                status = 1
            elif on_time is False:
                status = -1
            else:
                status = 0

            if name not in status_by_name:
                status_by_name[name] = status
            else:
                if status_by_name[name] != 1 and status == 1:
                    status_by_name[name] = 1
                elif status_by_name[name] == 0 and status == -1:
                    status_by_name[name] = -1

        row = [status_by_name.get(name, 0) for name in names]
        matrix.append(row)

    return matrix


def build_time_series(
    submissions: dict, projects: list[str], names: list[str], canonical: dict[str, str]
) -> dict[str, list[float | None]]:
    series: dict[str, list[float | None]] = {}

    for name in names:
        series[name] = []
        for project in projects:
            entries = submissions.get(project, [])
            deltas = []
            for entry in entries:
                entry_name = entry.get("submitter") or "Unknown"
                entry_name = canonical.get(normalize_name_key(entry_name), entry_name)
                if entry_name != name:
                    continue
                delta_seconds = entry.get("delta_seconds")
                if isinstance(delta_seconds, int):
                    deltas.append(delta_seconds)
            if deltas:
                hours = min(deltas) / 3600.0
                series[name].append(hours)
            else:
                series[name].append(None)

    return series


def build_name_colors(names: list[str]) -> dict[str, tuple[float, float, float, float]]:
    count = max(1, len(names))
    cmap_a = cm.get_cmap("tab20", count)
    cmap_b = cm.get_cmap("gist_ncar", count)
    color_map = {}
    for index, name in enumerate(names):
        color_map[name] = cmap_a(index) if index % 2 == 0 else cmap_b(index)
    return color_map


def main() -> None:
    with open(INPUT_JSON, "r", encoding="utf-8") as handle:
        submissions = json.load(handle)

    projects = list(submissions.keys())
    include_final = input("Include Final Project Proposal? (y/n): ").strip().lower()
    if include_final not in {"y", "yes"}:
        projects = [p for p in projects if p != "Final Project Proposal"]
    names, canonical = load_names(submissions)
    name_colors = build_name_colors(names)
    matrix = build_status_matrix(submissions, projects, names, canonical)
    time_series = build_time_series(submissions, projects, names, canonical)

    fig_width = max(10, len(names) * 0.4)
    fig_height = max(6, len(projects) * 0.4)
    fig, ax = plt.subplots(figsize=(fig_width, fig_height))

    cmap = ListedColormap(["#d9534f", "#2b2b2b", "#3cb371"])
    ax.imshow(matrix, aspect="auto", cmap=cmap, vmin=-1, vmax=1)

    ax.set_xticks(range(len(names)))
    ax.set_xticklabels(names, rotation=90, ha="center", fontsize=8)
    ax.set_yticks(range(len(projects)))
    ax.set_yticklabels(projects, fontsize=9)

    ax.set_xlabel("Submitter")
    ax.set_ylabel("Project")
    ax.set_title("Submission Status by Project")

    legend_items = [
        Patch(facecolor="#3cb371", label="On Time"),
        Patch(facecolor="#d9534f", label="Late"),
        Patch(facecolor="#2b2b2b", label="No Submission/Unknown"),
    ]
    ax.legend(handles=legend_items, loc="upper left", bbox_to_anchor=(1.02, 1.0))

    fig.tight_layout()
    fig.savefig(OUTPUT_IMAGE, dpi=150, bbox_inches="tight")

    fig2_width = max(10, len(projects) * 0.6)
    fig2, axes = plt.subplots(nrows=2, ncols=1, figsize=(fig2_width, 10), sharex=True)

    x_positions = list(range(len(projects)))
    name_items = list(time_series.items())
    midpoint = (len(name_items) + 1) // 2
    split_groups = [name_items[:midpoint], name_items[midpoint:]]

    for ax, group, title_suffix in zip(axes, split_groups, ["A-M", "N-Z"]):
        for name, values in group:
            y_values = [v if v is not None else float("nan") for v in values]
            color = name_colors.get(name)
            segment_x: list[int] = []
            segment_y: list[float] = []
            for x_pos, y_val in zip(x_positions, y_values):
                if isinstance(y_val, float) and math.isnan(y_val):
                    if segment_x:
                        ax.plot(
                            segment_x,
                            segment_y,
                            marker="o",
                            linewidth=1.2,
                            alpha=0.7,
                            label=name,
                            color=color,
                        )
                        segment_x = []
                        segment_y = []
                    continue
                segment_x.append(x_pos)
                segment_y.append(y_val)
            if segment_x:
                ax.plot(
                    segment_x,
                    segment_y,
                    marker="o",
                    linewidth=1.2,
                    alpha=0.7,
                    label=name,
                    color=color,
                )

        ax.axhline(0, color="#444444", linewidth=1)
        ax.set_ylabel("Hours relative to deadline")
        ax.set_title(f"Submission Timing by Project (Hours) {title_suffix}")
        ax.legend(loc="upper left", bbox_to_anchor=(1.02, 1.0), fontsize=8, ncol=1)

    axes[-1].set_xticks(x_positions)
    axes[-1].set_xticklabels(projects, rotation=45, ha="right", fontsize=9)
    axes[-1].set_xlabel("Project")

    fig2.tight_layout()
    fig2.savefig(OUTPUT_TIMELINE, dpi=150, bbox_inches="tight")


if __name__ == "__main__":
    main()
