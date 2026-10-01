"""
Graph construction and coordinate handling for TDMA schedule optimizer.
"""

from __future__ import annotations

import json
import math
from typing import Any, Dict, List, Mapping, Tuple, Union
import networkx as nx

Coordinate = Tuple[float, float]
CoordinatesMap = Dict[str, Coordinate]


def parse_coordinates(raw_input: Union[str, Mapping[str, Any]]) -> CoordinatesMap:
    """
    Parse and validate node coordinate mapping.

    Args:
        raw_input: JSON string or dictionary mapping node names to [x, y] coordinates.

    Returns:
        CoordinatesMap: Dictionary mapping node names to (x, y) float tuples.

    Raises:
        ValueError: If JSON is malformed, coordinate format is invalid, node list is empty,
                    or duplicate coordinates are detected.
    """
    if isinstance(raw_input, str):
        try:
            data = json.loads(raw_input)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Malformed JSON input for coordinates: {exc}") from exc
    elif isinstance(raw_input, Mapping):
        data = raw_input
    else:
        raise ValueError(
            f"Expected JSON string or mapping for coordinates, got {type(raw_input).__name__}"
        )

    if not isinstance(data, dict):
        raise ValueError(
            f"Coordinates root must be a JSON object / dict, got {type(data).__name__}"
        )

    if len(data) == 0:
        raise ValueError("Coordinate mapping is empty; at least 1 node is required.")

    parsed: CoordinatesMap = {}
    seen_positions: Dict[Coordinate, str] = {}

    for node_name, coord in data.items():
        if not isinstance(node_name, str) or not node_name.strip():
            raise ValueError(
                f"Node name must be a non-empty string, got: {node_name!r}"
            )

        if not isinstance(coord, (list, tuple)) or len(coord) != 2:
            raise ValueError(
                f"Node '{node_name}' must have 2D coordinates [x, y], got: {coord!r}"
            )

        try:
            x = float(coord[0])
            y = float(coord[1])
        except (TypeError, ValueError) as exc:
            raise ValueError(
                f"Node '{node_name}' coordinates must be numeric, got: {coord!r}"
            ) from exc

        if not (math.isfinite(x) and math.isfinite(y)):
            raise ValueError(
                f"Node '{node_name}' coordinates must be finite real numbers, got: ({x}, {y})"
            )

        # Check for duplicate coordinates
        # Two radios placed at the exact same physical coordinates violates physical topology
        pos_key = (round(x, 6), round(y, 6))
        if pos_key in seen_positions:
            existing_node = seen_positions[pos_key]
            raise ValueError(
                f"Duplicate coordinates detected: '{node_name}' and '{existing_node}' "
                f"both occupy position ({x}, {y})."
            )
        seen_positions[pos_key] = node_name

        parsed[node_name] = (x, y)

    return parsed


def euclidean_distance(p1: Coordinate, p2: Coordinate) -> float:
    """Calculate Euclidean distance between two 2D points in meters."""
    return math.hypot(p1[0] - p2[0], p1[1] - p2[1])


def build_connectivity_graph(
    coords: CoordinatesMap, radio_range: float = 500.0
) -> nx.Graph:
    """
    Build the connectivity graph G = (V, E).

    Nodes represent radio transceivers. An undirected edge (u, v) exists if and only if
    Euclidean distance <= radio_range.

    Boundary rule:
        Points with distance exactly equal to radio_range (e.g. 500.0 m) are considered
        in-range and will be connected by an edge. A small numerical epsilon (1e-9)
        is applied to avoid floating-point round-off exclusion.

    Args:
        coords: Dictionary mapping node names to (x, y) coordinates.
        radio_range: Maximum transmission distance in meters (default 500.0 m).

    Returns:
        nx.Graph: Undirected connectivity graph with 'pos' node attributes and
                  'distance' edge attributes.
    """
    if radio_range < 0:
        raise ValueError(f"Radio range must be non-negative, got {radio_range}")

    g = nx.Graph()
    # Add nodes in sorted order for reproducibility
    for node, pos in sorted(coords.items()):
        g.add_node(node, pos=pos)

    nodes = list(g.nodes())
    eps = 1e-9

    for i in range(len(nodes)):
        u = nodes[i]
        pos_u = coords[u]
        for j in range(i + 1, len(nodes)):
            v = nodes[j]
            pos_v = coords[v]
            dist = euclidean_distance(pos_u, pos_v)
            if dist <= radio_range + eps:
                g.add_edge(u, v, distance=dist)

    return g


def build_conflict_graph(g_connectivity: nx.Graph) -> nx.Graph:
    """
    Build the conflict graph G_conflict = G^2 (the square of G).

    In TDMA broadcast scheduling on a single frequency:
    1. Distance-1 conflict (direct collision): Adjacent nodes in G are in radio range
       and cannot transmit at the same time.
    2. Distance-2 conflict (hidden terminal): Two nodes sharing a common neighbor in G
       cannot transmit at the same time, because their transmissions would collide at the
       intermediate receiver.
    3. Spatial reuse: Nodes at distance >= 3 hops may transmit simultaneously without
       causing collision at any receiver.

    Therefore, two nodes conflict if and only if their shortest path distance in G is <= 2.
    This is precisely the graph power G^2. Consequently, a distance-2 vertex coloring of G
    is mathematically identical to an ordinary vertex coloring of G^2.

    Args:
        g_connectivity: The networkx connectivity graph G.

    Returns:
        nx.Graph: Conflict graph G^2 where edges represent TDMA slot mutual exclusion.
    """
    if len(g_connectivity) == 0:
        return nx.Graph()

    # nx.power(G, 2) creates edges between all pairs of nodes with shortest-path distance <= 2
    g_conflict = nx.power(g_connectivity, 2)

    # Ensure all original node attributes (e.g. 'pos') are preserved
    for node, data in g_connectivity.nodes(data=True):
        g_conflict.nodes[node].update(data)

    return g_conflict
