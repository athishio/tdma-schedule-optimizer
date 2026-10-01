# TDMA Schedule Planner and Spatial Reuse Optimizer

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://img.shields.io/badge/tests-47%20passed-brightgreen.svg)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A high-performance Python package and CLI for deterministic **TDMA (Time Division Multiple Access) Schedule Planning and Optimization** in multi-hop wireless networks. Built for wireless protocol development, featuring 5 distinct graph coloring heuristics, 2 exact solvers (Google OR-Tools CP-SAT and a pure-Python Branch-and-Bound fallback), an independent zero-trust schedule verifier, and an EMANE (Extendable Mobile Ad-hoc Network Emulator) translation bridge.

---

## Table of Contents
- [1. Problem Overview & Wireless Mechanics](#1-problem-overview--wireless-mechanics)
- [2. Mathematical Modeling: Graph Square Equivalence](#2-mathematical-modeling-graph-square-equivalence)
- [3. Optimization Algorithms](#3-optimization-algorithms)
- [4. Project Structure](#4-project-structure)
- [5. Installation & Setup](#5-installation--setup)
- [6. CLI Usage & Examples](#6-cli-usage--examples)
- [7. Benchmark Results](#7-benchmark-results)
- [8. Independent Verification Engine](#8-independent-verification-engine)
- [9. Part 2: EMANE Emulation Bridge](#9-part-2-emane-emulation-bridge)
- [10. Documentation Artifacts](#10-documentation-artifacts)
- [11. Author](#11-author)

---

## 1. Problem Overview & Wireless Mechanics

In single-frequency wireless networks, radio transceivers share an RF channel. To avoid destructive RF interference, TDMA partitions time into periodic **frames**, subdivided into equal-duration **timeslots** ($T_{slot} = 1.0\text{ ms}$). Radios transmit only during their assigned slot(s).

### Collision Constraints & Spatial Reuse
Nodes are situated at static 2D coordinates $(x, y)$ in meters with communication range $R = 500.0\text{ m}$ (points at exactly 500.0 m are in-range).

```
   (A) -------- 350 m -------- (B) -------- 350 m -------- (C) -------- 350 m -------- (D)
 [Slot 1]                   [Slot 2]                   [Slot 0]                   [Slot 1]
    |<--- Dist-1 Collision --->|                          |                          |
    |<--------------- Dist-2 Hidden Terminal ------------>|                          |
    |<--------------------------- Distance-3 Spatial Reuse (Allowed) --------------->|
```

1. **Distance-1 Conflict (Direct Collision):** Adjacent nodes in radio range ($d \le 500.0\text{ m}$) must never transmit simultaneously.
2. **Distance-2 Conflict (Hidden Terminal):** Two nodes that share a common intermediate neighbor must never transmit simultaneously (their transmissions collide at the intermediate receiver).
3. **Spatial Reuse (Distance $\ge 3$ Hops):** Nodes $\ge 3$ hops apart (or in disconnected components) **may safely reuse the same slot**.

**Optimization Goal:** Minimize the frame length (number of unique slots $K$) to maximize network throughput and minimize packet latency.

---

## 2. Mathematical Modeling: Graph Square Equivalence

1. **Physical Connectivity Graph $G = (V, E)$:**
   Nodes represent radios. Edge $(u, v) \in E \iff \text{Euclidean distance } d(u, v) \le 500.0\text{ m}$.
2. **Conflict Graph $G_{conflict} = G^2$ (The Graph Square):**
   Computed via `nx.power(G, 2)`. An edge exists between $u$ and $v$ in $G^2 \iff 1 \le \text{dist}_G(u, v) \le 2$.
3. **Equivalence Theorem:**
   A distance-2 vertex coloring of $G$ is **mathematically isomorphic** to an ordinary vertex coloring of $G^2$.
4. **Theoretical Bounds:**
   $$\omega(G^2) \le \chi(G^2) \le \Delta(G^2) + 1$$
   Where $\omega(G^2)$ is the maximum clique size and $\Delta(G^2)$ is the maximum degree in the conflict graph.

---

## 3. Optimization Algorithms

The package provides 5 heuristics and 2 exact solvers:

- **1. Largest-Degree-First (LDF / Welsh-Powell):** Colors high-degree conflict bottlenecks first; $\mathcal{O}(V \log V + E)$.
- **2. DSATUR (Degree of Saturation):** Dynamic heuristic selecting vertex with maximal colored neighbor saturation; $\mathcal{O}(V^2 + E)$.
- **3. Smallest-Last (Degeneracy / Matula-Beck):** Successive minimum-degree elimination ordering bounding colors by subgraph degeneracy; $\mathcal{O}(V + E)$.
- **4. Randomized Restarts:** Evaluates $N=1000$ seeded random permutations to escape local minima deterministically.
- **5. Local Search & Color Reduction:** Kempe-chain 2-color component swaps and min-conflicts Tabu search to eliminate highest color classes.
- **6. Exact Solver (OR-Tools CP-SAT):** 0-1 ILP constraint programming model with maximum clique pre-coloring symmetry breaking.
- **7. Exact Solver (Pure-Python Branch-and-Bound Fallback):** Zero-dependency DSATUR-guided branch-and-bound backtracking solver. Solves 16-node topologies in $< 0.5\text{ ms}$.

---

## 4. Project Structure

```
tdma-schedule-optimizer/
├── README.md                      # Comprehensive user & developer guide
├── requirements.txt               # Project dependencies
├── pyproject.toml                 # Package configuration
├── src/
│   └── tdma/
│       ├── __init__.py            # Package exports
│       ├── graph.py               # Coordinate parsing, G and G^2 construction
│       ├── coloring.py            # 5 coloring heuristics & local search
│       ├── exact.py               # CP-SAT & Pure-Python BnB exact solvers
│       ├── verify.py              # Zero-trust independent BFS verifier
│       ├── report.py              # ASCII report, matrix, JSON export, plots
│       └── cli.py                 # Argument parsing and orchestration
├── examples/
│   ├── grid_4x4_300m.json         # 4x4 lattice topology (16 nodes, 300m)
│   ├── sparse_linear_16.json      # Linear chain topology (16 nodes, 350m)
│   ├── dense_cluster_16.json      # Dense clique topology (16 nodes, K_16)
│   ├── disconnected_clusters_16.json # Two 8-node clusters (3000m separation)
│   └── grid_schedule.json         # Pre-computed 9-slot schedule JSON for grid (EMANE input)
├── tests/
│   ├── test_graph.py              # Graph construction & 500m boundary tests
│   ├── test_coloring.py           # Heuristics, spatial reuse, & determinism
│   ├── test_exact.py              # CP-SAT vs BnB solver consistency
│   ├── test_verify.py             # Verifier catches deliberate collisions
│   ├── test_properties.py         # Property tests on randomized topologies
│   └── test_cli.py                # End-to-end CLI & error handling
├── emane/                         # Part 2: EMANE Emulation Bridge
│   ├── Dockerfile                 # Consolidated Ubuntu 22.04 container
│   ├── README.md                  # Emulation test plan & documentation
│   ├── config/                    # EMANE TDMA MAC, PHY, and NEM XML profiles
│   └── bridge/
│       ├── schedule_to_emane.py   # Schedule JSON to EMANE XML translator
│       ├── publish_schedule.py    # Standalone EventService schedule publisher
│       └── test_emane_bridge.py   # Round-trip schema parity tests
└── docs/
    ├── DESIGN.md                  # Detailed engineering design document
    ├── design.pdf                 # Formatted PDF design document
    ├── PRESENTATION_OUTLINE.md    # 10-slide interview presentation outline
    ├── presentation.pptx          # PowerPoint slide deck
    └── WALKTHROUGH.md             # Codebase walkthrough & interview Q&A guide
```

---

## 5. Installation & Setup

### Prerequisites
- Python 3.10 or higher
- Git

### Quick Install
```bash
# Clone the repository
git clone https://github.com/example/tdma-schedule-optimizer.git
cd tdma-schedule-optimizer

# Install dependencies and editable package
pip install -r requirements.txt
pip install -e .
```

---

## 6. CLI Usage & Examples

### Running the Optimizer
The CLI accepts coordinates via an inline JSON string or a JSON file.

#### Example 1: 4x4 Grid Topology (File Input with Benchmark Comparison)
```bash
python -m tdma.cli --coords-file examples/grid_4x4_300m.json --compare
```

#### Output:
```text
================================================================
 TDMA TOPOLOGY OPTIMIZATION REPORT
================================================================
Total Nodes Processed : 16
Configured Radio Range : 500.0 meters
Optimized Frame Length : 9 unique timeslots (Lower is better)
-----------------------------------------------------------------
HEURISTIC BENCHMARK & OPTIMALITY ANALYSIS:
Method                               | Slots  | Runtime (ms)  | Optimum  | Gap  
--------------------------------------------------------------------------------
Greedy (Largest-Degree-First)        | 9      | 0.044         | 9        | 0 (Opt)
DSATUR                               | 9      | 0.091         | 9        | 0 (Opt)
Smallest-Last (Degeneracy)           | 9      | 0.080         | 9        | 0 (Opt)
Randomized Restarts (N=1000)         | 9      | 18.266        | 9        | 0 (Opt)
Local Search (Color Reduction)       | 9      | 38.875        | 9        | 0 (Opt)
--------------------------------------------------------------------------------
Exact (OR-Tools CP-SAT)              | 9      | 0.423         | 9        | 0 (Opt)
-----------------------------------------------------------------
NODE -> SLOT ASSIGNMENTS:
 Node_01: Slot 8
 Node_02: Slot 4
 Node_03: Slot 5
 Node_04: Slot 8
 Node_05: Slot 6
 Node_06: Slot 0
 Node_07: Slot 1
 Node_08: Slot 6
 Node_09: Slot 7
 Node_10: Slot 2
 Node_11: Slot 3
 Node_12: Slot 7
 Node_13: Slot 8
 Node_14: Slot 4
 Node_15: Slot 5
 Node_16: Slot 8

STRUCTURAL TDMA SCHEDULE MATRIX (Slot x Node Boolean Matrix):
Slot \ Node | 01 | 02 | 03 | 04 | 05 | 06 | 07 | 08 | 09 | 10 | 11 | 12 | 13 | 14 | 15 | 16
-----------------------------------------------------------------------------------------------
Slot 00    |  0 |  0 |  0 |  0 |  0 |  1 |  0 |  0 |  0 |  0 |  0 |  0 |  0 |  0 |  0 |  0
Slot 01    |  0 |  0 |  0 |  0 |  0 |  0 |  1 |  0 |  0 |  0 |  0 |  0 |  0 |  0 |  0 |  0
Slot 02    |  0 |  0 |  0 |  0 |  0 |  0 |  0 |  0 |  0 |  1 |  0 |  0 |  0 |  0 |  0 |  0
Slot 03    |  0 |  0 |  0 |  0 |  0 |  0 |  0 |  0 |  0 |  0 |  1 |  0 |  0 |  0 |  0 |  0
Slot 04    |  0 |  1 |  0 |  0 |  0 |  0 |  0 |  0 |  0 |  0 |  0 |  0 |  0 |  1 |  0 |  0
Slot 05    |  0 |  0 |  1 |  0 |  0 |  0 |  0 |  0 |  0 |  0 |  0 |  0 |  0 |  0 |  1 |  0
Slot 06    |  0 |  0 |  0 |  0 |  1 |  0 |  0 |  1 |  0 |  0 |  0 |  0 |  0 |  0 |  0 |  0
Slot 07    |  0 |  0 |  0 |  0 |  0 |  0 |  0 |  0 |  1 |  0 |  0 |  1 |  0 |  0 |  0 |  0
Slot 08    |  1 |  0 |  0 |  1 |  0 |  0 |  0 |  0 |  0 |  0 |  0 |  0 |  1 |  0 |  0 |  1
-----------------------------------------------------------------------------------------------
Execution finalized cleanly. Schedule verified conflict-free.
================================================================
```

#### Example 2: Inline Coordinates with JSON Export & Topology Plot
```bash
python -m tdma.cli \
  --coords '{"N1":[0,0],"N2":[300,0],"N3":[600,0],"N4":[900,0]}' \
  --export-json schedule.json \
  --plot topology.png
```

---

## 7. Benchmark Results

Real results measured by executing the benchmark suite across diverse topology structures:

| Scenario | $|V|$ | $G$ Edges | $G^2$ Edges | Max Deg $\Delta(G^2)$ | Exact Optimum | Best Heuristic | Optimality Gap | Runtime |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **4x4 Grid (300 m)** | 16 | 42 | 90 | 15 | **9 slots** | **9 slots** | **0 (Optimal)** | 0.48 ms |
| **Sparse Linear (350 m)**| 16 | 15 | 29 | 4 | **3 slots** | **3 slots** | **0 (Optimal)** | 0.17 ms |
| **Dense Cluster ($d \le 500$ m)**| 16 | 120 | 120 | 15 | **16 slots** | **16 slots** | **0 (Optimal)** | 0.22 ms |
| **Two Disconnected Clusters** | 16 | 56 | 56 | 7 | **8 slots** | **8 slots** | **0 (Optimal)** | 0.30 ms |

---

## 8. Independent Verification Engine

The verification engine (`src/tdma/verify.py`) operates with zero trust:
- **No Shared Code:** Does not import graph coloring, conflict graph, or $G^2$ functions.
- **BFS Shortest Paths on $G$:** Computes all-pairs shortest paths directly on the raw physical graph $G$.
- **Distance-1 Collisions:** Flags any two nodes with $\text{dist}_G(u, v) = 1$ sharing a slot.
- **Distance-2 Hidden Terminals:** Flags any two nodes with $\text{dist}_G(u, v) = 2$ sharing a slot, naming the mutual intermediate receiver.
- **Contiguity & Coverage:** Validates that all nodes are assigned and slot numbers form the contiguous set $\{0, 1, \dots, K-1\}$.

### Running the Test Suite
```bash
pytest -v
```
All **47 unit, property, and integration tests** pass with 100% coverage.

---

## 9. Part 2: EMANE Emulation Bridge

The bridge converts optimized schedules into native EMANE configuration files:

- **Schedule Artifact (`examples/grid_schedule.json`):** The repository provides `examples/grid_schedule.json`, containing the pre-computed, verified 9-slot schedule JSON for the 4x4 grid topology. The EMANE bridge accepts this artifact directly to produce valid XML configurations without re-running the solver.

```bash
# Step 1: Optimize and export schedule (or use pre-generated examples/grid_schedule.json)
python -m tdma.cli --coords-file examples/grid_4x4_300m.json --export-json examples/grid_schedule.json

# Step 2: Convert to EMANE XML & Python Event Script
python emane/bridge/schedule_to_emane.py \
  --input examples/grid_schedule.json \
  --output emane/config/schedule.xml \
  --event-script emane/bridge/publish_schedule.py \
  --slot-duration-us 1000
```

- **Docker Emulation Environment:** `emane/Dockerfile` builds an Ubuntu 22.04 container with EMANE, Python event bindings, and network benchmarking tools (`iperf3`, `tcpdump`, `ping`).
- **Test Plan:** See [`emane/README.md`](emane/README.md) for ICMP slot alignment verification and UDP interference demonstration.

---

## 10. Documentation Artifacts

- **[DESIGN.md](docs/DESIGN.md):** In-depth engineering design document covering protocol theory, mathematical proofs, algorithm complexities, empirical results, and edge-case handling.
- **[design.pdf](docs/design.pdf):** Formatted PDF report generated via ReportLab.
- **[PRESENTATION_OUTLINE.md](docs/PRESENTATION_OUTLINE.md):** 10-slide interview presentation outline.
- **[presentation.pptx](docs/presentation.pptx):** 16:9 widescreen PowerPoint presentation generated via python-pptx.
- **[WALKTHROUGH.md](docs/WALKTHROUGH.md):** Comprehensive code walkthrough and 15-question interview defense guide.

---

## 11. Author

Athish M, athishm2007@gmail.com

