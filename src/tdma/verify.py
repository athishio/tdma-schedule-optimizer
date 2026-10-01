"""
Independent Verifier for TDMA Schedules.

This module independently verifies conflict freedom without reusing
any graph coloring or conflict graph (G^2) code.
"""

from __future__ import annotations

import sys
from typing import Dict, List, Set, Tuple
import networkx as nx

Schedule = Dict[str, int]


def verify_schedule(
    g_connectivity: nx.Graph, schedule: Schedule
) -> Tuple[bool, List[str]]:
    """
    Independently verify that a TDMA schedule satisfies all protocol constraints:
    1. Node Coverage: Every node in G has exactly one slot assigned, and no extra nodes exist.
    2. Contiguity: Assigned slots must form a contiguous sequence {0, 1, ..., K-1}.
    3. Distance-1 Conflict (Direct collision):
       For every pair (u, v) with hop distance == 1 in G, slot(u) != slot(v).
    4. Distance-2 Conflict (Hidden terminal):
       For every pair (u, v) with hop distance == 2 in G, slot(u) != slot(v).
    5. Spatial Reuse:
       Nodes with hop distance >= 3 (or disconnected) are allowed to share slots.

    Args:
        g_connectivity: The physical connectivity graph G (NOT G^2).
        schedule: Dictionary mapping node names to assigned timeslots.

    Returns:
        Tuple[bool, List[str]]: (is_valid, list_of_violations)
    """
    violations: List[str] = []
    g_nodes = set(g_connectivity.nodes())
    sched_nodes = set(schedule.keys())

    # 1. Coverage Check
    missing_nodes = g_nodes - sched_nodes
    if missing_nodes:
        violations.append(
            f"Coverage Violation: {len(missing_nodes)} node(s) missing from schedule: "
            f"{sorted(list(missing_nodes))[:5]}"
        )

    extra_nodes = sched_nodes - g_nodes
    if extra_nodes:
        violations.append(
            f"Integrity Violation: {len(extra_nodes)} unknown node(s) present in schedule: "
            f"{sorted(list(extra_nodes))[:5]}"
        )

    if not schedule and len(g_nodes) > 0:
        return False, violations

    if not schedule and len(g_nodes) == 0:
        return True, []

    # 2. Contiguity Check
    slot_values = list(schedule.values())
    for node, s in schedule.items():
        if not isinstance(s, int) or s < 0:
            violations.append(
                f"Format Violation: Node '{node}' assigned invalid non-negative integer slot: {s!r}"
            )

    unique_slots = sorted(set(slot_values))
    k = len(unique_slots)
    expected_slots = list(range(k))
    if unique_slots != expected_slots:
        violations.append(
            f"Contiguity Violation: Slots are not contiguous 0..{k-1}. "
            f"Found slots: {unique_slots}"
        )

    # 3 & 4. Hop Distance Conflict Checks via Breadth-First Search on G
    # Compute all-pairs shortest paths using BFS on the raw connectivity graph G
    nodes_list = sorted(list(g_nodes), key=str)
    all_lengths: Dict[str, Dict[str, int]] = dict(
        nx.all_pairs_shortest_path_length(g_connectivity)
    )

    for i in range(len(nodes_list)):
        u = nodes_list[i]
        if u not in schedule:
            continue
        slot_u = schedule[u]
        lengths_u = all_lengths.get(u, {})

        for j in range(i + 1, len(nodes_list)):
            v = nodes_list[j]
            if v not in schedule:
                continue
            slot_v = schedule[v]

            if slot_u == slot_v:
                # Same slot: verify hop distance in G
                hop_dist = lengths_u.get(v, None)
                if hop_dist == 1:
                    # In direct radio range
                    dist_m = g_connectivity[u][v].get("distance", "unknown")
                    violations.append(
                        f"Distance-1 Conflict (Direct Collision): Adjacent nodes '{u}' and '{v}' "
                        f"(physical dist: {dist_m} m) both transmit in Slot {slot_u}."
                    )
                elif hop_dist == 2:
                    # Hidden terminal: find mutual neighbor
                    common_nbrs = sorted(
                        list(
                            set(g_connectivity.neighbors(u)).intersection(
                                g_connectivity.neighbors(v)
                            )
                        )
                    )
                    violations.append(
                        f"Distance-2 Conflict (Hidden Terminal): Nodes '{u}' and '{v}' "
                        f"share common neighbor(s) {common_nbrs} but both transmit in Slot {slot_u}."
                    )

    is_valid = len(violations) == 0
    return is_valid, violations


def check_and_report_schedule(
    g_connectivity: nx.Graph,
    schedule: Schedule,
    stream=sys.stdout,
) -> bool:
    """
    Validate schedule and print verification status.
    Prints "Schedule verified conflict-free." if valid, or lists violations.

    Args:
        g_connectivity: The physical connectivity graph G.
        schedule: Dictionary mapping node names to assigned timeslots.
        stream: Output stream (default sys.stdout).

    Returns:
        bool: True if conflict-free, False otherwise.
    """
    is_valid, violations = verify_schedule(g_connectivity, schedule)
    if is_valid:
        print("Execution finalized cleanly. Schedule verified conflict-free.", file=stream)
        return True
    else:
        print("VERIFICATION FAILURE: Schedule contains protocol violations:", file=stream)
        for v in violations:
            print(f"  [ERROR] {v}", file=stream)
        return False
