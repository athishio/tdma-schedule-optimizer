"""
Unit tests for TDMA graph coloring heuristics.
"""

import pytest
import networkx as nx
from tdma.graph import build_connectivity_graph, build_conflict_graph
from tdma.coloring import (
    compact_slots,
    greedy_largest_degree_first,
    dsatur_coloring,
    smallest_last_coloring,
    randomized_restarts_coloring,
    local_search_color_reduction,
)
from tdma.verify import verify_schedule


def test_compact_slots():
    uncompacted = {"A": 10, "B": 2, "C": 5, "D": 2}
    compacted = compact_slots(uncompacted)
    assert compacted["B"] == 0
    assert compacted["D"] == 0
    assert compacted["C"] == 1
    assert compacted["A"] == 2
    assert sorted(set(compacted.values())) == [0, 1, 2]


def test_line_of_3_nodes_hidden_terminal_conflict():
    """
    Line of 3 nodes: A(0, 0) -- B(350, 0) -- C(700, 0).
    A and B: distance 1.
    B and C: distance 1.
    A and C: distance 2 (hidden terminal).
    All three must have different slots (3 slots total).
    """
    coords = {"A": (0.0, 0.0), "B": (350.0, 0.0), "C": (700.0, 0.0)}
    g_conn = build_connectivity_graph(coords, radio_range=500.0)
    g_conf = build_conflict_graph(g_conn)

    for method in [
        greedy_largest_degree_first,
        dsatur_coloring,
        smallest_last_coloring,
        randomized_restarts_coloring,
        local_search_color_reduction,
    ]:
        sched = method(g_conf)
        assert len(set(sched.values())) == 3
        assert sched["A"] != sched["B"]
        assert sched["B"] != sched["C"]
        assert sched["A"] != sched["C"]

        is_valid, violations = verify_schedule(g_conn, sched)
        assert is_valid, f"Method {method.__name__} failed verification: {violations}"


def test_line_of_4_nodes_spatial_reuse():
    """
    Line of 4 nodes: A(0) -- B(350) -- C(700) -- D(1050).
    Hop distances:
    d(A, B) = 1
    d(B, C) = 1
    d(C, D) = 1
    d(A, C) = 2
    d(B, D) = 2
    d(A, D) = 3 (Spatial reuse allowed!)
    Needs exactly 3 slots, with A and D sharing a slot.
    """
    coords = {
        "A": (0.0, 0.0),
        "B": (350.0, 0.0),
        "C": (700.0, 0.0),
        "D": (1050.0, 0.0),
    }
    g_conn = build_connectivity_graph(coords, radio_range=500.0)
    g_conf = build_conflict_graph(g_conn)

    for method in [
        greedy_largest_degree_first,
        dsatur_coloring,
        smallest_last_coloring,
        randomized_restarts_coloring,
        local_search_color_reduction,
    ]:
        sched = method(g_conf)
        slots_used = len(set(sched.values()))
        assert slots_used == 3, f"{method.__name__} used {slots_used} slots instead of 3"
        assert sched["A"] == sched["D"], f"{method.__name__}: A and D should share a slot"
        assert sched["A"] != sched["B"]
        assert sched["A"] != sched["C"]
        assert sched["B"] != sched["C"]
        assert sched["B"] != sched["D"]

        is_valid, violations = verify_schedule(g_conn, sched)
        assert is_valid, f"{method.__name__} verification failed: {violations}"


def test_reproducibility_with_seed():
    """Randomized restarts and local search must be fully deterministic with fixed seed."""
    coords = {
        f"N_{i}": ((i % 4) * 300.0, (i // 4) * 300.0) for i in range(16)
    }
    g_conn = build_connectivity_graph(coords, radio_range=500.0)
    g_conf = build_conflict_graph(g_conn)

    sched1 = randomized_restarts_coloring(g_conf, num_restarts=50, seed=123)
    sched2 = randomized_restarts_coloring(g_conf, num_restarts=50, seed=123)
    assert sched1 == sched2

    ls1 = local_search_color_reduction(g_conf, initial_schedule=sched1, seed=456)
    ls2 = local_search_color_reduction(g_conf, initial_schedule=sched1, seed=456)
    assert ls1 == ls2
