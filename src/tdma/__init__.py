"""
TDMA Schedule Planner and Optimizer
===================================
A high-performance Python package for TDMA schedule planning and optimization
in multi-hop wireless networks with spatial reuse.
"""

from tdma.graph import (
    Coordinate,
    parse_coordinates,
    build_connectivity_graph,
    build_conflict_graph,
)
from tdma.coloring import (
    greedy_largest_degree_first,
    dsatur_coloring,
    smallest_last_coloring,
    randomized_restarts_coloring,
    local_search_color_reduction,
    compact_slots,
)
from tdma.exact import solve_exact_coloring
from tdma.verify import verify_schedule

__all__ = [
    "Coordinate",
    "parse_coordinates",
    "build_connectivity_graph",
    "build_conflict_graph",
    "greedy_largest_degree_first",
    "dsatur_coloring",
    "smallest_last_coloring",
    "randomized_restarts_coloring",
    "local_search_color_reduction",
    "compact_slots",
    "solve_exact_coloring",
    "verify_schedule",
]

__version__ = "1.0.0"
