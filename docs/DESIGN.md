# TDMA Schedule Planner and Spatial Reuse Optimizer: Engineering Design Document

**Author:** Protocol Development Team  
**Repository:** `tdma-schedule-optimizer`  
**Package:** `tdma`  
**Version:** 1.0.0  

---

## 1. Executive Summary & Problem Understanding

### 1.1 The Wireless Medium & TDMA Protocol Mechanics
In shared-spectrum radio frequency (RF) networks, transceivers share a common wireless channel. If two or more transmitters emit RF energy simultaneously within reception range of a common receiver, their electromagnetic waveforms interfere destructively, causing packet corruption (collision).

**Time Division Multiple Access (TDMA)** eliminates uncontrolled collisions by discretizing time into repeating sequences called **frames**. Each frame is subdivided into a fixed number of equal-duration **timeslots** ($T_{slot}$). Nodes are allocated designated slots in which they possess exclusive transmission rights.

```
Time Axis --->
+---------------+---------------+---------------+---------------+---------------+
| Slot 0 (1 ms) | Slot 1 (1 ms) | Slot 2 (1 ms) |      ...      | Slot K-1      |  (Frame Length = K slots)
+---------------+---------------+---------------+---------------+---------------+
|<----------------------------- Repeating TDMA Frame -------------------------->|
```

### 1.2 Interference Modalities & Spatial Reuse
The system models static transceivers positioned at 2D Euclidean coordinates $(x, y) \in \mathbb{R}^2$ with an omnidirectional communication radius $R = 500.0\text{ m}$. To ensure conflict-free broadcast scheduling, the schedule must resolve two distinct collision phenomena while maximizing spatial concurrency:

1. **Distance-1 Conflict (Direct In-Range Collision):**
   - **Condition:** Two nodes $u$ and $v$ have Euclidean distance $d(u, v) \le R$.
   - **Mechanism:** If $u$ and $v$ transmit concurrently, neither can decode the other's transmission due to mutual receiver saturation (half-duplex constraint) and overlapping RF emissions.
   - **Protocol Invariant:** $u$ and $v$ must **never** share a timeslot.

2. **Distance-2 Conflict (The Hidden Terminal Problem):**
   - **Condition:** Two nodes $u$ and $v$ are not in direct range ($d(u, v) > R$), but share a mutual neighbor $w$ such that $d(u, w) \le R$ and $d(v, w) \le R$.
   - **Mechanism:** Node $u$ cannot sense node $v$'s transmission (hidden terminal). If both transmit in the same slot, their signals superimpose destructively at $w$, causing collision and packet loss at the intermediate receiver.
   - **Protocol Invariant:** $u$ and $v$ must **never** share a timeslot.

3. **Spatial Reuse (Distance $\ge 3$ Hops):**
   - **Condition:** Nodes $u$ and $v$ have a shortest-path hop distance $h(u, v) \ge 3$ in the connectivity topology (or belong to disconnected graph components).
   - **Mechanism:** No common receiver can detect signals from both $u$ and $v$ with sufficient energy to corrupt reception.
   - **Optimization Objective:** Nodes separated by $\ge 3$ hops **may concurrently transmit in the same timeslot**, maximizing network throughput and spectral efficiency.

**Global Goal:** Minimize the total frame length (number of unique slots $K$). Minimizing $K$ maximizes per-node channel access frequency, minimizes packet latency, and maximizes aggregate network throughput.

---

## 2. Mathematical Modeling & Graph Theory

### 2.1 Graph Formulation
Let $V = \{v_1, v_2, \dots, v_n\}$ represent the set of radio nodes, where each node $v_i$ is located at coordinates $p(v_i) = (x_i, y_i)$.

1. **Physical Connectivity Graph $G = (V, E)$:**
   An undirected edge $(u, v) \in E$ exists if and only if the physical Euclidean distance satisfies:
   $$d(u, v) = \sqrt{(x_u - x_v)^2 + (y_u - y_v)^2} \le R$$
   *Boundary Rule:* Exactly $500.0\text{ m}$ is considered in-range. A numerical tolerance $\epsilon = 10^{-9}\text{ m}$ is applied during edge construction to prevent floating-point roundoff exclusion.

2. **Conflict Graph $G_{conflict} = G^2$ (The Graph Square):**
   The square of a graph $G$, denoted $G^2$, is defined on the same vertex set $V$, with an edge $(u, v) \in E(G^2)$ if and only if the shortest-path hop distance in $G$ satisfies:
   $$1 \le \text{dist}_G(u, v) \le 2$$

### 2.2 Proof of Equivalence: Distance-2 Coloring of $G \equiv$ Vertex Coloring of $G^2$
*Theorem:* A TDMA schedule mapping $c: V \rightarrow \{0, 1, \dots, K-1\}$ is conflict-free if and only if $c$ is a valid vertex coloring of $G^2$.

*Proof:*
- $(\Rightarrow)$ Suppose $c$ is a valid conflict-free schedule. If $(u, v) \in E(G^2)$, then by definition of graph power, $\text{dist}_G(u, v) \in \{1, 2\}$. If $\text{dist}_G(u, v) = 1$, $u$ and $v$ are adjacent in $G$ (distance-1 conflict). If $\text{dist}_G(u, v) = 2$, $u$ and $v$ share an intermediate neighbor $w$ (distance-2 hidden terminal conflict). In both cases, the protocol mandates $c(u) \neq c(v)$. Thus, no two adjacent vertices in $G^2$ share a color.
- $(\Leftarrow)$ Suppose $c$ is a valid vertex coloring of $G^2$. If two nodes $u, v$ have $\text{dist}_G(u, v) \le 2$, then by definition $(u, v) \in E(G^2)$, which implies $c(u) \neq c(v)$. If $\text{dist}_G(u, v) \ge 3$, $(u, v) \notin E(G^2)$, allowing $c(u) = c(v)$ (valid spatial reuse). Thus, $c$ satisfies all TDMA protocol requirements. $\blacksquare$

### 2.3 Theoretical Complexity & Bounds
- **NP-Hardness:** Determining the minimum chromatic number $\chi(G)$ is NP-hard (Karp, 1972). Even for unit disk graphs (UDG), distance-2 coloring is strongly NP-hard.
- **Lower Bound (Clique Number):**
  $$\chi(G^2) \ge \omega(G^2)$$
  Where $\omega(G^2)$ is the maximum clique size in $G^2$. If a subset of nodes $C \subseteq V$ pairwise conflict within 2 hops, each node in $C$ requires a distinct timeslot.
- **Upper Bound (Greedy Degree Bound):**
  $$\chi(G^2) \le \Delta(G^2) + 1$$
  Where $\Delta(G^2)$ is the maximum node degree in the conflict graph $G^2$.

---

## 3. Algorithm Design & Heuristic Architecture

The optimizer implements five diverse heuristics complemented by two exact solvers:

```
                                 [Conflict Graph G^2]
                                          |
        +------------------+--------------+-------------+------------------+
        |                  |              |             |                  |
        v                  v              v             v                  v
     1. LDF            2. DSATUR    3. Smallest-Last  4. Random Restarts  5. Local Search
   (O(V log V))        (O(V^2))        (O(V + E))        (N=1000)        (Kempe + Tabu)
        \                  |              |             |                  /
         +-----------------+--------------+-------------+-----------------+
                                          |
                              Candidate Best Schedule
                                          |
                           [Exact Solver Verification]
                             - Google OR-Tools CP-SAT
                             - Pure-Python BnB Fallback
                                          |
                           [Compaction: Contiguous 0..K-1]
                                          |
                        [Independent Verifier (BFS on G)]
```

### 3.1 Largest-Degree-First (LDF / Welsh-Powell)
- **Concept:** Highly connected nodes in $G^2$ pose the greatest constraint on neighboring allocations. Coloring high-degree vertices first minimizes bottlenecking later in the sequence.
- **Ordering:** Nodes sorted descending by $\text{deg}_{G^2}(v)$, with deterministic secondary tie-breaking by node identifier string.
- **Color Assignment:** First-fit greedy: assigns the smallest non-negative integer color $c \ge 0$ not used by any colored neighbor in $G^2$.
- **Complexity:** $\mathcal{O}(|V| \log |V| + |E(G^2)|)$.

### 3.2 Degree of Saturation (DSATUR - Brélaz, 1979)
- **Concept:** Dynamically measures the "urgency" of uncolored vertices. The **saturation degree** $\rho(v)$ is the number of distinct colors assigned to $v$'s colored neighbors in $G^2$.
- **Selection Rule:** At each step, select an uncolored node $u = \arg\max_{v} \rho(v)$.
- **Tie-Breaking:**
  1. Primary: Maximum uncolored degree in the remaining subgraph.
  2. Secondary: Maximum overall degree in $G^2$.
  3. Tertiary: Lexicographical node name string.
- **Complexity:** $\mathcal{O}(|V|^2 + |E(G^2)|)$.
- **Rationale:** DSATUR consistently achieves within 0–1 slot of the theoretical chromatic number on geometric random graphs.

### 3.3 Smallest-Last (Degeneracy / Matula & Beck, 1983)
- **Concept:** Exploits $k$-degeneracy. Vertices that can be colored with the lowest degree in a subgraph are eliminated first and placed at the bottom of an allocation stack.
- **Elimination:** Successively remove vertex $v$ with minimum degree in the induced remaining subgraph.
- **Coloring:** Reverse the elimination stack (smallest-last order) and color greedily.
- **Bound Guarantee:** Guarantees schedule length $\le \max_{H \subseteq G^2} \delta(H) + 1$, often outperforming static degree orderings in non-uniform clustering.
- **Complexity:** $\mathcal{O}(|V| + |E(G^2)|)$.

### 3.4 Seeded Randomized Restarts
- **Concept:** Explores alternative permutation basins by evaluating $N = 1000$ seeded random permutations of $V$, executing first-fit greedy coloring on each.
- **Determinism:** Seeded via `random.Random(seed)` (default: 42) ensuring reproducible schedules across runs.
- **Complexity:** $\mathcal{O}(N \cdot (|V| + |E(G^2)|))$.

### 3.5 Local Search & Color Reduction Pass
- **Concept:** Starting from the best heuristic schedule (using $K$ slots), attempts to compress the frame to $K-1$ slots by completely clearing slot $K-1$.
- **Three-Phase Reduction Strategy:**
  1. *Direct Recoloring:* For each node in slot $K-1$, attempt assignment to an existing conflict-free slot in $\{0, \dots, K-2\}$.
  2. *Kempe-Chain Swaps:* For nodes with residual conflicts, construct 2-color induced subgraphs $G^2[c_1, c_2]$ and swap colors within connected components to isolate the target node.
  3. *Min-Conflicts Tabu Search:* If direct swaps fail, assign target nodes to colors minimizing neighbor conflicts and run tabu search (tenure $= \max(5, |V|/3)$) over up to 2000 iterations to eliminate remaining violations.
  4. Repeat iteratively whenever a reduction to $K-1$ succeeds.

### 3.6 Exact Solvers
1. **Google OR-Tools CP-SAT:**
   - Formulated as a Constraint Satisfaction Optimization Problem:
     - Binary variables $x_{v, c} \in \{0, 1\}$ denoting node $v$ assigned slot $c$.
     - Binary indicator $y_c \in \{0, 1\}$ denoting slot $c$ is active.
     - Coverage: $\sum_{c=0}^{K_{ub}-1} x_{v, c} = 1, \quad \forall v \in V$.
     - Conflict: $x_{u, c} + x_{v, c} \le y_c, \quad \forall (u, v) \in E(G^2), \forall c$.
     - Symmetry Breaking: $y_0 \ge y_1 \ge y_2 \dots$; Pre-color maximum clique $C$ such that $x_{C_i, i} = 1$.
     - Objective: Minimize $\sum_{c} y_c$.
2. **Pure-Python Branch-and-Bound Backtracking (Zero-Dependency Fallback):**
   - Implements a dedicated branch-and-bound solver with:
     - Pre-coloring of the maximum clique $\omega(G^2)$ to eliminate color permutation symmetry.
     - Pruning whenever current colors used $\ge$ best-known upper bound.
     - Immediate termination when upper bound equals clique lower bound $\omega(G^2)$.
     - DSATUR variable branching order.

### 3.7 What Was Tried and Rejected
- **Pure Genetic Algorithms (GA):** Prototyped with chromosome string representations. Rejected due to excessive runtime ($> 5\text{ seconds}$), high stochastic variance, and poor constraint satisfaction without heavy repair heuristics.
- **Simulated Annealing on Unconstrained Encodings:** Tested with temperature cooling schedules. Frequently converged to near-valid states with 1–2 lingering conflicts, requiring additional post-processing repairs.
- **Naive ILP without Symmetry Breaking:** Slower by orders of magnitude due to branching over equivalent color permutations. Adding maximum clique fixation resolved this bottleneck.

---

## 4. Empirical Results & Topology Benchmarks

All metrics reported below were generated by executing the codebase directly against the configured benchmark suite (`benchmarks.py`, seed: 42):

### 4.1 Topology Comparison Table

| Topology Scenario | Nodes ($|V|$) | $G$ Edges | $G^2$ Edges | Max Deg $\Delta(G^2)$ | Exact Optimum ($\chi$) | Best Heuristic | Heuristic Gap | Exact Runtime |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **1. 4x4 Grid (300 m spacing)** | 16 | 42 | 90 | 15 | **9 slots** | **9 slots** | **0 (Optimal)** | 0.478 ms |
| **2. Sparse Linear Chain (350 m)**| 16 | 15 | 29 | 4 | **3 slots** | **3 slots** | **0 (Optimal)** | 0.171 ms |
| **3. Dense Cluster ($d \le 500$ m)**| 16 | 120 | 120 | 15 | **16 slots**| **16 slots**| **0 (Optimal)** | 0.222 ms |
| **4. Two Disconnected Clusters** | 16 | 56 | 56 | 7 | **8 slots** | **8 slots** | **0 (Optimal)** | 0.304 ms |

### 4.2 Detailed Analysis by Topology

#### Topology 1: 4x4 Grid (300 m Spacing)
- **Physical Layout:** Nodes arranged on a $4 \times 4$ lattice from $(0, 0)$ to $(900, 900)$ meters.
- **RF Connectivity:**
  - Horizontal/vertical neighbor distance: $300.0\text{ m} \le 500\text{ m}$ (Connected in $G$).
  - Diagonal neighbor distance: $\sqrt{300^2 + 300^2} \approx 424.26\text{ m} \le 500\text{ m}$ (Connected in $G$).
- **Mathematical Invariant:** Any $3 \times 3$ subgrid forms a clique of size 9 in $G^2$ because all pairs within that $3 \times 3$ subgrid are at most 2 hops apart. Therefore, $\omega(G^2) = 9$.
- **Spatial Reuse Result:**
  All four corner nodes—`Node_01` $(0, 0)$, `Node_04` $(900, 0)$, `Node_13` $(0, 900)$, and `Node_16` $(900, 900)$—are separated by $\ge 3$ hops in $G$. The optimizer successfully co-allocates all four corner nodes to **Slot 8**!
  Likewise, edge pairs (`Node_02` & `Node_14`), (`Node_03` & `Node_15`), (`Node_05` & `Node_08`), and (`Node_09` & `Node_12`) achieve spatial reuse.
- **Frame Length:** Achieves true theoretical minimum: **9 slots**.

#### Topology 2: Sparse Linear Chain (350 m Spacing)
- **Physical Layout:** 16 nodes arranged along a single axis $x_i = i \times 350\text{ m}$.
- **Hop Distances:** Node $i$ connects only to $i-1$ and $i+1$. Hop distance $h(i, j) = |i - j|$.
- **Spatial Reuse Result:** Nodes with $|i - j| \ge 3$ reuse slots. Frame length matches the theoretical 3-slot coloring of a path graph $P_n^2$:
  $$\text{Pattern: } 1, 2, 0, 1, 2, 0, 1, 2, 0, 1, 2, 0, 1, 2, 0, 1$$
- **Frame Length:** **3 slots**.

#### Topology 3: Dense Cluster (All Nodes in Range)
- **Physical Layout:** 16 nodes randomly clustered within a $250 \times 250\text{ m}$ footprint.
- **RF Connectivity:** Every node pair is within $500\text{ m}$. $G$ and $G^2$ form the complete graph $K_{16}$ (120 edges).
- **Frame Length:** Exactly **16 slots**. Zero spatial reuse possible; each node requires an exclusive slot.

#### Topology 4: Disconnected Clusters (Two 8-Node Enclaves)
- **Physical Layout:** Cluster A at $(0, 0)$, Cluster B at $(3000, 3000)$ meters.
- **RF Connectivity:** Distance between clusters is $\approx 4242\text{ m} \gg 1000\text{ m}$ ($\infty$ hops).
- **Spatial Reuse Result:** Nodes in Cluster A and Cluster B completely duplicate slots $0..7$. Frame length is $\max(8, 8) =$ **8 slots** instead of 16.

---

## 5. Independent Verification Methodology

To prevent algorithmic circularity, the test verification engine (`src/tdma/verify.py`) does **not** import or reuse any graph coloring code, conflict graph logic, or $G^2$ power routines.

### Verification Algorithm
```python
def verify_schedule(G_physical, schedule):
    # 1. Coverage Check: V(G) == keys(schedule)
    # 2. Contiguity Check: values(schedule) == {0, 1, ..., K-1}
    # 3. BFS Shortest Path Calculation on G_physical:
    for u, v in pairs(V):
        if schedule[u] == schedule[v]:
            h = shortest_path_length_BFS(G_physical, u, v)
            assert h >= 3, f"Collision: {u} and {v} share slot at hop distance {h}"
```

### Verification Safeguards
1. **Distance-1 Direct Collision Detection:** Explicitly flags any two adjacent nodes sharing a slot.
2. **Distance-2 Hidden Terminal Detection:** Intersects neighbor sets $\mathcal{N}(u) \cap \mathcal{N}(v)$ to identify the exact intermediate receiver at risk.
3. **Contiguity Enforcement:** Flags missing slot indices (e.g., using slots 0, 2 without slot 1).
4. **Coverage Assertion:** Flags unassigned or phantom nodes.

---

## 6. Part 2: EMANE Integration & Emulation Bridge

### 6.1 EMANE Architecture & Modeling Choices
EMANE (Extendable Mobile Ad-hoc Network Emulator) enforces real-time medium access control via Network Emulation Modules (NEMs). The bridge interfaces with the official `tdmaeventschedulerradiomodel`:

- **MAC Configuration (`mac-tdmaeventschedule.xml`):**
  - `slotduration`: `1000` $\mu\text{s}$ (1.0 ms slot length).
  - `slotoverhead`: `50` $\mu\text{s}$ guard interval accommodating propagation delay across 500 m ($1.67\ \mu\text{s}$) plus transceiver switching time.
- **PHY Configuration (`phy-universal.xml`):**
  - `frequency`: `2400000000` Hz (2.4 GHz carrier).
  - `bandwidth`: `20000000` Hz (20 MHz channel).
  - `txpower`: `0.0` dBm.
- **Mapping Strategy:**
  - Nodes assigned to slot $s$ are flagged as transmitters (`tx="true"`, `nodes="<id>"`).
  - All other nodes in that slot are placed in receive mode (`rx="*"`).

### 6.2 Round-Trip Validation
The bridge module (`emane/bridge/schedule_to_emane.py`) implements a standalone XML validator that parses generated schedule XML and verifies full bi-directional consistency against the schedule matrix without requiring EMANE to be installed.

### 6.3 What is Tested vs. What is Design-Only
- **Tested:** Python schedule transformation, NEM ID resolution, XML schema formatting, round-trip matrix validation, event script generation.
- **Design-Only:** Over-the-air RF packet exchange inside the Linux kernel network stack using live EMANE daemons (due to lack of host root/kernel privileges).

---

## 7. Assumptions & Edge-Case Handling

1. **Boundary Condition (500.0 m):**
   Distances are computed using double-precision Euclidean distance:
   $$d = \sqrt{(x_1 - x_2)^2 + (y_1 - y_2)^2}$$
   An edge is established if $d \le 500.0 + 10^{-9}\text{ m}$. Exactly 500.0 m is strictly treated as in-range.
2. **Physical Co-location (Duplicate Coordinates):**
   Placing two distinct radio identifiers at identical coordinates $(x, y)$ is a physical anomaly that causes singular topologies. The parser detects duplicate coordinates and terminates immediately with an explicit error message and non-zero exit code.
3. **Contiguous Compaction:**
   Whenever pruning or heuristics leave gaps in slot numbering, the compaction engine relabels active colors into the contiguous interval $[0, K-1]$.
4. **Arbitrary Node Counts ($n \ge 1$):**
   The pipeline gracefully supports single-node topologies (producing 1 slot, 0 edges) and arbitrary node counts.

---

## 8. Future Roadmap

1. **Multi-Channel TDMA (Time-Frequency Grid):**
   Expand the coloring dimension to 2D lattices $(t, f)$ where nodes may select across orthogonal frequency channels, reducing frame length.
2. **Dynamic Mobile TDMA (MANET):**
   Implement distributed reservation protocols (e.g., DRAND / C-TDMA) with periodic schedule re-convergence for moving nodes.
3. **Directed Link Scheduling (STDMA):**
   Transition from omnidirectional broadcast reservation to directed link-based slot scheduling, allowing simultaneous transmission to distinct non-interfering receivers.
