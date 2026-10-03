# Presentation Outline: TDMA Schedule Planner and Spatial Reuse Optimizer

**Target Audience:** Wireless Protocol Development Team & Systems Engineers  
**Duration:** 15–20 minutes  
**Format:** 8 Slides (16:9 Widescreen, 13.333 × 7.5 in)  
**Presenter:** Athish M (athishm2007@gmail.com)  

---

### Slide 1: Packing a radio network into the fewest time slots
- **Design:** Dark background (#1B1F2A), Georgia title, thin amber rule.
- **Content:** Title, presenter name, one short line describing the scope.
- **Visual Motif:** 16 dots in a 4×4 layout on the right, colored by the real slot assignment from `grid_schedule.json`.
- **Spoken Script (First Person):** Introduction to the TDMA scheduling problem, the goal of minimizing frame length K, and an overview of the graph squaring technique, heuristics, exact proofs, and EMANE bridge.

---

### Slide 2: Why two radios can't talk at once
- **Design:** Paper background (#F6F3EC), thin hairline rule under title.
- **Statement:** "A and C can't hear each other, but both reach B, so their signals collide there."
- **Visual:** Full-width native diagram showing radios A, B, and C with direct link arrows and an "out of range" dashed connection between A and C.
- **Spoken Script:** Explanation of direct distance-1 collisions and distance-2 hidden terminal collisions, establishing why radios sharing a neighbor cannot share a slot.

---

### Slide 3: My trick: square the graph
- **Design:** Paper background, thin hairline rule.
- **Statement:** "Coloring G² is the same as a conflict-free schedule, and nodes 3+ hops apart stay unconnected so they can share a slot."
- **Visual:** Vertically stacked diagrams of a 5-node line: physical graph G on top, amber "Square it" transition, and squared conflict graph G² below with separate 2-hop arcs.
- **Spoken Script:** Walkthrough of graph squaring as an algebraic equivalence to distance-2 coloring, showing how 3+ hop separation preserves slot reuse.

---

### Slide 4: What I tried, in order
- **Design:** Paper background, single hairline table without background fills.
- **Table Data:** Real performance numbers across 6 methods on the 4×4 grid:
  - Greedy by degree (Welsh-Powell): 9 slots, 0.06 ms
  - DSATUR (Saturation greedy): 9 slots, 0.15 ms
  - Smallest-last (Degeneracy order): 9 slots, 0.20 ms
  - 1000 random restarts: 9 slots, 24.2 ms
  - Local search with Kempe swaps: 9 slots, 60.8 ms
  - Exact solver (CP-SAT): 9 slots, 0.60 ms
- **Takeaway Line:** "All five reached 9, so I added an exact solver to find out whether 9 is the best possible."
- **Spoken Script:** First-person narrative describing the progression from greedy heuristics to restarts, local search, and exact constraint solving.

---

### Slide 5: The result on the 4x4 grid
- **Design:** Split layout. Dark terminal panel on the left; clean 4×4 grid diagram on the right.
- **Terminal Panel:** Consolas text showing the real CLI output: node-to-slot assignments and slot-by-node boolean matrix.
- **Grid Visual:** 16 nodes arranged on the physical grid, colored by timeslot, with the four corner nodes (Nodes 1, 4, 13, 16) ringed in amber to highlight spatial reuse in Slot 8.
- **Spoken Script:** Detailed walkthrough of the 4×4 grid schedule, confirming every node's slot assignment and explaining corner spatial reuse across the 900 m span.

---

### Slide 6: Why 9 is the best possible
- **Design:** Large number callout ("9") on the left; 4×4 grid diagram with an amber-highlighted 3×3 subgrid on the right.
- **Points:**
  - In range at 424 m diagonal (300√2 m ≤ 500 m).
  - Every pair in any 3×3 block is within 2 hops in G.
  - That forms a 9-clique in G², forcing 9 distinct slots.
- **Note:** "The brief's sample shows 5 slots. Node_01 and Node_03 are 600 m apart, but Node_02 hears both, so the distance-2 rule says they can't share a slot."
- **Spoken Script:** Mathematical proof showing that any 3×3 block forms a 9-clique in G², proving 9 slots is the global optimum.

---

### Slide 7: Four topologies, same story
- **Design:** Split layout. Native clustered bar chart on the left; single hairline table on the right.
- **Chart & Table:** Exact optimum vs best heuristic across 4 topologies:
  - 4×4 Grid: 42 G edges, 90 G² edges, 9 slots
  - Sparse Linear: 15 G edges, 29 G² edges, 3 slots
  - Dense Cluster: 120 G edges, 120 G² edges, 16 slots
  - Two Clusters: 56 G edges, 56 G² edges, 8 slots
- **Takeaway Line:** "At 16 nodes plain greedy already finds the optimum, so the exact solver is how I know it."
- **Spoken Script:** Analysis of topology density, complete clique behavior in dense clusters, and multi-cluster spatial reuse.

---

### Slide 8: Part 2 and what's left
- **Design:** Native 5-box horizontal pipeline (Optimizer → JSON → Bridge → XML → EMANE) with three clean lines below.
- **Pipeline Labels:** Optimizer, JSON, Bridge, and XML labeled "tested offline"; EMANE labeled "not run".
- **Points:**
  - EMANE needs pathloss calibrated to about 500 m, or all 16 radios hear each other.
  - Next step is running the container with virtual TAP interfaces and live traffic.
  - Future work covers joint time-frequency coloring and dynamic mobile topologies.
- **Spoken Script:** Transparent boundary discussion between offline XML translation and live kernel emulation, detailing physical propagation setup and future directions.
