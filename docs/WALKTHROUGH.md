# Technical Walkthrough & Line-by-Line Defense Guide

**Project:** TDMA Schedule Planner and Spatial Reuse Optimizer  
**Package:** `tdma`  
**Target:** Wireless Protocol Development & Systems Engineering Technical Interviews  

---

## 1. Architecture & Module Walkthrough

### 1.1 `src/tdma/graph.py`
* **Purpose:** Ingests raw radio coordinates, validates topological sanity, computes Euclidean distances, builds the physical connectivity graph $G$, and calculates the conflict graph $G^2$.
* **Key Functions:**
  - `parse_coordinates(raw_input)`:
    - Parses JSON string or dict.
    - Validates that coordinates are 2-element numeric lists/tuples $[x, y]$ with finite values (`math.isfinite`).
    - Enforces physical non-co-location: radio transceivers cannot occupy identical 2D coordinates. Raises `ValueError` on duplicates.
  - `euclidean_distance(p1, p2)`:
    - Computes $\sqrt{(x_1 - x_2)^2 + (y_1 - y_2)^2}$ via `math.hypot`.
  - `build_connectivity_graph(coords, radio_range=500.0)`:
    - Creates an undirected NetworkX graph $G$.
    - Adds edges between all node pairs with $d(u, v) \le 500.0 + 10^{-9}\text{ m}$.
  - `build_conflict_graph(g_connectivity)`:
    - Computes the graph square $G^2 = \text{nx.power}(G, 2)$.
    - An edge exists in $G^2$ if and only if $\text{dist}_G(u, v) \in \{1, 2\}$.

---

### 1.2 `src/tdma/coloring.py`
* **Purpose:** Implements 5 graph coloring heuristics and local search passes to find minimum vertex colorings of $G^2$.
* **Key Functions & Heuristics:**
  - `compact_slots(schedule)`:
    - Relabels assigned colors into contiguous integers $\{0, 1, \dots, K-1\}$.
  - `greedy_largest_degree_first(g_conflict)` (LDF / Welsh-Powell):
    - Sorts nodes by degree in $G^2$ descending, with deterministic name tie-breaking.
    - Assigns smallest non-negative integer color available.
  - `dsatur_coloring(g_conflict)` (Degree of Saturation):
    - Dynamically prioritizes uncolored nodes with the highest saturation degree $\rho(v)$ (number of distinct colors assigned to colored neighbors).
    - Ties broken by degree in the uncolored subgraph, then degree in $G^2$, then node name.
  - `smallest_last_coloring(g_conflict)` (Matula & Beck Degeneracy):
    - Repeatedly eliminates the vertex of minimum degree in the remaining subgraph.
    - Colors vertices in reverse elimination order.
  - `randomized_restarts_coloring(g_conflict, num_restarts=1000, seed=42)`:
    - Shuffles vertex order randomly across 1000 iterations using a seeded PRNG.
    - Retains the coloring with the minimum number of colors.
  - `local_search_color_reduction(g_conflict, initial_schedule, seed=42)`:
    - Attempts to eliminate color class $K-1$.
    - Phase 1: Direct recoloring into conflict-free slots $0..K-2$.
    - Phase 2: Kempe-chain 2-color swaps in induced two-color subgraphs.
    - Phase 3: Min-conflicts local search with Tabu tenure to escape local minima.
  - `run_all_heuristics(...)`:
    - Executes all heuristics, benchmarks execution time via `time.perf_counter()`, and packages results.

---

### 1.3 `src/tdma/exact.py`
* **Purpose:** Solves the minimum graph coloring problem to mathematical optimality ($\chi(G^2)$).
* **Solvers:**
  - `solve_cpsat(g_conflict)`:
    - Google OR-Tools Constraint Programming (CP-SAT) formulation.
    - Binary decision variables $x_{v, c} \in \{0, 1\}$ and slot active indicators $y_c \in \{0, 1\}$.
    - Symmetry breaking: Maximum clique $\omega(G^2)$ is pre-assigned fixed colors $0..\omega-1$.
    - Slot ordering constraints: $y_c \ge y_{c+1}$.
  - `solve_branch_and_bound(g_conflict)` (Pure-Python Fallback):
    - DSATUR-guided branch-and-bound backtracking.
    - Pre-colors maximum clique $\omega(G^2)$.
    - Instant lower-bound pruning: halts search if upper bound matches clique lower bound.
    - Color symmetry breaking: branches on at most one new unused color.
  - `solve_exact_coloring(...)`:
    - Detects whether `ortools` is installed; falls back gracefully to pure-Python Branch-and-Bound.

---

### 1.4 `src/tdma/verify.py`
* **Purpose:** Independent, zero-trust schedule verifier with zero code reuse.
* **Logic:**
  - Evaluates schedules directly against physical graph $G$ using Breadth-First Search (BFS).
  - Asserts coverage: $V(G) == \text{keys}(schedule)$.
  - Asserts contiguity: $\text{values}(schedule) == \{0, 1, \dots, K-1\}$.
  - Asserts conflict-freedom: For all $u, v \in V$ with $schedule[u] == schedule[v]$, verifies that $\text{BFS\_dist}_G(u, v) \ge 3$.
  - Explicitly identifies Distance-1 (direct) and Distance-2 (hidden terminal) violations.

---

### 1.5 `src/tdma/report.py`
* **Purpose:** Formats standard ASCII reports, boolean schedule matrices, JSON exports, and Matplotlib network topology diagrams.
* **Key Functions:**
  - `natural_sort_key(s)`: Natural sorting for node names (`Node_2` before `Node_10`).
  - `format_report(...)`: Generates ASCII output matching exact problem specifications.
  - `format_comparison_table(...)`: Produces benchmark comparison table with optimality gaps.
  - `export_schedule_json(...)`: Writes structured JSON with schedule matrix and metadata.
  - `plot_topology(...)`: Plots physical nodes, connectivity edges, and color-coded slot allocations.

---

### 1.6 `src/tdma/cli.py`
* **Purpose:** Command-line interface with argument parsing, error handling, and clean exit codes.
* **Exit Codes:**
  - `0`: Execution successful, schedule verified conflict-free.
  - `1`: Schedule verification failed (conflicts detected).
  - `2`: Input error (malformed JSON, duplicate coordinates, missing file).

---

### 1.7 `emane/bridge/schedule_to_emane.py`
* **Purpose:** Part 2 integration bridge translating Part 1 schedules into EMANE TDMA XML profiles and Python event publisher scripts.
* **Key Functions:**
  - `generate_emane_tdma_xml(...)`: Formats XML for `tdmaeventschedulerradiomodel` with 1 ms slots and Tx/Rx node lists.
  - `parse_emane_tdma_xml(...)`: Standalone XML parser for offline validation.
  - `validate_round_trip(...)`: Validates 100% parity between schedule matrix and generated XML.
  - `generate_emane_python_event_script(...)`: Generates dynamic event publisher using `emane.events.TDMAScheduleEvent`.

---

## 2. Key Mathematical Proofs & Theoretical Foundations

### 2.1 Why Distance-2 Coloring of $G$ Equals Ordinary Coloring of $G^2$
* **Definition:** A distance-2 coloring of $G = (V, E)$ assigns colors $c(v)$ such that $c(u) \neq c(v)$ whenever $\text{dist}_G(u, v) \le 2$.
* **Definition:** An ordinary vertex coloring of $G^2 = (V, E')$ assigns colors such that $c(u) \neq c(v)$ whenever $(u, v) \in E'$.
* **Equivalence:**
  By definition of graph power, $(u, v) \in E(G^2) \iff 1 \le \text{dist}_G(u, v) \le 2$.
  Therefore, $(u, v) \in E(G^2)$ if and only if $u$ and $v$ have a Distance-1 or Distance-2 conflict in $G$.
  Hence, any valid vertex coloring of $G^2$ satisfies all TDMA Distance-1 and Distance-2 conflict constraints on $G$, and vice-versa. $\blacksquare$

### 2.2 Why Greedy Coloring Uses At Most $\Delta(G^2) + 1$ Colors
* **Proof:**
  Let $v_1, v_2, \dots, v_n$ be an arbitrary vertex ordering. When vertex $v_i$ is colored, it has at most $\text{deg}_{G^2}(v_i) \le \Delta(G^2)$ neighbors that could have been previously colored.
  Therefore, among the integer colors $\{0, 1, \dots, \Delta(G^2)\}$, at most $\Delta(G^2)$ distinct colors can be occupied by neighbors of $v_i$.
  By the Pigeonhole Principle, at least one color in $\{0, 1, \dots, \Delta(G^2)\}$ must be free.
  The greedy first-fit strategy is guaranteed to select an available color $\le \Delta(G^2)$.
  Thus, $\chi(G^2) \le \Delta(G^2) + 1$. $\blacksquare$

### 2.3 Why the 3x3 Subgrid Argument Gives a Lower Bound of 9
* **Geometry:** On a grid with 300 m spacing and 500 m radio range:
  - Horizontal/vertical separation: $300\text{ m} \le 500\text{ m}$ (hop distance 1).
  - Diagonal separation: $\sqrt{300^2 + 300^2} \approx 424.26\text{ m} \le 500\text{ m}$ (hop distance 1).
* **Subgrid Hop Distance:**
  Consider any $3 \times 3$ subgrid of 9 nodes (e.g., coordinates $\{0, 300, 600\} \times \{0, 300, 600\}$).
  The maximum distance between any two nodes in this subgrid is the opposite corner distance:
  $$\sqrt{600^2 + 600^2} \approx 848.5\text{ m} > 500\text{ m}$$
  However, both opposite corners connect to the center node $(300, 300)$ at diagonal distance $\approx 424.26\text{ m} \le 500\text{ m}$.
  Thus, the shortest path hop distance between any pair in the $3 \times 3$ subgrid is at most 2 hops!
* **Clique Formation:**
  Because every pair of nodes in the $3 \times 3$ subgrid has hop distance $\le 2$, every pair is connected by an edge in $G^2$.
  This induces a complete subgraph (clique) of size 9 in $G^2$: $\omega(G^2) \ge 9$.
* **Conclusion:**
  Since the chromatic number is bounded below by the clique number ($\chi \ge \omega$), the frame length must be at least 9 slots. Any schedule with fewer than 9 slots will cause a collision. $\blacksquare$

### 2.4 Why the $10^{-9}$ Tolerance Is Necessary
* In double-precision floating-point arithmetic (`IEEE 754`), calculating $\sqrt{300^2 + 400^2}$ can occasionally yield $500.00000000000006$ due to binary fraction rounding.
* Strict comparison `dist <= 500.0` would evaluate to `False`, incorrectly disconnecting radios placed exactly 500 m apart.
* Using `dist <= 500.0 + 1e-9` guarantees numerical robustness without including nodes at 500.001 m.

---

## 3. Top 15 Likely Interview Questions & Model Answers

### Q1: What is the difference between Distance-1 and Distance-2 coloring in TDMA?
**Answer:** Distance-1 coloring prevents direct collisions between adjacent nodes in radio range ($d \le 500\text{ m}$). Distance-2 coloring prevents the **hidden terminal problem**, where two nodes out of range of each other transmit simultaneously to a shared intermediate neighbor, corrupting reception at that mutual neighbor.

### Q2: Why did you construct the conflict graph as $G^2$ instead of checking 2-hop paths in every heuristic?
**Answer:** Constructing $G^2$ decouples topology analysis from coloring. Once $G^2$ is built via `nx.power(G, 2)`, standard graph coloring heuristics (LDF, DSATUR, Kempe chains) apply directly with optimal $\mathcal{O}(1)$ neighbor lookups, avoiding redundant $\mathcal{O}(V^2)$ BFS traversals during optimization.

### Q3: Why does DSATUR perform better than simple greedy coloring?
**Answer:** Static greedy orderings (like LDF) sort vertices once by degree, ignoring how choices affect remaining vertices. DSATUR dynamically updates the **saturation degree**—the number of distinct colors already used by neighbors. It always colors the most constrained vertex next, minimizing backtracking and color count.

### Q4: How does Smallest-Last (degeneracy) ordering help in non-uniform networks?
**Answer:** Degeneracy ordering successively removes minimum-degree vertices from the remaining subgraph. This protects high-degree nodes in dense sub-clusters from being arbitrarily constrained by peripheral nodes, guaranteeing a coloring bounded by the graph's degeneracy $\max_{H \subseteq G} \delta(H) + 1$.

### Q5: What is a Kempe chain, and how does your local search use it?
**Answer:** A Kempe chain is a maximal connected component in a subgraph induced by two colors $(c_1, c_2)$. Swapping the colors of all vertices in this component preserves valid coloring. Our local search uses Kempe swaps to free up a target color on neighbors of a node, allowing us to eliminate the highest color class.

### Q6: Why did you implement a pure-Python exact solver alongside OR-Tools?
**Answer:** In production and embedded deployment, external C-libraries like OR-Tools may not have pre-compiled wheels (e.g., Python 3.14 or custom ARM Linux architectures). Our pure-Python Branch-and-Bound solver guarantees mathematical optimality with zero external dependencies.

### Q7: How does your exact solver avoid exploring symmetric color permutations?
**Answer:** We find a maximum clique $\omega(G^2)$ and pre-assign its vertices fixed colors $0 \dots \omega-1$. Furthermore, during backtracking, the solver branches on existing colors first and introduces at most **one** new color, pruning redundant permutations.

### Q8: Why did the sample output in the prompt mention 5 slots, but your optimizer found 9 slots for the 4x4 grid?
**Answer:** The prompt explicitly stated that 5 slots was illustrative and not to be hardcoded. Mathematically, in a 4x4 grid with 300 m spacing and 500 m range, diagonal nodes are within range ($424.26\text{ m} \le 500\text{ m}$). Any $3 \times 3$ subgrid forms a 9-node clique in $G^2$. Thus, 9 is a proven mathematical lower bound ($\omega \ge 9$).

### Q9: Why is the verifier independent of the optimizer?
**Answer:** Using the same graph structures ($G^2$) or algorithms for both optimization and verification creates circular logic: a bug in $G^2$ construction would fool the verifier. Our verifier uses raw physical graph $G$ and runs independent BFS shortest paths to verify hop distances directly.

### Q10: What edge cases did you encounter, and how did you handle them?
**Answer:**
1. *Boundary 500.0 m:* Handled with $10^{-9}\text{ m}$ float tolerance.
2. *Duplicate coordinates:* Flagged as physical impossibilities with clear validation errors.
3. *Single-node/isolated topologies:* Gracefully outputs 1 slot without crashes.
4. *Disconnected clusters:* Full spatial reuse across clusters (8 slots instead of 16).

### Q11: How do you map node slot assignments to EMANE's TDMA radio model?
**Answer:** In EMANE's `tdmaeventschedulerradiomodel`, each frame is divided into $K$ slots. For slot index $s$, nodes assigned slot $s$ are configured as transmitters (`tx="true"`, `nodes="<id>"`), while all other nodes are set to receive (`rx="*"`).

### Q12: Why is the slot duration set to 1000 µs (1 ms) and guard time to 50 µs?
**Answer:** Over 500 meters, radio propagation takes $\approx 1.67\ \mu\text{s}$. A 50 µs guard time accounts for RF power ramp-up, propagation delay, and clock synchronization drift while leaving 950 µs (95%) for data payload.

### Q13: What happens in EMANE if two adjacent nodes are accidentally scheduled in the same slot?
**Answer:** Both nodes transmit RF energy simultaneously. The EMANE Universal PHY model sums the overlapping signals, calculating the Signal-to-Interference-plus-Noise Ratio (SINR). Because SINR drops below the Packet Clear Rate (PCR) threshold, packets are dropped as interference (`numRxDropInterference`).

### Q14: How does your EMANE bridge validate XML schedules without requiring EMANE installed?
**Answer:** It implements an independent XML parser (`parse_emane_tdma_xml`) that performs round-trip schema parsing, verifying that frame length, slot duration, and node TX/RX assignments in the XML match the input schedule matrix with 100% parity.

### Q15: How would you extend this scheduler for mobile tactical networks?
**Answer:** Mobile nodes cause graph edges to appear and disappear dynamically. I would implement a hybrid architecture: pre-compute cluster-based spatial reuse schedules, and use distributed reservation algorithms (e.g., DRAND) for local slot adjustments when topology changes are detected via link-state beacons.
