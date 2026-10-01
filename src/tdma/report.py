"""
Formatting, visualization, and export utilities for TDMA schedules.
"""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional
import networkx as nx

Schedule = Dict[str, int]


def natural_sort_key(s: str) -> List[Any]:
    """Sort strings with embedded numbers naturally (e.g. Node_2 before Node_10)."""
    return [int(text) if text.isdigit() else text.lower() for text in re.split(r"(\d+)", s)]


def short_node_label(node_name: str) -> str:
    """Generate a clean 2-4 character column label for the matrix header."""
    # If node ends in digits (e.g. Node_01 or N16), extract the digits
    match = re.search(r"(\d+)$", node_name)
    if match:
        num_str = match.group(1)
        if len(num_str) == 1:
            return f"{int(num_str):02d}"
        return num_str
    # Otherwise return first 4 chars
    return node_name[:4]


def format_report(
    coords: Dict[str, Any],
    schedule: Schedule,
    radio_range: float,
    verified: bool,
    comparison_table: Optional[str] = None,
) -> str:
    """
    Format the complete TDMA Topology Optimization Report matching specification.

    Args:
        coords: Coordinates mapping.
        schedule: Final chosen schedule mapping node -> slot.
        radio_range: Configured transmission range in meters.
        verified: True if verified conflict-free.
        comparison_table: Optional ASCII table comparing heuristics.

    Returns:
        str: Formatted report.
    """
    lines: List[str] = []
    lines.append("================================================================")
    lines.append(" TDMA TOPOLOGY OPTIMIZATION REPORT")
    lines.append("================================================================")
    num_nodes = len(schedule)
    k = len(set(schedule.values())) if schedule else 0

    lines.append(f"Total Nodes Processed : {num_nodes}")
    lines.append(f"Configured Radio Range : {radio_range:.1f} meters")
    lines.append(f"Optimized Frame Length : {k} unique timeslots (Lower is better)")
    lines.append("-----------------------------------------------------------------")

    # Optional Heuristic Comparison Section
    if comparison_table:
        lines.append(comparison_table)
        lines.append("-----------------------------------------------------------------")

    lines.append("NODE -> SLOT ASSIGNMENTS:")
    sorted_nodes = sorted(schedule.keys(), key=natural_sort_key)
    for node in sorted_nodes:
        lines.append(f" {node}: Slot {schedule[node]}")

    lines.append("")
    lines.append("STRUCTURAL TDMA SCHEDULE MATRIX (Slot x Node Boolean Matrix):")

    # Matrix column header
    stripped_labels = [short_node_label(node) for node in sorted_nodes]
    if len(set(stripped_labels)) == len(sorted_nodes):
        col_labels = stripped_labels
    else:
        # If stripped labels are not unique (e.g. ClusterA_01 and ClusterB_01 both strip to '01'),
        # print full node names so every column header is unique.
        col_labels = list(sorted_nodes)

    header = "Slot \\ Node | " + " | ".join(col_labels)
    lines.append(header)
    divider_len = max(len(header) + 4, 75)
    lines.append("-" * divider_len)

    # Matrix rows
    for slot_idx in range(k):
        row_bits = ["1" if schedule[node] == slot_idx else "0" for node in sorted_nodes]
        row_str = f"Slot {slot_idx:02d}    | " + " | ".join(
            f"{bit:^{len(lbl)}}" if len(lbl) > 2 else f"{bit:>{len(lbl)}}"
            for bit, lbl in zip(row_bits, col_labels)
        )
        lines.append(row_str)

    lines.append("-" * divider_len)
    if verified:
        lines.append("Execution finalized cleanly. Schedule verified conflict-free.")
    else:
        lines.append("VERIFICATION FAILED: Violations detected in schedule!")
    lines.append("================================================================")

    return "\n".join(lines)


def format_comparison_table(
    heuristic_results: Dict[str, Dict[str, Any]],
    optimum: Optional[int] = None,
    exact_solver_name: Optional[str] = None,
    exact_runtime_ms: Optional[float] = None,
) -> str:
    """
    Format a comparison table of heuristics vs exact solver.

    Args:
        heuristic_results: Dict from run_all_heuristics.
        optimum: Exact chromatic number (if computed).
        exact_solver_name: Name of exact solver used.
        exact_runtime_ms: Exact solver execution time in ms.

    Returns:
        str: ASCII comparison table.
    """
    lines: List[str] = []
    lines.append("HEURISTIC BENCHMARK & OPTIMALITY ANALYSIS:")
    header = f"{'Method':<36} | {'Slots':<6} | {'Runtime (ms)':<13} | {'Optimum':<8} | {'Gap':<5}"
    lines.append(header)
    lines.append("-" * len(header))

    opt_str = str(optimum) if optimum is not None else "N/A"

    for name, data in heuristic_results.items():
        slots = data["slots_used"]
        rt = data["runtime_ms"]
        if optimum is not None:
            gap = f"+{slots - optimum}" if slots > optimum else "0 (Opt)"
        else:
            gap = "N/A"
        lines.append(f"{name:<36} | {slots:<6} | {rt:<13.3f} | {opt_str:<8} | {gap:<5}")

    footnote = None
    if optimum is not None and exact_solver_name:
        lines.append("-" * len(header))
        # Shorten fallback solver label to "Exact (Python B&B)" to maintain column alignment
        if "Branch-and-Bound" in exact_solver_name or "Python" in exact_solver_name:
            exact_label = "Exact (Python B&B)"
            footnote = f"* Exact (Python B&B): {exact_solver_name}"
        else:
            exact_label = f"Exact ({exact_solver_name})"
        rt_str = f"{exact_runtime_ms:.3f}" if exact_runtime_ms is not None else "N/A"
        lines.append(f"{exact_label:<36} | {optimum:<6} | {rt_str:<13} | {opt_str:<8} | 0 (Opt)")

    if footnote:
        lines.append(footnote)

    return "\n".join(lines)


def export_schedule_json(
    filepath: str,
    coords: Dict[str, Any],
    schedule: Schedule,
    radio_range: float,
    optimum: Optional[int] = None,
) -> None:
    """
    Export the schedule and topology to a structured JSON file.
    """
    sorted_nodes = sorted(schedule.keys(), key=natural_sort_key)
    k = len(set(schedule.values())) if schedule else 0

    matrix: Dict[str, Dict[str, int]] = {}
    for slot_idx in range(k):
        slot_key = f"Slot_{slot_idx:02d}"
        matrix[slot_key] = {
            node: (1 if schedule[node] == slot_idx else 0) for node in sorted_nodes
        }

    data = {
        "metadata": {
            "total_nodes": len(schedule),
            "radio_range_meters": radio_range,
            "frame_length_slots": k,
            "optimal_frame_length": optimum,
            "is_optimal": (k == optimum if optimum is not None else None),
        },
        "coordinates": coords,
        "schedule": {node: schedule[node] for node in sorted_nodes},
        "schedule_matrix": matrix,
    }

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def plot_topology(
    g_connectivity: nx.Graph,
    schedule: Schedule,
    output_path: str,
    radio_range: float = 500.0,
) -> None:
    """
    Plot the radio topology, connectivity edges, and slot assignments
    using matplotlib (if installed).
    """
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        return

    fig, ax = plt.subplots(figsize=(10, 8))

    pos = nx.get_node_attributes(g_connectivity, "pos")
    if not pos:
        # Fallback layout if no pos
        pos = nx.spring_layout(g_connectivity, seed=42)

    k = max(set(schedule.values())) + 1 if schedule else 1
    # Colormap
    cmap = plt.get_cmap("tab20" if k > 10 else "tab10")

    # Draw connectivity edges
    nx.draw_networkx_edges(
        g_connectivity,
        pos,
        ax=ax,
        edge_color="#B0BEC5",
        style="solid",
        width=1.5,
        alpha=0.8,
    )

    # Draw nodes colored by assigned slot
    sorted_nodes = sorted(g_connectivity.nodes(), key=natural_sort_key)
    node_colors = [cmap(schedule.get(n, 0) % 20) for n in sorted_nodes]

    nx.draw_networkx_nodes(
        g_connectivity,
        pos,
        nodelist=sorted_nodes,
        ax=ax,
        node_color=node_colors,
        node_size=600,
        edgecolors="#263238",
        linewidths=1.5,
    )

    # Node labels
    labels = {n: f"{short_node_label(n)}\n(S{schedule.get(n, 0)})" for n in sorted_nodes}
    nx.draw_networkx_labels(
        g_connectivity,
        pos,
        labels=labels,
        ax=ax,
        font_size=8,
        font_weight="bold",
        font_color="#212121",
    )

    ax.set_title(
        f"TDMA Topology & Spatial Slot Allocation (Range: {radio_range:.1f} m, Frame: {k} slots)",
        fontsize=13,
        fontweight="bold",
        pad=15,
    )
    ax.set_xlabel("X Coordinate (meters)", fontsize=10)
    ax.set_ylabel("Y Coordinate (meters)", fontsize=10)
    ax.grid(True, linestyle="--", alpha=0.4)

    plt.tight_layout()
    plt.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
