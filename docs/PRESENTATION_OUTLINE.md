# Presentation Outline: TDMA Schedule Planner and Spatial Reuse Optimizer

**Target Audience:** Wireless Protocol Development Internship Interviewers & Systems Engineers  
**Duration:** 15–20 minutes  
**Format:** 10 Slides  

---

### Slide 1: Title & Overview
- **Title:** TDMA Schedule Planner & Spatial Reuse Optimizer
- **Subtitle:** Conflict-Free Frame Optimization in Multi-Hop Wireless Networks with EMANE Emulation Bridge
- **Presenter:** Protocol Development Engineering Candidate
- **Core Objective:** Minimize TDMA frame length under strict Distance-1 and Distance-2 (hidden terminal) constraints while exploiting spatial reuse.

---

### Slide 2: The Physical & Protocol Challenge
- **Shared Wireless Medium:** Single frequency channel, half-duplex omnidirectional transceivers.
- **Interference Modalities:**
  - *Distance-1 Collision:* Adjacent nodes within radio range ($d \le 500\text{ m}$) collide if transmitting simultaneously.
  - *Distance-2 (Hidden Terminal) Collision:* Two nodes out of range of each other, but sharing a common neighbor, corrupt packets at that mutual receiver.
- **Spatial Concurrency (Reuse):** Nodes separated by $\ge 3$ hops can safely reuse timeslots without mutual interference.
- **Goal:** Minimize frame length $K$ (maximizes per-node throughput and minimizes packet latency).

---

### Slide 3: Mathematical Graph Formulation
- **Connectivity Graph $G = (V, E)$:** Edges where Euclidean distance $d(u, v) \le 500.0\text{ m}$ (inclusive).
- **Conflict Graph $G_{conflict} = G^2$:** Edges between all pairs with shortest path $\le 2$ hops.
- **Equivalence Theorem:** Distance-2 vertex coloring of $G$ is mathematically isomorphic to ordinary vertex coloring of $G^2$.
- **Complexity:** NP-hard in general; bounded by $\omega(G^2) \le \chi(G^2) \le \Delta(G^2) + 1$.

---

### Slide 4: Algorithmic Architecture & Heuristics
- **1. Largest-Degree-First (LDF / Welsh-Powell):** Colors high-degree conflict bottlenecks first; $\mathcal{O}(V \log V + E)$.
- **2. DSATUR (Degree of Saturation):** Dynamic greedy heuristic choosing vertex with maximum colored neighbor diversity; $\mathcal{O}(V^2 + E)$.
- **3. Smallest-Last (Degeneracy):** Matula-Beck ordering eliminating minimum-degree nodes; bounds coloring by graph degeneracy.
- **4. Randomized Restarts:** Evaluates $N=1000$ seeded random permutations to escape local minima.
- **5. Local Search & Color Reduction:** Kempe-chain 2-color swaps and min-conflicts Tabu search to eliminate highest color classes.

---

### Slide 5: Exact Solvers & Proof of Optimality
- **Dual-Solver Strategy:**
  - *Primary Solver:* Google OR-Tools CP-SAT (0-1 ILP with symmetry breaking).
  - *Fallback Solver:* Pure-Python DSATUR Branch-and-Bound Backtracking.
- **Symmetry Breaking:** Maximum clique $\omega(G^2)$ is pre-assigned fixed colors $0 \dots \omega-1$.
- **Lower Bound Pruning:** Search halts immediately once upper bound matches clique lower bound.
- **Performance:** Solves 16-node topologies in $< 0.5\text{ ms}$.

---

### Slide 6: Empirical Results & Benchmark Suite
- **4x4 Grid (300 m spacing):**
  - All heuristics found **9 slots** (verified exact optimum, 0 gap).
  - Four corners (Nodes 1, 4, 13, 16) all share Slot 8!
- **Sparse Linear Chain (350 m spacing):**
  - Requires exactly **3 slots** (repetition pattern: $1, 2, 0, 1, 2, 0\dots$).
- **Dense Cluster ($d \le 500$ m):**
  - Forms $K_{16}$ clique; requires **16 slots** (no spatial reuse possible).
- **Two Disconnected Clusters:**
  - Full spatial reuse across clusters; requires **8 slots** instead of 16.

---

### Slide 7: Independent Schedule Verifier
- **Design Principle:** Absolute separation of concerns—zero shared code with coloring or $G^2$ construction.
- **BFS Shortest-Path Checks:** Evaluates hop distances directly on physical graph $G$.
- **Assertions Enforced:**
  - Every node has exactly one slot (Coverage check).
  - Slots are contiguous $0 \dots K-1$ (Contiguity check).
  - No pairs within 1 or 2 hops share slots (Conflict freedom).
- **Outcome:** Catches deliberate collisions, missing nodes, and gaps; exits non-zero on failure.

---

### Slide 8: EMANE Emulation Bridge (Part 2)
- **High-Fidelity Virtual Testbed:** Integrates with EMANE `tdmaeventschedulerradiomodel`.
- **Profiles Created:**
  - 1 ms slot duration (`1000` $\mu\text{s}$), 50 $\mu\text{s}$ guard time.
  - 2.4 GHz carrier, 20 MHz bandwidth, 0 dBm transmit power.
- **Automated Translator (`schedule_to_emane.py`):**
  - Converts JSON schedule to native EMANE schedule XML.
  - Generates Python `emane.events.TDMAScheduleEvent` publisher script.
  - Round-trip validation test suite passes with 100% parity.

---

### Slide 9: Emulation Test Plan & Engineering Decisions
- **Emulation Verification Test Plan:**
  - *Valid Schedule:* Ping/iperf packets transmit strictly inside scheduled 1 ms slots at 9 ms intervals.
  - *Corrupted Schedule:* Overlapping transmissions in Slot 0 drop SINR below PCR threshold, triggering packet discards.
- **Key Engineering Decisions:**
  - Float epsilon ($10^{-9}$) ensures exact 500.0 m points are included.
  - Duplicate coordinate validation detects impossible physical co-locations.
  - Deterministic random seed ensures reproducible schedules.

---

### Slide 10: Conclusion & Future Roadmap
- **Key Takeaways:**
  - Fully working Python TDMA planner with 5 heuristics and 2 exact solvers.
  - 100% test coverage (42 pytest tests passing).
  - Full EMANE Docker container, XML configurations, and bridge scripts.
- **Future Enhancements:**
  - Multi-frequency TDMA (2D time-frequency grid).
  - Mobile ad-hoc networks with distributed scheduling (DRAND).
  - Directed link-based STDMA.
