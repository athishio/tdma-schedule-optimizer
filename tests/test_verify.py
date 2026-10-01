"""
Unit tests for the independent schedule verifier.
"""

import pytest
import networkx as nx
from tdma.graph import build_connectivity_graph
from tdma.verify import verify_schedule


@pytest.fixture
def line_3_graph():
    # A(0) -- B(350) -- C(700)
    coords = {"A": (0.0, 0.0), "B": (350.0, 0.0), "C": (700.0, 0.0)}
    return build_connectivity_graph(coords, radio_range=500.0)


def test_verifier_accepts_valid_schedule(line_3_graph):
    valid_sched = {"A": 0, "B": 1, "C": 2}
    is_valid, violations = verify_schedule(line_3_graph, valid_sched)
    assert is_valid
    assert len(violations) == 0


def test_verifier_catches_distance_1_collision(line_3_graph):
    # A and B are adjacent (distance 1); giving them the same slot must fail!
    bad_sched = {"A": 0, "B": 0, "C": 1}
    is_valid, violations = verify_schedule(line_3_graph, bad_sched)
    assert not is_valid
    assert any("Distance-1 Conflict (Direct Collision)" in v for v in violations)


def test_verifier_catches_distance_2_hidden_terminal(line_3_graph):
    # A and C share neighbor B (distance 2); giving them the same slot must fail!
    bad_sched = {"A": 0, "B": 1, "C": 0}
    is_valid, violations = verify_schedule(line_3_graph, bad_sched)
    assert not is_valid
    assert any("Distance-2 Conflict (Hidden Terminal)" in v for v in violations)


def test_verifier_catches_missing_node(line_3_graph):
    # Missing C
    incomplete_sched = {"A": 0, "B": 1}
    is_valid, violations = verify_schedule(line_3_graph, incomplete_sched)
    assert not is_valid
    assert any("Coverage Violation" in v for v in violations)


def test_verifier_catches_unknown_node(line_3_graph):
    extra_sched = {"A": 0, "B": 1, "C": 2, "Unknown_Ghost": 3}
    is_valid, violations = verify_schedule(line_3_graph, extra_sched)
    assert not is_valid
    assert any("Integrity Violation" in v for v in violations)


def test_verifier_catches_non_contiguous_slots(line_3_graph):
    # Slots 0 and 2 used, but slot 1 is omitted
    non_contiguous = {"A": 0, "B": 2, "C": 3}
    is_valid, violations = verify_schedule(line_3_graph, non_contiguous)
    assert not is_valid
    assert any("Contiguity Violation" in v for v in violations)


def test_verifier_catches_negative_slots(line_3_graph):
    invalid_sched = {"A": -1, "B": 0, "C": 1}
    is_valid, violations = verify_schedule(line_3_graph, invalid_sched)
    assert not is_valid
    assert any("Format Violation" in v for v in violations)
