"""
TDMA Graph Coloring Heuristics and Local Search Optimization.
"""

from __future__ import annotations

import random
import time
from typing import Any, Dict, List, Optional, Set, Tuple
import networkx as nx

Schedule = Dict[str, int]


def compact_slots(schedule: Schedule) -> Schedule:
    """
    Relabel color slots so that they are strictly contiguous integers: 0, 1, ..., K-1.

    Args:
        schedule: Dictionary mapping node names to integer slot assignments.

    Returns:
        Schedule: A new schedule dictionary with compacted slot indices.
    """
    if not schedule:
        return {}

    unique_slots = sorted(set(schedule.values()))
    slot_mapping = {old_slot: new_slot for new_slot, old_slot in enumerate(unique_slots)}
    return {node: slot_mapping[slot] for node, slot in schedule.items()}


def greedy_first_available_color(
    g_conflict: nx.Graph, node_order: List[str]
) -> Schedule:
    """
    Assign the smallest non-negative integer color available for each node
    in the order specified by node_order.

    Args:
        g_conflict: Conflict graph G^2.
        node_order: List of node names defining the sequential coloring order.

    Returns:
        Schedule: Dictionary mapping node names to assigned slots.
    """
    schedule: Schedule = {}

    for node in node_order:
        used_neighbor_colors: Set[int] = {
            schedule[nbr] for nbr in g_conflict.neighbors(node) if nbr in schedule
        }
        # Find smallest non-negative integer not used by any neighbor
        color = 0
        while color in used_neighbor_colors:
            color += 1
        schedule[node] = color

    return compact_slots(schedule)


def greedy_largest_degree_first(g_conflict: nx.Graph) -> Schedule:
    """
    Largest-Degree-First (LDF / Welsh-Powell) heuristic.

    Vertices are ordered in descending order of their degree in G_conflict.
    Ties are broken deterministically by node name.

    Args:
        g_conflict: Conflict graph G^2.

    Returns:
        Schedule: Conflict-free TDMA slot assignment.
    """
    if len(g_conflict) == 0:
        return {}

    # Sort descending by degree, ascending by name for deterministic tie-breaking
    sorted_nodes = sorted(
        g_conflict.nodes(),
        key=lambda n: (-g_conflict.degree(n), str(n)),
    )
    return greedy_first_available_color(g_conflict, sorted_nodes)


def dsatur_coloring(g_conflict: nx.Graph) -> Schedule:
    """
    DSATUR (Degree of Saturation) coloring algorithm.

    At each step, select an uncolored vertex with the highest saturation degree
    (number of distinct colors assigned to its colored neighbors).
    Tie-breaking:
    1. Highest degree in the uncolored subgraph.
    2. Highest overall degree in G_conflict.
    3. Lexicographical node name (deterministic).

    Args:
        g_conflict: Conflict graph G^2.

    Returns:
        Schedule: Conflict-free TDMA slot assignment.
    """
    if len(g_conflict) == 0:
        return {}

    uncolored: Set[str] = set(g_conflict.nodes())
    neighbor_colors: Dict[str, Set[int]] = {n: set() for n in uncolored}
    schedule: Schedule = {}

    # Degrees in uncolored subgraph
    uncolored_degrees: Dict[str, int] = {n: g_conflict.degree(n) for n in uncolored}
    total_degrees: Dict[str, int] = {n: g_conflict.degree(n) for n in uncolored}

    while uncolored:
        # Pick vertex with max saturation degree, then max uncolored degree,
        # then max total degree, then lexicographical name
        best_node = max(
            uncolored,
            key=lambda n: (
                len(neighbor_colors[n]),
                uncolored_degrees[n],
                total_degrees[n],
                # Invert string comparison for max by negating ordinals or using min
            ),
        )
        # For completely deterministic tie-breaking when tuples match:
        max_sat = len(neighbor_colors[best_node])
        max_uncolored_deg = uncolored_degrees[best_node]
        max_tot_deg = total_degrees[best_node]

        candidates = [
            n
            for n in uncolored
            if len(neighbor_colors[n]) == max_sat
            and uncolored_degrees[n] == max_uncolored_deg
            and total_degrees[n] == max_tot_deg
        ]
        best_node = sorted(candidates, key=str)[0]

        # Find smallest available color
        color = 0
        used = neighbor_colors[best_node]
        while color in used:
            color += 1

        schedule[best_node] = color
        uncolored.remove(best_node)

        # Update neighbors
        for nbr in g_conflict.neighbors(best_node):
            if nbr in uncolored:
                neighbor_colors[nbr].add(color)
                uncolored_degrees[nbr] -= 1

    return compact_slots(schedule)


def smallest_last_coloring(g_conflict: nx.Graph) -> Schedule:
    """
    Smallest-Last (Degeneracy / Matula & Beck) heuristic.

    Repeatedly removes the vertex with the minimum degree in the remaining
    subgraph to establish an elimination ordering, then colors vertices in
    reverse elimination order (smallest-last).

    Args:
        g_conflict: Conflict graph G^2.

    Returns:
        Schedule: Conflict-free TDMA slot assignment.
    """
    if len(g_conflict) == 0:
        return {}

    degrees = {node: g_conflict.degree(node) for node in g_conflict.nodes()}
    remaining = set(g_conflict.nodes())
    elimination_order: List[str] = []

    adj = {node: set(g_conflict.neighbors(node)) for node in g_conflict.nodes()}

    while remaining:
        # Choose node with minimum degree in remaining subgraph
        min_deg = min(degrees[n] for n in remaining)
        candidates = [n for n in remaining if degrees[n] == min_deg]
        # Deterministic tie-break by name
        chosen = sorted(candidates, key=str)[0]

        remaining.remove(chosen)
        elimination_order.append(chosen)

        for nbr in adj[chosen]:
            if nbr in remaining:
                degrees[nbr] -= 1

    # Reverse order: vertices removed last are colored first
    coloring_order = list(reversed(elimination_order))
    return greedy_first_available_color(g_conflict, coloring_order)


def randomized_restarts_coloring(
    g_conflict: nx.Graph,
    num_restarts: int = 1000,
    seed: int = 42,
) -> Schedule:
    """
    Randomized restarts greedy coloring.

    Generates multiple seeded random vertex orderings, runs greedy first-fit coloring,
    and keeps the schedule with the minimal frame length (number of slots).

    Args:
        g_conflict: Conflict graph G^2.
        num_restarts: Number of random permutations to evaluate (default 1000).
        seed: Random seed for deterministic reproducibility.

    Returns:
        Schedule: Best TDMA schedule discovered across restarts.
    """
    if len(g_conflict) == 0:
        return {}

    rng = random.Random(seed)
    nodes = sorted(list(g_conflict.nodes()), key=str)

    best_schedule: Optional[Schedule] = None
    best_slot_count = float("inf")

    # Always evaluate deterministic LDF as the initial baseline
    baseline = greedy_largest_degree_first(g_conflict)
    best_schedule = baseline
    best_slot_count = len(set(baseline.values()))

    # Run randomized restarts
    shuffled = list(nodes)
    for _ in range(num_restarts):
        rng.shuffle(shuffled)
        sched = greedy_first_available_color(g_conflict, shuffled)
        slots_used = len(set(sched.values()))
        if slots_used < best_slot_count:
            best_slot_count = slots_used
            best_schedule = sched

    assert best_schedule is not None
    return compact_slots(best_schedule)


def local_search_color_reduction(
    g_conflict: nx.Graph,
    initial_schedule: Optional[Schedule] = None,
    max_iterations: int = 2000,
    seed: int = 42,
) -> Schedule:
    """
    Local Search / Color-Reduction Pass (Kempe chains + Min-Conflicts).

    Attempts to systematically reduce the total number of colors by:
    1. Identifying the highest color class K-1.
    2. Attempting direct recoloring of nodes with color K-1 into slots 0..K-2.
    3. Attempting Kempe-chain 2-color swaps to clear slot K-1.
    4. If conflicts remain, using min-conflicts local search with a tabu tenure
       to eliminate all conflicts in a (K-1)-color target frame.
    5. Repeating iteratively as long as color reduction succeeds.

    Args:
        g_conflict: Conflict graph G^2.
        initial_schedule: Optional starting schedule; if None, DSATUR is used.
        max_iterations: Maximum search iterations per reduction attempt.
        seed: Random seed for tie-breaking and search stochasticity.

    Returns:
        Schedule: Improved (or unchanged) conflict-free schedule.
    """
    if len(g_conflict) == 0:
        return {}

    rng = random.Random(seed)

    if initial_schedule is None:
        current_schedule = dsatur_coloring(g_conflict)
    else:
        current_schedule = compact_slots(dict(initial_schedule))

    nodes = sorted(list(g_conflict.nodes()), key=str)
    adj = {u: set(g_conflict.neighbors(u)) for u in nodes}

    improved = True
    while improved:
        current_schedule = compact_slots(current_schedule)
        k = len(set(current_schedule.values()))
        if k <= 1:
            break

        target_k = k - 1
        nodes_in_last_color = [n for n in nodes if current_schedule[n] == target_k]

        # Phase 1: Try direct recoloring into an existing color 0..target_k-1
        can_directly_recolor = True
        temp_schedule = dict(current_schedule)
        for node in nodes_in_last_color:
            used_nbr_colors = {
                temp_schedule[nbr] for nbr in adj[node] if nbr != node
            }
            available = [c for c in range(target_k) if c not in used_nbr_colors]
            if available:
                temp_schedule[node] = available[0]
            else:
                can_directly_recolor = False
                break

        if can_directly_recolor:
            current_schedule = temp_schedule
            improved = True
            continue

        # Phase 2: Kempe-chain 2-color swaps
        kempe_success = False
        temp_schedule = dict(current_schedule)
        for node in nodes_in_last_color:
            if temp_schedule[node] != target_k:
                continue
            # Try to swap colors in a 2-color induced subgraph
            for c_cand in range(target_k):
                # Neighbors of node that have color c_cand
                conflicting_nbrs = [
                    nbr for nbr in adj[node] if temp_schedule[nbr] == c_cand
                ]
                # Try swapping c_cand with some other color c_alt for each conflicting neighbor
                cleared_all = True
                working_copy = dict(temp_schedule)
                for w in conflicting_nbrs:
                    swapped = False
                    for c_alt in range(target_k):
                        if c_alt == c_cand:
                            continue
                        # Find connected component of w in induced subgraph of {c_cand, c_alt}
                        component: Set[str] = set()
                        queue = [w]
                        component.add(w)
                        while queue:
                            curr = queue.pop(0)
                            for nbr in adj[curr]:
                                if nbr not in component and working_copy[nbr] in (
                                    c_cand,
                                    c_alt,
                                ):
                                    component.add(nbr)
                                    queue.append(nbr)
                        # Swap is valid if node itself is not adjacent to any other node in component that would end up with c_cand
                        # If node has no other neighbor in component with c_alt:
                        alt_neighbors_in_comp = [
                            nbr
                            for nbr in adj[node]
                            if nbr in component and working_copy[nbr] == c_alt
                        ]
                        if not alt_neighbors_in_comp:
                            for member in component:
                                working_copy[member] = (
                                    c_alt
                                    if working_copy[member] == c_cand
                                    else c_cand
                                )
                            swapped = True
                            break
                    if not swapped:
                        cleared_all = False
                        break

                if cleared_all:
                    # node can now safely take c_cand
                    working_copy[node] = c_cand
                    temp_schedule = working_copy
                    break

        if all(temp_schedule[n] < target_k for n in nodes):
            current_schedule = temp_schedule
            improved = True
            continue

        # Phase 3: Min-Conflicts Local Search with Tabu List
        # Attempt to find a valid coloring using exactly target_k colors (0..target_k-1)
        search_schedule: Dict[str, int] = {}
        for n in nodes:
            c = current_schedule[n]
            search_schedule[n] = c if c < target_k else rng.randint(0, target_k - 1)

        tabu_list: Dict[Tuple[str, int], int] = {}
        tabu_tenure = max(5, len(nodes) // 3)

        success = False
        for iteration in range(max_iterations):
            # Compute conflicts
            conflicts: List[str] = []
            for n in nodes:
                c = search_schedule[n]
                if any(search_schedule[nbr] == c for nbr in adj[n]):
                    conflicts.append(n)

            if not conflicts:
                success = True
                break

            # Pick a conflicting node (randomized with bias towards higher degree)
            node_to_move = rng.choice(conflicts)

            # Evaluate cost (number of conflicts) for each color in 0..target_k-1
            best_colors: List[int] = []
            min_nbr_conflicts = float("inf")

            for c in range(target_k):
                if c == search_schedule[node_to_move]:
                    continue
                # Tabu check: unless it eliminates all conflicts
                is_tabu = tabu_list.get((node_to_move, c), 0) > iteration
                c_conflicts = sum(1 for nbr in adj[node_to_move] if search_schedule[nbr] == c)

                if c_conflicts < min_nbr_conflicts:
                    if not is_tabu or c_conflicts == 0:
                        min_nbr_conflicts = c_conflicts
                        best_colors = [c]
                elif c_conflicts == min_nbr_conflicts:
                    if not is_tabu or c_conflicts == 0:
                        best_colors.append(c)

            if best_colors:
                chosen_color = rng.choice(best_colors)
                old_color = search_schedule[node_to_move]
                search_schedule[node_to_move] = chosen_color
                tabu_list[(node_to_move, old_color)] = iteration + tabu_tenure

        if success:
            current_schedule = search_schedule
            improved = True
        else:
            improved = False

    return compact_slots(current_schedule)


def run_all_heuristics(
    g_conflict: nx.Graph,
    seed: int = 42,
    num_restarts: int = 1000,
) -> Dict[str, Dict[str, Any]]:
    """
    Run and benchmark all TDMA coloring heuristics on G_conflict.

    Args:
        g_conflict: Conflict graph G^2.
        seed: Deterministic random seed.
        num_restarts: Restarts count for randomized search.

    Returns:
        Dict: Mapping heuristic name to result dictionary containing:
              - 'schedule': Schedule dict
              - 'slots_used': int
              - 'runtime_ms': float
    """
    results: Dict[str, Dict[str, Any]] = {}

    # 1. Largest Degree First (LDF)
    t0 = time.perf_counter()
    ldf_sched = greedy_largest_degree_first(g_conflict)
    t_ldf = (time.perf_counter() - t0) * 1000.0
    results["Greedy (Largest-Degree-First)"] = {
        "schedule": ldf_sched,
        "slots_used": len(set(ldf_sched.values())) if ldf_sched else 0,
        "runtime_ms": t_ldf,
    }

    # 2. DSATUR
    t0 = time.perf_counter()
    dsatur_sched = dsatur_coloring(g_conflict)
    t_dsatur = (time.perf_counter() - t0) * 1000.0
    results["DSATUR"] = {
        "schedule": dsatur_sched,
        "slots_used": len(set(dsatur_sched.values())) if dsatur_sched else 0,
        "runtime_ms": t_dsatur,
    }

    # 3. Smallest-Last (Degeneracy)
    t0 = time.perf_counter()
    sl_sched = smallest_last_coloring(g_conflict)
    t_sl = (time.perf_counter() - t0) * 1000.0
    results["Smallest-Last (Degeneracy)"] = {
        "schedule": sl_sched,
        "slots_used": len(set(sl_sched.values())) if sl_sched else 0,
        "runtime_ms": t_sl,
    }

    # 4. Randomized Restarts
    t0 = time.perf_counter()
    rand_sched = randomized_restarts_coloring(
        g_conflict, num_restarts=num_restarts, seed=seed
    )
    t_rand = (time.perf_counter() - t0) * 1000.0
    results[f"Randomized Restarts (N={num_restarts})"] = {
        "schedule": rand_sched,
        "slots_used": len(set(rand_sched.values())) if rand_sched else 0,
        "runtime_ms": t_rand,
    }

    # 5. Local Search / Color Reduction
    # Pass best of DSATUR or Randomized as starting point
    best_candidate = min(
        [ldf_sched, dsatur_sched, sl_sched, rand_sched],
        key=lambda s: len(set(s.values())) if s else float("inf"),
    )
    t0 = time.perf_counter()
    ls_sched = local_search_color_reduction(
        g_conflict, initial_schedule=best_candidate, seed=seed
    )
    t_ls = (time.perf_counter() - t0) * 1000.0
    results["Local Search (Color Reduction)"] = {
        "schedule": ls_sched,
        "slots_used": len(set(ls_sched.values())) if ls_sched else 0,
        "runtime_ms": t_ls,
    }

    return results
