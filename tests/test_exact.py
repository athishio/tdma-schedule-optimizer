"""
Unit tests for exact coloring solvers (CP-SAT and Pure-Python Branch & Bound).
"""

import pytest
import networkx as nx
from tdma.graph import build_connectivity_graph, build_conflict_graph
from tdma.exact import solve_cpsat, solve_branch_and_bound, solve_exact_coloring
from tdma.verify import verify_schedule


@pytest.mark.parametrize(
    "topology, expected_opt",
    [
        ("line3", 3),
        ("line4", 3),
        ("star4", 4),
        ("cluster5", 5),
    ],
)
def test_exact_solvers_consistency(topology, expected_opt):
    """Verify CP-SAT and Pure-Python Branch & Bound produce identical optimal chromatic numbers."""
    if topology == "line3":
        coords = {"A": (0.0, 0.0), "B": (350.0, 0.0), "C": (700.0, 0.0)}
    elif topology == "line4":
        coords = {
            "A": (0.0, 0.0),
            "B": (350.0, 0.0),
            "C": (700.0, 0.0),
            "D": (1050.0, 0.0),
        }
    elif topology == "star4":
        # Star graph: Center at (0, 0), 3 leaves at (300, 0), (0, 300), (-300, 0)
        coords = {
            "Center": (0.0, 0.0),
            "Leaf1": (300.0, 0.0),
            "Leaf2": (0.0, 300.0),
            "Leaf3": (-300.0, 0.0),
        }
    elif topology == "cluster5":
        # 5 nodes within 200m pairwise: complete graph K_5
        coords = {f"N{i}": (i * 40.0, 0.0) for i in range(5)}
    else:
        raise ValueError(f"Unknown topology: {topology}")

    g_conn = build_connectivity_graph(coords, radio_range=500.0)
    g_conf = build_conflict_graph(g_conn)

    # 1. Pure-Python Branch-and-Bound
    sched_bnb, opt_bnb, _ = solve_branch_and_bound(g_conf)
    assert opt_bnb == expected_opt
    is_valid, violations = verify_schedule(g_conn, sched_bnb)
    assert is_valid, f"BnB schedule invalid: {violations}"

    # 2. CP-SAT (if ortools is installed)
    try:
        import ortools.sat.python.cp_model  # noqa: F401
        sched_cp, opt_cp, _ = solve_cpsat(g_conf)
        assert opt_cp == expected_opt
        is_valid_cp, violations_cp = verify_schedule(g_conn, sched_cp)
        assert is_valid_cp, f"CP-SAT schedule invalid: {violations_cp}"
    except ImportError:
        pass


def test_solve_exact_coloring_interface():
    coords = {"A": (0.0, 0.0), "B": (300.0, 0.0)}
    g_conn = build_connectivity_graph(coords, radio_range=500.0)
    g_conf = build_conflict_graph(g_conn)

    sched, opt_k, solver_name, rt = solve_exact_coloring(g_conf, force_pure_python=True)
    assert opt_k == 2
    assert "Branch-and-Bound" in solver_name
    assert rt >= 0.0
