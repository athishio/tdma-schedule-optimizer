"""
Unit tests for graph construction and coordinate parsing.
"""

import pytest
import networkx as nx
from tdma.graph import (
    parse_coordinates,
    euclidean_distance,
    build_connectivity_graph,
    build_conflict_graph,
)


def test_parse_valid_coordinates():
    raw = '{"Node_01": [0.0, 0.0], "Node_02": [300.0, 400.0]}'
    parsed = parse_coordinates(raw)
    assert len(parsed) == 2
    assert parsed["Node_01"] == (0.0, 0.0)
    assert parsed["Node_02"] == (300.0, 400.0)


def test_parse_dict_input():
    data = {"A": [10.5, 20.0], "B": (30.0, 40.0)}
    parsed = parse_coordinates(data)
    assert parsed["A"] == (10.5, 20.0)
    assert parsed["B"] == (30.0, 40.0)


def test_parse_duplicate_coordinates_raises_error():
    raw = '{"Node_01": [100.0, 200.0], "Node_02": [100.0, 200.0]}'
    with pytest.raises(ValueError, match="Duplicate coordinates detected"):
        parse_coordinates(raw)


def test_parse_malformed_json_raises_error():
    with pytest.raises(ValueError, match="Malformed JSON"):
        parse_coordinates('{"Node_01": [0, 0], invalid}')


def test_parse_empty_input_raises_error():
    with pytest.raises(ValueError, match="Coordinate mapping is empty"):
        parse_coordinates("{}")


def test_parse_invalid_coordinate_dimension():
    with pytest.raises(ValueError, match="must have 2D coordinates"):
        parse_coordinates('{"Node_01": [0.0]}')
    with pytest.raises(ValueError, match="must have 2D coordinates"):
        parse_coordinates('{"Node_01": [0.0, 1.0, 2.0]}')


def test_parse_non_numeric_coordinates():
    with pytest.raises(ValueError, match="must be numeric"):
        parse_coordinates('{"Node_01": ["abc", 10.0]}')


def test_parse_non_finite_coordinates():
    with pytest.raises(ValueError, match="must be finite"):
        parse_coordinates({"Node_01": [float("inf"), 0.0]})


def test_euclidean_distance():
    assert euclidean_distance((0.0, 0.0), (300.0, 400.0)) == pytest.approx(500.0)
    assert euclidean_distance((10.0, 10.0), (10.0, 10.0)) == 0.0


def test_radio_range_boundary_exactly_500m():
    """
    Test that two nodes at Euclidean distance exactly 500.0 m are connected by an edge.
    (300, 400) gives sqrt(300^2 + 400^2) = 500.0 exactly.
    """
    coords = {
        "Node_A": (0.0, 0.0),
        "Node_B": (300.0, 400.0),  # Exactly 500.0 m
        "Node_C": (300.001, 400.0),  # Slightly > 500.0 m
    }
    g = build_connectivity_graph(coords, radio_range=500.0)
    assert g.has_edge("Node_A", "Node_B")
    assert not g.has_edge("Node_A", "Node_C")


def test_isolated_node_handling():
    coords = {
        "Node_A": (0.0, 0.0),
        "Node_B": (100.0, 0.0),
        "Node_Isolated": (10000.0, 10000.0),
    }
    g = build_connectivity_graph(coords, radio_range=500.0)
    assert g.has_edge("Node_A", "Node_B")
    assert g.degree("Node_Isolated") == 0


def test_conflict_graph_square():
    """
    In a line of 3 nodes: A -- B -- C with spacing 350m:
    G has edges (A, B) and (B, C).
    G^2 must have edges (A, B), (B, C), and (A, C).
    """
    coords = {
        "A": (0.0, 0.0),
        "B": (350.0, 0.0),
        "C": (700.0, 0.0),
    }
    g_conn = build_connectivity_graph(coords, radio_range=500.0)
    assert set(g_conn.edges()) == {("A", "B"), ("B", "C")}

    g_conf = build_conflict_graph(g_conn)
    # In G^2, all pairs are adjacent (K_3)
    assert g_conf.has_edge("A", "B")
    assert g_conf.has_edge("B", "C")
    assert g_conf.has_edge("A", "C")
