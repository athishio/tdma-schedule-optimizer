# Presentation Outline: TDMA Schedule Planner and Spatial Reuse Optimizer

**Target Audience:** Wireless Protocol Development Internship Interviewers & Systems Engineers  
**Duration:** 15–20 minutes  
**Format:** 8 Slides (16:9 Widescreen, 13.333 × 7.5 in)  
**Presenter:** Athish M (athishm2007@gmail.com)  

---

### Slide 1: Title
- **Kicker:** WIRELESS PROTOCOL DEVELOPMENT | TAKE-HOME TASK
- **Title:** Packing a radio network into the fewest time slots
- **Subtitle:** distance-2 graph coloring, spatial reuse, exact-optimum benchmark, EMANE bridge
- **Key Metrics / Stats:**
  - `16` radios, 500 m range
  - `9` slots on the 4x4 grid, proven optimal
  - `47` automated tests passing
- **Presenter:** Athish M

---

### Slide 2: The Problem
- **Title:** Two ways to collide, one way to save slots
- **Core Concept:** TDMA operates on a single shared frequency with a repeating frame of K slots. Fewer slots means each radio talks more often.
- **Three Interference & Protocol Rules:**
  - *Rule 1 (Direct link):* Adjacent radios within 500 m direct range collide if transmitting concurrently. Requires distinct slots.
  - *Rule 2 (Hidden terminal):* Two non-adjacent radios with a shared neighbour corrupt reception at that mutual node. Requires distinct slots.
  - *Rule 3 (Spatial reuse):* Radios 3+ hops apart cannot interfere with each other's receptions and safely share the same timeslot, multiplying channel capacity.
- **Native Visual:** A → B ← C native diagram with "under 500 m" link labels, out-of-range dashed connection between A and C, and caption: *"A and C are out of range, yet if both transmit in the same slot they collide at B."*

---

### Slide 3: The Model
- **Title:** Distance-2 coloring is just ordinary coloring of the squared graph
- **Three Formulation Steps:**
  - *(1) Build G:* Undirected edge if Euclidean distance $d \le 500.0$ m (exactly 500 m counts, $10^{-9}$ m tolerance).
  - *(2) Square it ($G^2$):* Using `nx.power(G, 2)`. Edges exist between 1-hop and 2-hop neighbors so hidden terminals become adjacent.
  - *(3) Color $G^2$:* Color equals timeslot. Pairs 3+ hops apart stay unconnected so they may reuse a color.
- **Native Visuals:**
  - 4-node line diagram A–B–C–D colored with Slots 0, 1, 2, 0 demonstrating safe spatial reuse across 3 hops (*"A and D are 3 hops apart, so they reuse slot 0"*).
  - Bounds & complexity panel: $\omega(G^2) \le \chi(G^2) \le \Delta(G^2) + 1$ with explanation that graph coloring is NP-hard, motivating heuristics paired with exact lower bounds.

---

### Slide 4: Algorithms
- **Title:** Five heuristics, two exact solvers, one independent checker
- **Native Comparative Table:**
  - *Largest-Degree-First (LDF):* Orders nodes by conflict degree; colors high-degree bottlenecks first. $\mathcal{O}(V \log V + E)$ (~0.06 ms).
  - *DSATUR:* Greedy saturation picking node with highest colored-neighbor diversity. $\mathcal{O}(V^2 + E)$ (~0.15 ms).
  - *Smallest-Last:* Reverse elimination ordering bounded by degeneracy. $\mathcal{O}(V + E)$ (~0.20 ms).
  - *Random Restarts:* 1000 seeded orders, retains the best observed schedule. (~24 ms).
  - *Local Search:* Kempe-chain swaps plus tabu search, up to 2000 steps to trim top color. (~50 ms).
  - *CP-SAT Exact:* 0-1 ILP with maximum-clique pre-coloring for symmetry breaking. Proven optimum (~0.8 ms).
  - *Branch & Bound Exact:* Backtracking with DSATUR branching, no dependencies, used as fallback.
- **Architecture Callout:** The schedule is the best result across methods, the exact solver is the yardstick, and a separate BFS verifier checks the final schedule.

---

### Slide 5: The 4x4 Grid
- **Title:** The 4x4 grid needs 9 slots, and four corners share one
- **Native 4x4 Grid Diagram:**
  - 16 nodes arranged from Node_01 at bottom-left (0,0) to Node_16 at top-right (900,900).
  - Drawn using the real schedule from `examples/grid_schedule.json` (Node_01 to Node_16 = slots 8, 4, 5, 8, 6, 0, 1, 6, 7, 2, 3, 7, 8, 4, 5, 8).
  - Validated by running the independent verifier prior to rendering.
  - Four corner radios (Nodes 1, 4, 13, 16) ringed with a dashed amber ring sharing Slot 8.
- **Mathematical Proof of Optimality:**
  - (1) Diagonal distance $300\sqrt{2} = 424.3$ m is in direct radio range ($\le 500$ m).
  - (2) Any $3 \times 3$ subgrid of 9 nodes has all pairs within 2 hops in $G$.
  - (3) Therefore, those 9 nodes form a 9-clique in $G^2$ (every pair conflicts).
  - (4) $\chi(G^2) \ge \omega(G^2) = 9$. No schedule can use fewer than 9 slots, and the solver finds exactly 9.
- **Key Metrics:** 42 edges in $G$, 90 edges in $G^2$, 15 max degree in $G^2$.
- **Brief Clarification:** The assignment sample's 5-slot table is an illustrative format example with partial coordinates, not a target.

---

### Slide 6: Benchmarks
- **Title:** Every heuristic matched the exact optimum on all four topologies
- **Native Clustered Bar Chart:** Exact optimum vs best heuristic across 4 benchmark topologies:
  - 4x4 Grid (300 m): 9 vs 9
  - Sparse Linear (350 m): 3 vs 3
  - Dense Cluster (≤500 m): 16 vs 16
  - Two Disconnected Clusters (3000 m gap): 8 vs 8
- **Topology Summary Table:**
  - 4x4 Grid: 42 $G$ edges, 90 $G^2$ edges, 9 slots
  - Sparse Line: 15 $G$ edges, 29 $G^2$ edges, 3 slots
  - Dense Cluster: 120 $G$ edges, 120 $G^2$ edges, 16 slots
  - Two Clusters: 56 $G$ edges, 56 $G^2$ edges, 8 slots
- **Analysis Cards:**
  - *What the numbers say:* Dense cluster is a 16-clique so 16 is forced; two clusters 3000 m apart reuse slots 0 to 7, halving the frame.
  - *Cost on 16 nodes:* Greedy and DSATUR under 0.3 ms, 1000 restarts about 15 to 37 ms, exact solve about 0.2 to 1.2 ms.

---

### Slide 7: Verification and Part 2
- **Title:** Verified independently; EMANE bridge designed and tested offline
- **Top Row Cards:**
  - *Independent Verifier:* BFS hop distances on raw $G$, zero shared code with colouring. Checks one slot per node, contiguous slots $0..K-1$, no pair within 2 hops shares a slot. All 47 tests pass, including property tests and a fallback solver that matches CP-SAT.
  - *EMANE Range Modelling (Design Only):* EMANE does not know the 500 m rule natively. Radios communicate over multicast OTA; locations and pathloss must be calibrated to ~500 m effective range, otherwise all 16 radios hear each other globally and the schedule would collide. Status: planned, not run.
- **Native 5-Box Pipeline:**
  - `[Python Optimizer]` → `[Schedule JSON]` → `[Bridge Script]` → `[Schedule XML]` → `[EMANE Nodes]`
  - Explicit boundary labels:
    - *TESTED OFFLINE:* JSON to XML translation, node-to-NEM mapping, round-trip schema check.
    - *DESIGN ONLY:* live emulation, Docker build, packet-level slot enforcement.

---

### Slide 8: Status
- **Title:** What is proven, what is pending, and what comes next
- **Three Structured Columns:**
  - **PROVEN:**
    - 9, 3, 16, 8 slots each equal to the exact optimum.
    - Independent verifier passes on all topologies.
    - CP-SAT and pure-Python solver agree.
    - 47 automated tests pass on a fresh clone.
    - Exact 500.0 m float tolerance ($10^{-9}$ m) and duplicate rejection.
  - **NOT YET RUN:**
    - Live EMANE emulation in multi-node container.
    - Docker build and live TAP interface setup.
    - Packet-level slot enforcement with ping/iperf.
    - Pathloss calibration to about 500 m.
    - Deliberate conflict injection test.
  - **NEXT:**
    - Multi-channel time $\times$ frequency colouring across orthogonal bands.
    - Mobility and dynamic re-scheduling (DRAND / C-TDMA protocols).
    - Link-level scheduling (directed spatial TDMA).
    - Larger topologies to stress the heuristics ($n = 50$ to 500).
