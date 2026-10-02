# TDMA Schedule Planner and Spatial Reuse Optimizer: Engineering Design Document

**Author:** Athish M  
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

### 3.7 Considered but Not Implemented
- **Genetic Algorithms (GA):** Considered for global search, but stochastic evaluation offers no guarantee or proof of optimality, requires complex chromosome encodings for graph coloring, and cannot strictly enforce hard distance-2 constraints without auxiliary repair heuristics.
- **Simulated Annealing (SA):** Unconstrained energy formulations with conflict penalties require fragile temperature schedule tuning and frequently terminate with lingering violations, requiring secondary deterministic repair passes.
- **Plain ILP without Symmetry Breaking:** Standard 0-1 ILP formulations suffer from massive search tree expansion due to symmetric color permutations (any permutation of color indices represents an identical physical schedule). Adding maximum-clique pre-coloring breaks this symmetry by anchoring $\omega(G^2)$ colors upfront.

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

### 4.3 Why This Differs from the Brief's Illustrative Sample Output
The assignment brief provides an illustrative sample report showing `"Optimized Frame Length : 5 unique timeslots"`. The brief's sample shows 5 slots but does not give all coordinates, so it is treated as an illustrative format example, not a target. Our independent verifier is the correctness check.

**Mathematical Proof of Lower Bound:**
In the specified 4x4 grid topology with 300 m spacing and $R = 500.0\text{ m}$:
1. Adjacent nodes along rows and columns are separated by 300.0 m $\le 500.0\text{ m}$ (in range, distance 1).
2. Diagonal neighbors are separated by $\sqrt{300^2 + 300^2} \approx 424.26\text{ m} \le 500.0\text{ m}$ (in range, distance 1).
3. Any $3 \times 3$ subgrid (9 nodes, e.g., Nodes 1, 2, 3, 5, 6, 7, 9, 10, 11) has maximum hop distance 2 in $G$.
4. Consequently, all 9 nodes in any $3 \times 3$ block pairwise conflict, inducing a complete subgraph (clique) of size 9 in the conflict graph $G^2$: $\omega(G^2) \ge 9$.
5. By graph coloring fundamentals, the chromatic number is bounded below by the clique number:
   $$\chi(G^2) \ge \omega(G^2) = 9$$
Therefore, any schedule with fewer than 9 slots mathematically violates either a Distance-1 (direct collision) or Distance-2 (hidden terminal) invariant. Our independent BFS verifier confirms that **9 unique slots** is the true conflict-free global optimum.

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

### 6.3 Tested vs. Design-Only Scope
- **Tested Offline:** Automated schedule JSON transformation, NEM integer ID mapping, XML schedule generation, round-trip schema parsing, schedule-to-matrix parity assertion, and Python event script generation. Tested in pytest with 100% pass rate without requiring EMANE.
- **Design-Only:** Real-time over-the-air RF packet exchange inside the Linux kernel network stack using running EMANE daemons (due to requirement of root/kernel privileges and containerized environment).

| Parameter / Component | Category | Verified Name / Value | Exact Official URL | Quoted Official Documentation | Status |
| :--- | :--- | :--- | :--- | :--- | :---: |
| **MAC Model Library** | MAC Plugin | `tdmaeventschedulerradiomodel` | [tdmaradiomodel.xml.in](https://github.com/adjacentlink/emane/blob/master/src/models/mac/tdma/eventscheduler/tdmaradiomodel.xml.in) | `<mac library='tdmaeventschedulerradiomodel'>` | **VERIFIED** |
| **MAC Parameters vs Structure** | Architecture | Attributes of `<structure>`, not `<mac>` | [tdma-radio-model.txt](https://github.com/adjacentlink/emane-guide/blob/main/guide/tdma-radio-model.txt) | *"The TDMA structure defines: Slot size in microseconds, Slot overhead in microseconds, Number of slots per frame, Number of frames per multiframe, Transceiver bandwidth in Hz"* | **VERIFIED** |
| **MAC PCR Curve URI** | MAC Parameter | `pcrcurveuri` | [tdmaradiomodel.xml.in](https://github.com/adjacentlink/emane/blob/master/src/models/mac/tdma/eventscheduler/tdmaradiomodel.xml.in) | `<param name="pcrcurveuri" value='file://@datadir@/xml/models/mac/tdmaeventscheduler/tdmabasemodelpcr.xml'/>` | **VERIFIED** |
| **MAC Queue Controls** | MAC Parameters | `queue.depth`, `queue.aggregationenable`, etc. | [tdmaradiomodel.xml.in](https://github.com/adjacentlink/emane/blob/master/src/models/mac/tdma/eventscheduler/tdmaradiomodel.xml.in) | `<param name='queue.depth' value='255'/><param name='queue.aggregationenable' value='on'/><param name='queue.strictdequeueenable' value='off'/>` | **VERIFIED** |
| **Schedule XML Root** | XML Schema | `<emane-tdma-schedule>` | [tdmaschedule.xsd](https://github.com/adjacentlink/emane/blob/master/src/python/emane/events/schema/tdmaschedule.xsd) | `<xs:element name='emane-tdma-schedule'>` | **VERIFIED** |
| **Schedule Structure** | XML Element | `<structure frames='..' slots='..' slotoverhead='..' slotduration='..' bandwidth='..'/>` | [tdmaschedule.xsd](https://github.com/adjacentlink/emane/blob/master/src/python/emane/events/schema/tdmaschedule.xsd) | `<xs:element name="structure" minOccurs='0'><xs:attribute name='slotduration' type='xs:unsignedLong' use='required'/><xs:attribute name='slotoverhead' type='xs:unsignedLong' use='required'/>...` | **VERIFIED** |
| **Multiframe & Frames** | XML Elements | `<multiframe>` containing `<frame index='..'>` | [tdmaschedule.xsd](https://github.com/adjacentlink/emane/blob/master/src/python/emane/events/schema/tdmaschedule.xsd) | `<xs:element name="multiframe"><xs:complexType><xs:sequence><xs:element name="frame" maxOccurs="unbounded">` | **VERIFIED** |
| **Slot Allocation & Types** | XML Elements | `<slot index='..' nodes='..'>` with `<tx>`, `<rx>`, `<idle>` | [tdmaschedule.xsd](https://github.com/adjacentlink/emane/blob/master/src/python/emane/events/schema/tdmaschedule.xsd) | `<xs:element name="slot" maxOccurs="unbounded"><xs:attribute name='index' use='required'/><xs:attribute name='nodes' use='required'/><xs:choice minOccurs='0'><xs:element name="tx">...` | **VERIFIED** |
| **Schedule Injection Tool** | CLI Utility | `emaneevent-tdmaschedule` | [tdma-radio-model.txt](https://github.com/adjacentlink/emane-guide/blob/main/guide/tdma-radio-model.txt) | *"The emaneevent-tdmaschedule script can be used to process a TDMA Schedule XML file... $ emaneevent-tdmaschedule your-desired-schedule.xml -i lo"* | **VERIFIED** |
| **Python Event Class** | Python Class | `emane.events.TDMAScheduleEvent` | [tdmascheduleevent.py](https://github.com/adjacentlink/emane/blob/master/src/python/emane/events/tdmascheduleevent.py) | `class TDMAScheduleEvent(Event): IDENTIFIER = 105; def structure(self,**kwargs): ... def append(self,frameIndex,slotIndex,**kwargs):` | **VERIFIED** |
| **Python Event Publisher** | Python Class | `emane.events.EventService` | [eventservice.py](https://github.com/adjacentlink/emane/blob/master/src/python/emane/events/eventservice.py) | `class EventService: def __init__(self,eventchannel,otachannel = None): (self._multicastGroup,self._port,_) = eventchannel; def publish(self,nemId,event):` | **VERIFIED** |

### 6.4 Radio Propagation & Range Modeling (Design Only / Untested)
EMANE's TDMA scheduler radio model has no intrinsic knowledge of the discrete 500.0 m communication range constraint. In EMANE, which virtual radios hear each other is determined strictly by node locations and RF pathloss (location/pathloss events) combined with receiver sensitivity and antenna configuration.

To demonstrate spatial reuse in an emulation:
1. **Node Locations & Pathloss:** The emulation must place virtual radios at the exact coordinates defined in the Python topology input using `emane.events.LocationEvent` (Event ID 100) or by publishing explicit pathloss matrices via `emane.events.PathlossEvent` (Event ID 101).
2. **Effective Range Calibration:** The physical layer's transmit power (`txpower = 0.0 dBm`), pathloss model (`propagationmodel = freespace` or `2ray`), and Packet Completion Rate curve (`tdmabasemodelpcr.xml`) must be configured so that the received SINR drops below the decoding threshold at distances exceeding approximately 500.0 meters.
3. **Collision Risk Under Global Visibility:** If the emulation were executed without location/pathloss events or with an uncalibrated propagation model, all 16 virtual radios would hear one another globally across the multicast OTA channel (`224.1.2.8:45703`). Under global visibility, concurrent transmissions scheduled for nodes separated by $\ge 3$ hops (e.g., Node_01 and Node_04 sharing Slot 8 in the 4x4 grid) would collide at the PHY layer, causing packet drops that the graph model proves should not occur.

*Status: DESIGN ONLY / UNTESTED. Offline XML schedule translation and schema parity are fully tested; live RF propagation tuning and packet-level slot enforcement have not been executed on a live Linux kernel testbed.*

### 6.5 Bridge Design and Planned Test Plan (Not Yet Run)
1. **XML Schedule Translation:**
   Each node's timeslot assignment from the optimizer is mapped into an EMANE `<slot>` entry. Transmitting nodes are tagged with `<tx>` containing their 1-based NEM identifier (`nodes="1,4,13,16"`), while non-transmitting nodes default to receive mode (`<rx>`).
2. **Schedule Injection:**
   The schedule is either loaded at initialization via `<param name='schedule' value='schedule.xml'/>` or published dynamically onto the EMANE event channel (`224.1.2.8:45703`) using `emaneevent-tdmaschedule` or Python `emane.events.EventService.publish()`.
3. **Planned Verification Observations:**
   - *Valid Schedule:* In a planned emulation run, ping and iperf streams between nodes should observe packet transmissions occurring strictly inside allocated 1.0 ms slots at repeating frame intervals, with zero packet loss between collision-free transmitters.
   - *Deliberately Conflicting Schedule:* Forcing two nodes within 2 hops to share a slot should produce simultaneous transmissions that overlap at the shared receiver, resulting in low SINR, PCR curve packet discards, and measurable loss.
   - *Range Calibration:* Pathloss and antenna parameters should be calibrated so received power beyond ~500 m drops below the receiver sensitivity threshold, demonstrating physical spatial reuse without false collisions.

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
