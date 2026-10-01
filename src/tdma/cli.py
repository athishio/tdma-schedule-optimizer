"""
Command-Line Interface (CLI) for TDMA Schedule Optimizer.
"""

from __future__ import annotations

import argparse
import os
import sys
from typing import Any, Dict, Optional, Tuple

from tdma.graph import (
    build_conflict_graph,
    build_connectivity_graph,
    parse_coordinates,
)
from tdma.coloring import run_all_heuristics, compact_slots
from tdma.exact import solve_exact_coloring
from tdma.verify import verify_schedule
from tdma.report import (
    format_report,
    format_comparison_table,
    export_schedule_json,
    plot_topology,
)


def create_parser() -> argparse.ArgumentParser:
    """Create command line argument parser."""
    parser = argparse.ArgumentParser(
        prog="python -m tdma.cli",
        description="TDMA Schedule Planner and Spatial Reuse Optimizer in Python",
    )
    coord_group = parser.add_mutually_exclusive_group(required=True)
    coord_group.add_argument(
        "--coords",
        type=str,
        help="JSON string mapping node names to [x, y] coordinates in meters.",
    )
    coord_group.add_argument(
        "--coords-file",
        type=str,
        help="Path to JSON file containing node coordinates mapping.",
    )

    parser.add_argument(
        "--range",
        type=float,
        default=500.0,
        dest="radio_range",
        help="Radio communication range in meters (default: 500.0).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for deterministic optimization (default: 42).",
    )
    parser.add_argument(
        "--compare",
        action="store_true",
        help="Run all heuristics and exact solver, printing a detailed comparison table.",
    )
    parser.add_argument(
        "--export-json",
        type=str,
        metavar="PATH",
        help="Export schedule and metadata to specified JSON file.",
    )
    parser.add_argument(
        "--plot",
        type=str,
        metavar="PATH",
        help="Generate and save network topology plot colored by assigned TDMA slot.",
    )
    parser.add_argument(
        "--force-pure-python-exact",
        action="store_true",
        help="Force exact solver to use pure-Python Branch-and-Bound instead of OR-Tools.",
    )
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    """Main CLI entrypoint."""
    parser = create_parser()
    args = parser.parse_args(argv)

    # 1. Ingest coordinates
    raw_coords: str
    if args.coords is not None:
        raw_coords = args.coords
    else:
        if not os.path.exists(args.coords_file):
            print(
                f"[ERROR] Coordinates file not found: {args.coords_file}",
                file=sys.stderr,
            )
            return 2
        try:
            with open(args.coords_file, "r", encoding="utf-8") as f:
                raw_coords = f.read()
        except Exception as exc:
            print(
                f"[ERROR] Failed reading coordinates file '{args.coords_file}': {exc}",
                file=sys.stderr,
            )
            return 2

    try:
        coords = parse_coordinates(raw_coords)
    except ValueError as exc:
        print(f"[ERROR] Invalid coordinate input: {exc}", file=sys.stderr)
        return 2

    # 2. Build connectivity graph G and conflict graph G^2
    try:
        g_conn = build_connectivity_graph(coords, radio_range=args.radio_range)
        g_conf = build_conflict_graph(g_conn)
    except Exception as exc:
        print(f"[ERROR] Graph construction error: {exc}", file=sys.stderr)
        return 2

    # 3. Run optimization
    # Run all heuristics
    heuristic_results = run_all_heuristics(
        g_conf, seed=args.seed, num_restarts=1000
    )

    # Pick the best schedule across all heuristics
    best_heuristic_name = min(
        heuristic_results.keys(),
        key=lambda k: heuristic_results[k]["slots_used"],
    )
    final_schedule = heuristic_results[best_heuristic_name]["schedule"]
    final_k = heuristic_results[best_heuristic_name]["slots_used"]

    # 4. Exact solver
    exact_sched = None
    opt_k = None
    exact_solver_name = None
    exact_rt = None

    # Always solve exact or solve if requested / small graph
    # Prompt: "Part 1 ... since n=16 is small, also compute the true optimum to benchmark them."
    try:
        exact_sched, opt_k, exact_solver_name, exact_rt = solve_exact_coloring(
            g_conf, force_pure_python=args.force_pure_python_exact
        )
        if opt_k < final_k:
            final_schedule = exact_sched
            final_k = opt_k
    except Exception as exc:
        # If exact solver encounters issue, continue with best heuristic
        pass

    final_schedule = compact_slots(final_schedule)

    # 5. Independent verification (CRITICAL)
    is_valid, violations = verify_schedule(g_conn, final_schedule)

    # 6. Format report
    comparison_str = None
    if args.compare:
        comparison_str = format_comparison_table(
            heuristic_results,
            optimum=opt_k,
            exact_solver_name=exact_solver_name,
            exact_runtime_ms=exact_rt,
        )

    report_text = format_report(
        coords=coords,
        schedule=final_schedule,
        radio_range=args.radio_range,
        verified=is_valid,
        comparison_table=comparison_str,
    )
    print(report_text)

    # 7. Exports & Plots
    if args.export_json:
        try:
            export_schedule_json(
                args.export_json,
                coords=coords,
                schedule=final_schedule,
                radio_range=args.radio_range,
                optimum=opt_k,
            )
            print(f"[INFO] Schedule exported successfully to: {args.export_json}")
        except Exception as exc:
            print(f"[WARNING] Failed to export JSON: {exc}", file=sys.stderr)

    if args.plot:
        try:
            plot_topology(
                g_conn,
                schedule=final_schedule,
                output_path=args.plot,
                radio_range=args.radio_range,
            )
            print(f"[INFO] Topology plot saved successfully to: {args.plot}")
        except Exception as exc:
            print(f"[WARNING] Failed to generate plot: {exc}", file=sys.stderr)

    # 8. Check verification exit code
    if not is_valid:
        print("\nSchedule verification failed with the following violations:", file=sys.stderr)
        for v in violations:
            print(f"  - {v}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
