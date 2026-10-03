# TDMA Schedule Optimizer

This tool schedules radio nodes into TDMA timeslots using distance-2 graph colouring, allowing radios that are 3 or more hops apart to safely share slots through spatial reuse. On a 16-node 4x4 grid at 300 m spacing with a 500 m communication range, the optimizer produces a 9-slot schedule, which is the mathematically proven minimum.

## Results at a Glance

| Topology | Nodes | Range | G Edges | G² Edges | Slots |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 4×4 Grid | 16 | 500 m | 42 | 90 | 9 |
| Sparse Linear | 16 | 500 m | 15 | 29 | 3 |
| Dense Cluster | 16 | 500 m | 120 | 120 | 16 |
| Disconnected Clusters | 16 | 500 m | 56 | 56 | 8 |

All five heuristics matched the exact optimum across every benchmark topology.

## Quick Start

Requires Python 3.10 or newer (tested on Python 3.14).

```bash
pip install -r requirements.txt
pip install -e .
python -m tdma.cli --coords-file examples/grid_4x4_300m.json
python -m pytest -q
```

The editable install (`pip install -e .`) registers the package so the CLI and test suite resolve imports cleanly. The test suite runs 47 tests and takes a few seconds.

## Usage

| Option | Description |
| :--- | :--- |
| `--coords` | Inline JSON string of node coordinates |
| `--coords-file` | Path to JSON file containing node coordinates |
| `--range` | Communication range in meters (default: 500.0) |
| `--seed` | Random seed for tie-breaking and randomized restarts |
| `--compare` | Compare all five heuristics against exact solvers with runtimes |
| `--export-json` | Export the verified schedule and coordinates to a JSON file |
| `--plot` | Generate a 2D connectivity and slot assignment diagram |
| `--force-pure-python-exact` | Force pure Python exact backtracking solver instead of OR-Tools |

Inline coordinate input:

Bash, Git Bash, Linux, macOS:
```bash
python -m tdma.cli --coords '{"A": [0, 0], "B": [300, 0], "C": [600, 0]}'
```

Windows PowerShell (double quotes must be escaped):
```powershell
python -m tdma.cli --coords '{\"A\": [0, 0], \"B\": [300, 0], \"C\": [600, 0]}'
```

On Windows, using `--coords-file` avoids shell quoting problems entirely.

Output on the 4x4 grid example:
```
NODE -> SLOT ASSIGNMENTS:
 Node_01: Slot 8    Node_05: Slot 6    Node_09: Slot 7    Node_13: Slot 8
 Node_02: Slot 4    Node_06: Slot 0    Node_10: Slot 2    Node_14: Slot 4
 Node_03: Slot 5    Node_07: Slot 1    Node_11: Slot 3    Node_15: Slot 5
 Node_04: Slot 8    Node_08: Slot 6    Node_12: Slot 7    Node_16: Slot 8

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
```

## How It Works

The optimizer models physical connectivity as a unit-disk graph G where radios within 500 m share an edge. It squares G to produce conflict graph G², where an edge connects any pair separated by 1 or 2 hops. Standard vertex colouring on G² directly solves distance-2 colouring: direct neighbours and hidden terminals receive different slots, while pairs 3 or more hops apart can reuse the same slot. The three greedy heuristics take well under a millisecond on 16 nodes; 1000 random restarts and local search take tens of milliseconds. An exact CP-SAT solver (with pure Python branch-and-bound fallback) computes the global optimum. Before output, an independent BFS-based verifier checks distance-1 and distance-2 constraints. See [docs/design.pdf](docs/design.pdf) for mathematical proofs and benchmark analysis.

## Repository Layout

```
tdma-schedule-optimizer/
  README.md           # Project documentation and quick start guide
  pyproject.toml      # Build metadata and pytest configuration
  requirements.txt    # Python runtime and optional dependencies
  .gitignore          # Git exclusion rules for caches and artifacts
  src/tdma/           # Graph builder, heuristics, exact solver, report, and CLI
  tests/              # 47 unit, property, and bridge test cases
  examples/           # Sample topology JSON files and verified grid schedule
  emane/              # EMANE emulation configs, Dockerfile, and translation bridge
  docs/               # Design report PDF and slide deck PPTX
  tools/              # Scripts to regenerate design.pdf and presentation.pptx
```

## Part 2 (EMANE)

The EMANE bridge translates optimizer schedules into EMANE's event-driven TDMA XML format. Tested offline: schedule JSON to EMANE XML conversion, event publisher script generation, and XML round-trip parsing validation. Not run: live multi-node emulation inside containers, real-time TAP traffic, and kernel-level packet enforcement. See [emane/README.md](emane/README.md) for details.

## Documents

- [docs/design.pdf](docs/design.pdf): Full design report with mathematical proofs, benchmark analysis, and architecture notes.
- [docs/presentation.pptx](docs/presentation.pptx): 8-slide widescreen presentation deck walking through formulation, results, and proof of optimality.

## Author

Athish M (athishm2007@gmail.com)
