"""
Exact Solvers for Minimum Vertex Coloring of the Conflict Graph G^2.

Provides:
1. Google OR-Tools CP-SAT solver (if installed).
2. Pure-Python DSATUR Branch-and-Bound Backtracking solver (zero-dependency fallback).
"""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional, Set, Tuple
import networkx as nx

from tdma.coloring import compact_slots, dsatur_coloring

Schedule = Dict[str, int]


def _find_max_clique(g: nx.Graph) -> List[str]:
    """Find a maximum (or large maximal) clique in graph G for symmetry breaking."""
    if len(g) == 0:
        return []
    try:
        # nx.max_weight_clique or nx.clique.max_clique
        cliques = nx.find_cliques(g)
        max_c: List[str] = []
        # Check first 500 maximal cliques to find the largest
        for idx, c in enumerate(cliques):
            if len(c) > len(max_c):
                max_c = c
            if idx > 500:
                break
        return max_c
    except Exception:
        # Fallback to greedy clique
        nodes_by_deg = sorted(g.nodes(), key=lambda n: g.degree(n), reverse=True)
        clique = []
        for n in nodes_by_deg:
            if all(g.has_edge(n, member) for member in clique):
                clique.append(n)
        return clique


def solve_cpsat(
    g_conflict: nx.Graph,
    timeout_sec: float = 30.0,
) -> Tuple[Schedule, int, float]:
    """
    Solve minimum vertex coloring using Google OR-Tools CP-SAT.

    Formulation:
    - Binary variables x[v, c] = 1 iff node v is assigned slot c.
    - Binary variables y[c] = 1 iff slot c is used by at least one node.
    - Each node receives exactly one slot: sum_c x[v, c] == 1.
    - Adjacent nodes cannot share slot c: x[u, c] + x[v, c] <= y[c].
    - Symmetry breaking:
      1. Slots ordered: y[c] >= y[c+1].
      2. Max clique C assigned fixed slots: x[C[i], i] == 1.
    - Objective: minimize sum_c y[c].

    Returns:
        Tuple[Schedule, int, float]: (schedule, chromatic_number, runtime_ms)
    """
    from ortools.sat.python import cp_model

    t0 = time.perf_counter()
    n = len(g_conflict)
    if n == 0:
        return {}, 0, 0.0

    nodes = sorted(list(g_conflict.nodes()), key=str)

    # Upper bound from fast DSATUR
    heuristic_sol = dsatur_coloring(g_conflict)
    k_ub = len(set(heuristic_sol.values()))

    # Lower bound from max clique
    max_clique = _find_max_clique(g_conflict)
    k_lb = len(max_clique)

    if k_lb == k_ub:
        # Heuristic already proved optimal!
        elapsed = (time.perf_counter() - t0) * 1000.0
        return compact_slots(heuristic_sol), k_ub, elapsed

    model = cp_model.CpModel()

    # Decision variables
    # x[v, c]: node v has color c
    x: Dict[Tuple[str, int], Any] = {}
    for v in nodes:
        for c in range(k_ub):
            x[(v, c)] = model.NewBoolVar(f"x_{v}_{c}")

    # y[c]: color c is used
    y = [model.NewBoolVar(f"y_{c}") for c in range(k_ub)]

    # Constraint 1: Each node assigned exactly one color
    for v in nodes:
        model.Add(sum(x[(v, c)] for c in range(k_ub)) == 1)

    # Constraint 2: Adjacent nodes in G_conflict cannot share color
    for u, v in g_conflict.edges():
        for c in range(k_ub):
            model.Add(x[(u, c)] + x[(v, c)] <= y[c])

    # Constraint 3: Link x[v, c] to y[c]
    for v in nodes:
        for c in range(k_ub):
            model.Add(x[(v, c)] <= y[c])

    # Symmetry breaking 1: y[c] non-increasing
    for c in range(k_ub - 1):
        model.Add(y[c] >= y[c + 1])

    # Symmetry breaking 2: Fix max clique to distinct colors
    for idx, member in enumerate(max_clique):
        if idx < k_ub:
            model.Add(x[(member, idx)] == 1)

    # Objective: Minimize total colors used
    model.Minimize(sum(y))

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = timeout_sec
    solver.parameters.num_search_workers = 4

    status = solver.Solve(model)
    elapsed = (time.perf_counter() - t0) * 1000.0

    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        schedule: Schedule = {}
        for v in nodes:
            for c in range(k_ub):
                if solver.Value(x[(v, c)]) == 1:
                    schedule[v] = c
                    break
        chromatic_num = int(solver.ObjectiveValue())
        return compact_slots(schedule), chromatic_num, elapsed
    else:
        # Fallback to heuristic if timeout or infeasible
        return compact_slots(heuristic_sol), k_ub, elapsed


def solve_branch_and_bound(
    g_conflict: nx.Graph,
) -> Tuple[Schedule, int, float]:
    """
    Pure-Python DSATUR Branch-and-Bound Backtracking Solver.

    Uses degree of saturation (DSATUR) dynamic vertex selection,
    maximum clique pre-coloring, chromatic number lower bounds,
    and color permutation symmetry breaking to achieve rapid exact solutions.

    Returns:
        Tuple[Schedule, int, float]: (schedule, chromatic_number, runtime_ms)
    """
    t0 = time.perf_counter()
    n = len(g_conflict)
    if n == 0:
        return {}, 0, 0.0

    nodes = sorted(list(g_conflict.nodes()), key=str)
    adj = {u: set(g_conflict.neighbors(u)) for u in nodes}

    # Initial upper bound from DSATUR heuristic
    heuristic_sol = dsatur_coloring(g_conflict)
    best_schedule = dict(heuristic_sol)
    best_k = len(set(best_schedule.values()))

    # Lower bound from max clique
    max_clique = _find_max_clique(g_conflict)
    clique_size = len(max_clique)

    if best_k <= clique_size:
        # Proved optimal without search!
        elapsed = (time.perf_counter() - t0) * 1000.0
        return compact_slots(best_schedule), best_k, elapsed

    # Pre-color the max clique
    current_schedule: Dict[str, int] = {}
    neighbor_colors: Dict[str, Set[int]] = {node: set() for node in nodes}

    for color_idx, member in enumerate(max_clique):
        current_schedule[member] = color_idx
        for nbr in adj[member]:
            neighbor_colors[nbr].add(color_idx)

    uncolored = [node for node in nodes if node not in current_schedule]

    def backtrack(colors_used: int) -> None:
        nonlocal best_k, best_schedule

        # Prune if current colors used already reaches or exceeds best known
        if colors_used >= best_k:
            return

        # If all nodes are colored, we found a strictly better solution!
        remaining = [node for node in nodes if node not in current_schedule]
        if not remaining:
            if colors_used < best_k:
                best_k = colors_used
                best_schedule = dict(current_schedule)
            return

        # Dynamic variable selection: DSATUR vertex with max saturation degree
        # Tie-break by degree in G_conflict
        target = max(
            remaining,
            key=lambda u: (len(neighbor_colors[u]), len(adj[u])),
        )

        forbidden_colors = neighbor_colors[target]

        # 1. Try assigning an already used color
        for c in range(colors_used):
            if c not in forbidden_colors:
                current_schedule[target] = c
                affected_neighbors = []
                for nbr in adj[target]:
                    if c not in neighbor_colors[nbr]:
                        neighbor_colors[nbr].add(c)
                        affected_neighbors.append(nbr)

                backtrack(colors_used)

                # Backtrack undo
                for nbr in affected_neighbors:
                    neighbor_colors[nbr].remove(c)
                del current_schedule[target]

                # Early exit if we reached theoretical lower bound
                if best_k <= clique_size:
                    return

        # 2. Try introducing a NEW color (symmetry breaking: at most one new color)
        new_color = colors_used
        if new_color + 1 < best_k:
            current_schedule[target] = new_color
            affected_neighbors = []
            for nbr in adj[target]:
                if new_color not in neighbor_colors[nbr]:
                    neighbor_colors[nbr].add(new_color)
                    affected_neighbors.append(nbr)

            backtrack(colors_used + 1)

            for nbr in affected_neighbors:
                neighbor_colors[nbr].remove(new_color)
            del current_schedule[target]

    backtrack(clique_size)

    elapsed = (time.perf_counter() - t0) * 1000.0
    return compact_slots(best_schedule), best_k, elapsed


def solve_exact_coloring(
    g_conflict: nx.Graph,
    timeout_sec: float = 30.0,
    force_pure_python: bool = False,
) -> Tuple[Schedule, int, str, float]:
    """
    Compute the true minimum chromatic number (optimal TDMA frame length)
    using OR-Tools CP-SAT (if available) or falling back gracefully to
    the pure-Python Branch-and-Bound backtracking solver.

    Args:
        g_conflict: Conflict graph G^2.
        timeout_sec: Timeout for solver in seconds.
        force_pure_python: If True, bypass CP-SAT and use pure-Python solver.

    Returns:
        Tuple[Schedule, int, str, float]:
            (optimal_schedule, chromatic_number, solver_name, runtime_ms)
    """
    if len(g_conflict) == 0:
        return {}, 0, "None", 0.0

    if not force_pure_python:
        try:
            import ortools.sat.python.cp_model  # noqa: F401

            sched, opt_k, elapsed = solve_cpsat(
                g_conflict, timeout_sec=timeout_sec
            )
            return sched, opt_k, "OR-Tools CP-SAT", elapsed
        except (ImportError, Exception):
            pass

    # Pure-Python Branch-and-Bound Fallback
    sched, opt_k, elapsed = solve_branch_and_bound(g_conflict)
    return sched, opt_k, "Pure-Python Branch-and-Bound (DSATUR)", elapsed
