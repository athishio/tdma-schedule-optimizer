"""
Property-based and randomized topology tests.
"""

import random
import pytest
import networkx as nx
from tdma.graph import build_connectivity_graph, build_conflict_graph
from tdma.coloring import (
    greedy_largest_degree_first,
    dsatur_coloring,
    smallest_last_coloring,
    randomized_restarts_coloring,
    local_search_color_reduction,
)
from tdma.exact import solve_branch_and_bound
from tdma.verify import verify_schedule


@pytest.mark.parametrize("test_seed", [101, 202, 303, 404, 505])
def test_random_topology_heuristics_soundness_and_optimality_bound(test_seed):
    """
    Generate random 2D topologies:
    - Verify every heuristic schedule passes independent conflict verification.
    - Verify heuristic slot count >= exact optimum (lower bound invariant).
    """
    rng = random.Random(test_seed)
    num_nodes = rng.randint(6, 12)
    area_width = 1200.0

    coords = {}
    for i in range(num_nodes):
        x = rng.uniform(0.0, area_width)
        y = rng.uniform(0.0, area_width)
        coords[f"Node_{i:02d}"] = (round(x, 2), round(y, 2))

    g_conn = build_connectivity_graph(coords, radio_range=500.0)
    g_conf = build_conflict_graph(g_conn)

    # Compute exact optimum
    _, opt_k, _ = solve_branch_and_bound(g_conf)

    heuristics = [
        ("LDF", greedy_largest_degree_first(g_conf)),
        ("DSATUR", dsatur_coloring(g_conf)),
        ("Smallest-Last", smallest_last_coloring(g_conf)),
        ("Random-Restarts", randomized_restarts_coloring(g_conf, num_restarts=50, seed=test_seed)),
        ("Local-Search", local_search_color_reduction(g_conf, seed=test_seed, max_iterations=500)),
    ]

    for name, sched in heuristics:
        # Invariant 1: Valid and conflict-free
        is_valid, violations = verify_schedule(g_conn, sched)
        assert is_valid, f"Seed {test_seed}: {name} produced violations: {violations}"

        # Invariant 2: Slots must be contiguous 0..K-1
        k_used = len(set(sched.values())) if sched else 0
        assert sorted(set(sched.values())) == list(range(k_used))

        # Invariant 3: Heuristic frame length cannot be strictly less than exact optimum
        assert k_used >= opt_k, (
            f"Seed {test_seed}: {name} used {k_used} slots which is less than exact optimum {opt_k}!"
        )


def test_single_node_topology():
    """Edge case: 1 node."""
    coords = {"Solo_Node": (100.0, 100.0)}
    g_conn = build_connectivity_graph(coords, radio_range=500.0)
    g_conf = build_conflict_graph(g_conn)

    sched = dsatur_coloring(g_conf)
    assert sched == {"Solo_Node": 0}
    is_valid, violations = verify_schedule(g_conn, sched)
    assert is_valid


def test_all_nodes_isolated():
    """Edge case: All nodes far apart (> 1000m). Frame length should be 1."""
    coords = {
        f"Node_{i}": (i * 2000.0, 0.0) for i in range(8)
    }
    g_conn = build_connectivity_graph(coords, radio_range=500.0)
    g_conf = build_conflict_graph(g_conn)

    sched = dsatur_coloring(g_conf)
    assert len(set(sched.values())) == 1
    is_valid, violations = verify_schedule(g_conn, sched)
    assert is_valid
