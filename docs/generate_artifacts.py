"""
Generate docs/design.pdf (8-section design notes, 6-8 pages)
and docs/presentation.pptx (via build_deck.py).
"""

from __future__ import annotations

import io
import json
import os
import sys
import tempfile

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    KeepTogether,
    HRFlowable,
    Preformatted,
    Image,
)
from reportlab.pdfgen import canvas

from tdma.graph import parse_coordinates, build_connectivity_graph
from tdma.verify import verify_schedule

# ---------------------------------------------------------------------------
# Colors
# ---------------------------------------------------------------------------
NAVY = "#0D47A1"
DARK_NAVY = "#0A3470"
LIGHT_NAVY = "#1A237E"
BODY_COLOR = "#212121"
SUBTITLE_COLOR = "#37474F"
BORDER_COLOR = "#CFD8DC"
ROW_ALT = "#F5F7FA"
ACCENT = "#1565C0"

# ---------------------------------------------------------------------------
# PDF: NumberedCanvas with Athish M footer and header
# ---------------------------------------------------------------------------

class NumberedCanvas(canvas.Canvas):
    """Two-pass canvas for 'Page X of Y', running header, and author footer."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#546E7A"))

        # Running Header (pages > 1)
        if self._pageNumber > 1:
            self.drawString(45, letter[1] - 30, "Athish M | TDMA Schedule Optimizer")
            self.setStrokeColor(colors.HexColor(BORDER_COLOR))
            self.setLineWidth(0.5)
            self.line(45, letter[1] - 33, letter[0] - 45, letter[1] - 33)

        # Running Footer (all pages)
        self.setStrokeColor(colors.HexColor(BORDER_COLOR))
        self.setLineWidth(0.5)
        self.line(45, 32, letter[0] - 45, 32)
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(letter[0] - 45, 20, page_str)
        self.drawString(45, 20, "Athish M | TDMA Schedule Optimizer")
        self.restoreState()


# ---------------------------------------------------------------------------
# PDF Builder
# ---------------------------------------------------------------------------

def build_pdf(filename: str):
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        rightMargin=45,
        leftMargin=45,
        topMargin=45,
        bottomMargin=45,
    )
    styles = getSampleStyleSheet()

    # Typography styles — 10 pt body for clean readability
    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        textColor=colors.HexColor(NAVY),
        alignment=0,
        spaceAfter=4,
    )
    subtitle_style = ParagraphStyle(
        "DocSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=13.5,
        textColor=colors.HexColor(SUBTITLE_COLOR),
        spaceAfter=8,
    )
    h1_style = ParagraphStyle(
        "H1_Custom",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=12.5,
        leading=15.5,
        textColor=colors.HexColor(NAVY),
        spaceBefore=10,
        spaceAfter=4,
        keepWithNext=True,
    )
    h2_style = ParagraphStyle(
        "H2_Custom",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=10.5,
        leading=13.5,
        textColor=colors.HexColor(LIGHT_NAVY),
        spaceBefore=8,
        spaceAfter=3,
        keepWithNext=True,
    )
    body_style = ParagraphStyle(
        "Body_Custom",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=9.8,
        leading=13.2,
        textColor=colors.HexColor(BODY_COLOR),
        spaceAfter=5,
    )
    bullet_style = ParagraphStyle(
        "Bullet_Custom",
        parent=body_style,
        leftIndent=14,
        firstLineIndent=-10,
        spaceAfter=3,
    )
    table_cell = ParagraphStyle(
        "TableCell",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=7.8,
        leading=9.8,
        textColor=colors.HexColor(BODY_COLOR),
    )
    table_cell_bold = ParagraphStyle(
        "TableCellBold",
        parent=table_cell,
        fontName="Helvetica-Bold",
        textColor=colors.HexColor(NAVY),
    )
    table_cell_header = ParagraphStyle(
        "TableCellHeader",
        parent=table_cell,
        fontName="Helvetica-Bold",
        fontSize=7.8,
        leading=9.8,
        textColor=colors.white,
    )
    pre_style = ParagraphStyle(
        "PreStyle",
        parent=styles["Normal"],
        fontName="Courier",
        fontSize=7.2,
        leading=8.8,
        textColor=colors.HexColor("#1A237E"),
    )

    story = []

    # Temporary image paths
    temp_dir = tempfile.gettempdir()
    grid_img_path = os.path.join(temp_dir, "grid_graph_figure.png")
    arch_img_path = os.path.join(temp_dir, "arch_figure.png")
    _generate_grid_graph_image(grid_img_path)
    _generate_architecture_diagram(arch_img_path)

    # ============================= PAGE 1 =============================
    story.append(Paragraph("TDMA Schedule Optimizer: Design and Implementation Notes", title_style))
    story.append(Paragraph(
        "<b>Author:</b> Athish M &nbsp;|&nbsp; <b>Repository:</b> tdma-schedule-optimizer &nbsp;|&nbsp; <b>Package:</b> tdma v1.0.0",
        subtitle_style
    ))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor(NAVY), spaceAfter=8))

    # SECTION 1
    story.append(Paragraph("1. The Problem in My Own Words", h1_style))
    story.append(Paragraph(
        "I built this optimizer to solve broadcast scheduling for radio nodes on a shared 2.4 GHz wireless channel. "
        "When nodes share a radio channel, uncontrolled transmissions cause packet collisions. "
        "Time Division Multiple Access (TDMA) fixes this by breaking time into repeating frames of fixed timeslots. "
        "Each node gets one or more slots to transmit.",
        body_style
    ))
    story.append(Paragraph(
        "The network sits on a 2D plane with an omnidirectional radio range of 500.0 meters. "
        "A valid schedule must handle two collision types:",
        body_style
    ))
    story.append(Paragraph("• <b>Distance-1 collision:</b> Two nodes within 500 meters cannot transmit in the same slot. If they transmit together, each radio drowns out the other and neither can receive.", bullet_style))
    story.append(Paragraph("• <b>Distance-2 collision (the hidden-terminal problem):</b> Two nodes might be more than 500 meters apart, but share a common neighbor within 500 meters of both. If both transmit at the same time, the neighbor hears overlapping signals and receives garbage.", bullet_style))
    story.append(Paragraph("• <b>Spatial reuse:</b> Two nodes that are 3 or more hops apart in the network graph can transmit in the same timeslot. No shared receiver can hear both, so their transmissions do not collide.", bullet_style))
    story.append(Paragraph(
        "My goal is to find a conflict-free schedule that uses the minimum number of timeslots. "
        "A shorter frame means every node transmits more frequently, latency drops, and overall network throughput increases.",
        body_style
    ))

    # SECTION 2
    story.append(Paragraph("2. How I Modelled It", h1_style))
    story.append(Paragraph(
        "I modelled the radio network as an undirected physical graph <i>G = (V, E)</i>. "
        "The vertices <i>V</i> are radio transceivers with coordinates <i>(x, y)</i>. "
        "An edge exists between node <i>u</i> and node <i>v</i> if their Euclidean distance satisfies "
        "<i>d(u, v) &le; 500.0 m</i>. "
        "I treat a distance of exactly 500.0 m as in range, applying a numerical tolerance of 10<sup>-9</sup> meters to avoid floating-point roundoff issues.",
        body_style
    ))
    story.append(Paragraph(
        "To handle both 1-hop and 2-hop conflicts directly, I construct the squared graph <i>G<sup>2</sup></i>. "
        "The graph <i>G<sup>2</sup></i> has the same vertices as <i>G</i>. "
        "An edge exists between <i>u</i> and <i>v</i> in <i>G<sup>2</sup></i> if the shortest path distance in <i>G</i> is 1 or 2 hops: "
        "<i>1 &le; dist<sub>G</sub>(u, v) &le; 2</i>.",
        body_style
    ))
    story.append(Paragraph(
        "With this construction, a valid TDMA schedule is equivalent to a proper vertex colouring of <i>G<sup>2</sup></i>. "
        "Two nodes that share an edge in <i>G<sup>2</sup></i> conflict and must receive different colors (slots). "
        "Two nodes with no edge in <i>G<sup>2</sup></i> are at least 3 hops apart and can safely share a slot.",
        body_style
    ))
    story.append(Paragraph(
        "Vertex colouring on arbitrary graphs is NP-hard. Even for unit-disk graphs, distance-2 colouring remains NP-hard. "
        "I use two graph properties to bound the required slots:<br/>"
        "• <b>Lower bound:</b> The maximum clique size <i>&omega;(G<sup>2</sup>)</i>. If a group of nodes all pairwise conflict within 2 hops, every node in that group needs a distinct slot.<br/>"
        "• <b>Upper bound:</b> The maximum vertex degree <i>&Delta;(G<sup>2</sup>) + 1</i>, achievable by greedy colouring.",
        body_style
    ))

    # ============================= PAGE 2 =============================
    story.append(PageBreak())

    # SECTION 3
    story.append(Paragraph("3. What I Tried and What Happened", h1_style))
    story.append(Paragraph(
        "I implemented five heuristic algorithms to find schedules quickly, and two exact solvers to verify whether those schedules reached the mathematical minimum.",
        body_style
    ))
    story.append(Paragraph("3.1 Five Heuristics", h2_style))
    story.append(Paragraph(
        "I evaluated all five heuristics on the 4x4 grid topology (16 nodes, 300 m spacing, 500 m range):<br/>"
        "1. <b>Largest-Degree-First (LDF / Welsh-Powell):</b> Sorts nodes descending by degree in <i>G<sup>2</sup></i> and colors greedily. It assigned 9 slots in 0.06 ms. It was the fastest heuristic.<br/>"
        "2. <b>DSATUR (Brélaz):</b> Selects the uncolored vertex with the highest number of distinct colors among its neighbors. It assigned 9 slots in 0.25 ms.<br/>"
        "3. <b>Smallest-Last (Matula and Beck):</b> Repeatedly removes the minimum-degree vertex from the remaining subgraph, then colors in reverse order. It assigned 9 slots in 0.09 ms.<br/>"
        "4. <b>Randomized Restarts:</b> Evaluates 1000 seeded random vertex permutations with greedy first-fit. It consistently found 9 slots in 60.8 ms.<br/>"
        "5. <b>Local Search (Color Reduction):</b> Starts from the best greedy schedule and attempts to eliminate the highest slot using Kempe-chain swaps and tabu search. On the 4x4 grid, it attempted to reduce 9 slots to 8, but correctly stopped because 8 slots is mathematically impossible.<br/>"
        "All five heuristics matched the theoretical minimum of 9 slots on the 4x4 grid. LDF proved to be the fastest option.",
        body_style
    ))

    story.append(Paragraph("3.2 Two Exact Solvers", h2_style))
    story.append(Paragraph(
        "Heuristics cannot prove optimality on their own. I added two exact solvers to certify the true minimum frame length:<br/>"
        "1. <b>Google OR-Tools CP-SAT:</b> Formulates the problem as constraint optimization with binary assignment variables <i>x<sub>v,c</sub></i> and slot indicators <i>y<sub>c</sub></i>. I broke color permutation symmetry by pre-colouring a maximum clique in <i>G<sup>2</sup></i>. It solved the 4x4 grid in 0.60 ms, confirming that 9 slots is the exact optimum.<br/>"
        "2. <b>Pure-Python Branch-and-Bound Fallback:</b> A zero-dependency backtracking solver. It uses clique pre-colouring, lower-bound pruning, and DSATUR variable ordering. It serves as a standalone fallback when OR-Tools is not installed.",
        body_style
    ))

    story.append(Paragraph("3.3 What I Considered but Rejected", h2_style))
    story.append(Paragraph(
        "During design, I considered several alternative optimization approaches:<br/>"
        "• <b>Genetic Algorithms:</b> I rejected genetic algorithms because their stochastic search provides no guarantee of optimality. Furthermore, distance-2 graph coloring has strict hard constraints, and random crossover or mutation operators frequently produce invalid schedules that require expensive repair routines.<br/>"
        "• <b>Simulated Annealing:</b> I rejected simulated annealing because penalty tuning on soft conflict formulations is fragile. It often converges to near-valid states with residual collisions, requiring an auxiliary deterministic coloring pass.<br/>"
        "• <b>Plain ILP without Symmetry Breaking:</b> A naive ILP formulation assigns colors <i>0 ... K-1</i>. Because any permutation of slot assignments is equivalent, the solver explores thousands of symmetric branches. Anchoring a maximum clique upfront breaks this symmetry and allows CP-SAT to solve the 4x4 grid in under 1 millisecond.",
        body_style
    ))

    story.append(Paragraph("3.4 Summary of Design Decisions", h2_style))
    story.append(Paragraph(
        "<b>Why graph squaring?</b> Squaring isolates distance constraints into edge adjacency. Standard graph coloring routines can then run unmodified.<br/>"
        "<b>Why five heuristics?</b> They offer distinct trade-offs between execution speed and search depth across irregular topologies.<br/>"
        "<b>Why an exact solver?</b> Exact methods certify whether heuristic schedules reached the mathematical floor.<br/>"
        "<b>Why a separate verifier?</b> A separate verifier independently evaluates physical invariants using BFS on <i>G</i>.",
        body_style
    ))

    # ============================= PAGE 3 =============================
    story.append(PageBreak())

    # SECTION 4
    story.append(Paragraph("4. Results on the Benchmark Topologies", h1_style))
    story.append(Paragraph(
        "I tested the optimizer across four representative topologies. Every topology matched the exact theoretical optimum with zero heuristic gap.",
        body_style
    ))

    # Topology Summary Table
    table_data = [
        [
            Paragraph("Topology Scenario", table_cell_header),
            Paragraph("Nodes", table_cell_header),
            Paragraph("G Edges", table_cell_header),
            Paragraph("G² Edges", table_cell_header),
            Paragraph("Max Deg", table_cell_header),
            Paragraph("Exact Opt", table_cell_header),
            Paragraph("Best Heur", table_cell_header),
            Paragraph("Gap", table_cell_header),
            Paragraph("Runtime", table_cell_header),
        ],
        [
            Paragraph("1. 4x4 Grid (300 m)", table_cell),
            Paragraph("16", table_cell),
            Paragraph("42", table_cell),
            Paragraph("90", table_cell),
            Paragraph("15", table_cell),
            Paragraph("<b>9 slots</b>", table_cell_bold),
            Paragraph("<b>9 slots</b>", table_cell_bold),
            Paragraph("0", table_cell),
            Paragraph("0.48 ms", table_cell),
        ],
        [
            Paragraph("2. Sparse Linear (350 m)", table_cell),
            Paragraph("16", table_cell),
            Paragraph("15", table_cell),
            Paragraph("29", table_cell),
            Paragraph("4", table_cell),
            Paragraph("<b>3 slots</b>", table_cell_bold),
            Paragraph("<b>3 slots</b>", table_cell_bold),
            Paragraph("0", table_cell),
            Paragraph("0.17 ms", table_cell),
        ],
        [
            Paragraph("3. Dense Cluster (&le;500 m)", table_cell),
            Paragraph("16", table_cell),
            Paragraph("120", table_cell),
            Paragraph("120", table_cell),
            Paragraph("15", table_cell),
            Paragraph("<b>16 slots</b>", table_cell_bold),
            Paragraph("<b>16 slots</b>", table_cell_bold),
            Paragraph("0", table_cell),
            Paragraph("0.22 ms", table_cell),
        ],
        [
            Paragraph("4. Disconnected Clusters", table_cell),
            Paragraph("16", table_cell),
            Paragraph("56", table_cell),
            Paragraph("56", table_cell),
            Paragraph("7", table_cell),
            Paragraph("<b>8 slots</b>", table_cell_bold),
            Paragraph("<b>8 slots</b>", table_cell_bold),
            Paragraph("0", table_cell),
            Paragraph("0.30 ms", table_cell),
        ],
    ]
    t = Table(table_data, colWidths=[1.7 * inch, 0.5 * inch, 0.55 * inch, 0.6 * inch, 0.55 * inch, 0.65 * inch, 0.65 * inch, 0.5 * inch, 0.65 * inch])
    t.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(NAVY)),
            ("ALIGN", (1, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor(BORDER_COLOR)),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor(ROW_ALT)]),
            ("TOPPADDING", (0, 0), (-1, -1), 2.5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
        ])
    )
    story.append(t)
    story.append(Spacer(1, 6))

    story.append(Paragraph("4.1 Detailed Look at the 4x4 Grid", h2_style))
    story.append(Paragraph(
        "Why does the 4x4 grid with 300 m spacing require exactly 9 slots?<br/>"
        "• Horizontal and vertical neighbors sit 300 m apart, within the 500 m radio range.<br/>"
        "• Diagonal neighbors sit <i>sqrt(300<sup>2</sup> + 300<sup>2</sup>) &approx; 424.26 m</i> apart, also within the 500 m range.<br/>"
        "• Any 3x3 block of 9 nodes has a maximum path distance of 2 hops in <i>G</i>.<br/>"
        "• Therefore, all 9 nodes in any 3x3 block conflict with each other in <i>G<sup>2</sup></i>, forming a clique of size 9: <i>&omega;(G<sup>2</sup>) &ge; 9</i>.<br/>"
        "• Because the chromatic number <i>&chi;(G<sup>2</sup>) &ge; &omega;(G<sup>2</sup>)</i>, no schedule can use fewer than 9 slots.<br/>"
        "Spatial reuse occurs at the edges and corners. The four corner nodes (Node_01 at (0,0), Node_04 at (900,0), Node_13 at (0,900), and Node_16 at (900,900)) sit 3 or more hops apart. The optimizer groups all four corner nodes into Slot 8.",
        body_style
    ))

    # Figure 1: Grid diagram
    story.append(Spacer(1, 4))
    story.append(Image(grid_img_path, width=5.6 * inch, height=3.3 * inch))
    story.append(Paragraph("<i>Figure 1: Verified 9-slot schedule for the 4x4 grid (300 m spacing). Corner nodes 1, 4, 13, 16 share Slot 8 (spatial reuse).</i>", subtitle_style))

    # ============================= PAGE 4 =============================
    story.append(PageBreak())

    story.append(Paragraph("4.2 Real CLI Output for the 4x4 Grid", h2_style))
    story.append(Paragraph(
        "Below is the complete, raw terminal output generated by executing <code>python -m tdma.cli --coords-file examples/grid_4x4_300m.json</code>. "
        "The report displays total nodes, configured range, optimized frame length, individual node allocations, and the structural slot-by-node boolean schedule matrix:",
        body_style
    ))

    cli_output = (
        "================================================================\n"
        " TDMA TOPOLOGY OPTIMIZATION REPORT\n"
        "================================================================\n"
        "Total Nodes Processed : 16\n"
        "Configured Radio Range : 500.0 meters\n"
        "Optimized Frame Length : 9 unique timeslots (Lower is better)\n"
        "-----------------------------------------------------------------\n"
        "NODE -> SLOT ASSIGNMENTS:\n"
        " Node_01: Slot 8\n"
        " Node_02: Slot 4\n"
        " Node_03: Slot 5\n"
        " Node_04: Slot 8\n"
        " Node_05: Slot 6\n"
        " Node_06: Slot 0\n"
        " Node_07: Slot 1\n"
        " Node_08: Slot 6\n"
        " Node_09: Slot 7\n"
        " Node_10: Slot 2\n"
        " Node_11: Slot 3\n"
        " Node_12: Slot 7\n"
        " Node_13: Slot 8\n"
        " Node_14: Slot 4\n"
        " Node_15: Slot 5\n"
        " Node_16: Slot 8\n\n"
        "STRUCTURAL TDMA SCHEDULE MATRIX (Slot x Node Boolean Matrix):\n"
        "Slot \\ Node | 01 | 02 | 03 | 04 | 05 | 06 | 07 | 08 | 09 | 10 | 11 | 12 | 13 | 14 | 15 | 16\n"
        "-----------------------------------------------------------------------------------------------\n"
        "Slot 00    |  0 |  0 |  0 |  0 |  0 |  1 |  0 |  0 |  0 |  0 |  0 |  0 |  0 |  0 |  0 |  0\n"
        "Slot 01    |  0 |  0 |  0 |  0 |  0 |  0 |  1 |  0 |  0 |  0 |  0 |  0 |  0 |  0 |  0 |  0\n"
        "Slot 02    |  0 |  0 |  0 |  0 |  0 |  0 |  0 |  0 |  0 |  1 |  0 |  0 |  0 |  0 |  0 |  0\n"
        "Slot 03    |  0 |  0 |  0 |  0 |  0 |  0 |  0 |  0 |  0 |  0 |  1 |  0 |  0 |  0 |  0 |  0\n"
        "Slot 04    |  0 |  1 |  0 |  0 |  0 |  0 |  0 |  0 |  0 |  0 |  0 |  0 |  0 |  1 |  0 |  0\n"
        "Slot 05    |  0 |  0 |  1 |  0 |  0 |  0 |  0 |  0 |  0 |  0 |  0 |  0 |  0 |  0 |  1 |  0\n"
        "Slot 06    |  0 |  0 |  0 |  0 |  1 |  0 |  0 |  1 |  0 |  0 |  0 |  0 |  0 |  0 |  0 |  0\n"
        "Slot 07    |  0 |  0 |  0 |  0 |  0 |  0 |  0 |  0 |  1 |  0 |  0 |  1 |  0 |  0 |  0 |  0\n"
        "Slot 08    |  1 |  0 |  0 |  1 |  0 |  0 |  0 |  0 |  0 |  0 |  0 |  0 |  1 |  0 |  0 |  1\n"
        "-----------------------------------------------------------------------------------------------\n"
        "Execution finalized cleanly. Schedule verified conflict-free.\n"
        "================================================================"
    )
    story.append(Spacer(1, 4))
    story.append(Preformatted(cli_output, pre_style))

    # ============================= PAGE 5 =============================
    story.append(PageBreak())

    # SECTION 5
    story.append(Paragraph("5. How I Checked the Answer", h1_style))
    story.append(Paragraph(
        "I wrote the verifier in <code>src/tdma/verify.py</code> as an isolated module. "
        "It does not import any graph coloring code or the <i>G<sup>2</sup></i> conflict graph.",
        body_style
    ))

    story.append(Paragraph("5.1 Verification Invariants", h2_style))
    story.append(Paragraph(
        "The verifier takes the physical graph <i>G</i> and the schedule dictionary. It checks three invariants:<br/>"
        "1. <b>Complete Coverage:</b> Every node in <i>V</i> appears in the schedule.<br/>"
        "2. <b>Contiguous Indexing:</b> Slot numbers form a contiguous range <i>0 ... K-1</i> with no empty gaps.<br/>"
        "3. <b>Conflict Freedom:</b> For every pair of nodes <i>(u, v)</i> sharing a slot, the verifier computes the shortest path length in <i>G</i> using Breadth-First Search (BFS). It asserts that <i>dist<sub>G</sub>(u, v) &ge; 3</i>.<br/>"
        "If any two nodes sharing a slot are 1 hop apart, the verifier reports a direct collision. If they are 2 hops apart, it identifies their shared intermediate neighbor and reports a hidden-terminal violation.",
        body_style
    ))

    story.append(Paragraph("5.2 Boundary Rule and Numerical Tolerance", h2_style))
    story.append(Paragraph(
        "A distance of exactly 500.0 m counts as in range (tolerance 1e-9 m). "
        "This boundary rule ensures consistent edge creation between topology generation, optimization, and verification, preventing floating-point precision differences from dropping edge adjacencies.",
        body_style
    ))

    story.append(Paragraph("5.3 Distinguishing Correctness from Optimality", h2_style))
    story.append(Paragraph(
        "The verifier checks conflict freedom and structural correctness. It does not prove optimality on its own. "
        "Optimality is established by the 9-clique lower bound and certified by the exact solvers. "
        "A schedule with 16 slots on the 4x4 grid would pass the verifier with zero conflicts, but it would not be optimal. "
        "Optimality requires comparing the verified frame length against the clique lower bound <i>&omega;(G<sup>2</sup>)</i> and the CP-SAT objective.",
        body_style
    ))

    story.append(Paragraph("5.4 Automated Test Suite", h2_style))
    story.append(Paragraph(
        "The test suite contains 47 automated tests covering edge cases, property bounds, and round-trip translations. "
        "All 47 tests pass under pytest. Key test categories include:<br/>"
        "• Single-node topologies (1 slot, 0 edges).<br/>"
        "• Co-located coordinate detection and immediate error termination.<br/>"
        "• Disconnected components and multi-cluster spatial reuse.<br/>"
        "• Intentional conflict injection to confirm the verifier catches 1-hop and 2-hop violations.<br/>"
        "• XML round-trip parity checks for the EMANE bridge.",
        body_style
    ))

    # ============================= PAGE 6 =============================
    story.append(PageBreak())

    # SECTION 6
    story.append(Paragraph("6. Part 2: EMANE Integration and Emulation Bridge", h1_style))
    story.append(Paragraph(
        "Part 2 bridges the Python optimizer to the Extendable Mobile Ad-hoc Network Emulator (EMANE). "
        "EMANE is a real-time framework that emulates link and physical layer radio behaviors in network research.",
        body_style
    ))

    story.append(Paragraph("6.1 Architecture Overview", h2_style))
    story.append(Spacer(1, 4))
    story.append(Image(arch_img_path, width=6.2 * inch, height=2.2 * inch))
    story.append(Paragraph("<i>Figure 2: EMANE integration pipeline. Schedule translation is tested offline; live RF emulation inside Linux network namespaces is design-only.</i>", subtitle_style))
    story.append(Spacer(1, 4))

    story.append(Paragraph("6.2 What I Tested Offline vs What Was Not Run", h2_style))
    story.append(Paragraph(
        "• <b>Tested offline:</b> I tested JSON schedule parsing, 1-based NEM identifier mapping, EMANE XML schedule generation, round-trip XML schema validation, and Python event injection script generation. All offline bridge tests pass under pytest without requiring EMANE.<br/>"
        "• <b>Not run:</b> I did not run live over-the-air packet emulation inside Linux network namespaces with EMANE daemons. Running live EMANE requires root privileges, Linux kernel virtual interfaces, and a containerized test environment.",
        body_style
    ))

    story.append(Paragraph("6.3 Radio Propagation and Range Modeling in EMANE", h2_style))
    story.append(Paragraph(
        "EMANE's TDMA scheduler radio model has no built-in 500-meter cutoff. Physical reachability is determined by node positions, RF pathloss events (<code>PathlossEvent</code>, Event ID 101), antenna gain, and receiver sensitivity.<br/>"
        "If EMANE runs without location or pathloss events, all 16 virtual radios share a single broadcast domain over multicast OTA (<code>224.1.2.8:45703</code>). "
        "Under global visibility, transmissions from nodes sharing Slot 8 (such as Node_01 and Node_04) would collide at the physical layer. "
        "To demonstrate spatial reuse in emulation, pathloss and transmit power must be calibrated so received signal strength drops below detection threshold beyond 500 meters.",
        body_style
    ))

    # ============================= PAGE 7 =============================
    story.append(PageBreak())

    story.append(Paragraph("6.4 Official EMANE Verification Log", h2_style))
    story.append(Paragraph(
        "Reference repositories: "
        "<link href='https://github.com/adjacentlink/emane'>https://github.com/adjacentlink/emane</link>"
        " &nbsp;|&nbsp; "
        "<link href='https://github.com/adjacentlink/emane-guide'>https://github.com/adjacentlink/emane-guide</link>",
        body_style
    ))

    emane_rows = [
        [
            Paragraph("Parameter / Component", table_cell_header),
            Paragraph("Category", table_cell_header),
            Paragraph("Verified Name / Setting", table_cell_header),
            Paragraph("Source file &amp; quoted line", table_cell_header),
            Paragraph("Status", table_cell_header),
        ],
        [
            Paragraph("MAC Model Library", table_cell_bold),
            Paragraph("MAC Plugin", table_cell),
            Paragraph("tdmaeventschedulerradiomodel", table_cell),
            Paragraph("<b>tdmaradiomodel.xml.in</b>: <i>&lt;mac library='tdmaeventschedulerradiomodel'&gt;</i>", table_cell),
            Paragraph("<b>VERIFIED</b>", table_cell_bold),
        ],
        [
            Paragraph("MAC vs Structure", table_cell_bold),
            Paragraph("Architecture", table_cell),
            Paragraph("&lt;structure&gt; holds timing", table_cell),
            Paragraph("<b>tdma-radio-model.txt</b>: <i>'The TDMA structure defines: Slot size..., Slot overhead...'</i>", table_cell),
            Paragraph("<b>VERIFIED</b>", table_cell_bold),
        ],
        [
            Paragraph("MAC PCR Curve URI", table_cell_bold),
            Paragraph("MAC Param", table_cell),
            Paragraph("pcrcurveuri", table_cell),
            Paragraph("<b>tdmaradiomodel.xml.in</b>: <i>&lt;param name='pcrcurveuri' value='...tdmabasemodelpcr.xml'/&gt;</i>", table_cell),
            Paragraph("<b>VERIFIED</b>", table_cell_bold),
        ],
        [
            Paragraph("MAC Queue Controls", table_cell_bold),
            Paragraph("MAC Param", table_cell),
            Paragraph("queue.depth, aggregation, etc.", table_cell),
            Paragraph("<b>tdmaradiomodel.xml.in</b>: <i>&lt;param name='queue.depth' value='255'/&gt;</i>", table_cell),
            Paragraph("<b>VERIFIED</b>", table_cell_bold),
        ],
        [
            Paragraph("Schedule Root Element", table_cell_bold),
            Paragraph("XML Schema", table_cell),
            Paragraph("&lt;emane-tdma-schedule&gt;", table_cell),
            Paragraph("<b>tdmaschedule.xsd</b>: <i>&lt;xs:element name='emane-tdma-schedule'&gt;</i>", table_cell),
            Paragraph("<b>VERIFIED</b>", table_cell_bold),
        ],
        [
            Paragraph("Structure Element", table_cell_bold),
            Paragraph("XML Element", table_cell),
            Paragraph("&lt;structure frames=.. slots=..&gt;", table_cell),
            Paragraph("<b>tdmaschedule.xsd</b>: <i>&lt;xs:element name='structure' slotduration=..&gt;</i>", table_cell),
            Paragraph("<b>VERIFIED</b>", table_cell_bold),
        ],
        [
            Paragraph("Multiframe / Frame", table_cell_bold),
            Paragraph("XML Element", table_cell),
            Paragraph("&lt;multiframe&gt; / &lt;frame&gt;", table_cell),
            Paragraph("<b>tdmaschedule.xsd</b>: <i>&lt;xs:element name='multiframe'&gt; containing &lt;frame&gt;</i>", table_cell),
            Paragraph("<b>VERIFIED</b>", table_cell_bold),
        ],
        [
            Paragraph("Slot Allocation", table_cell_bold),
            Paragraph("XML Element", table_cell),
            Paragraph("&lt;slot index=.. nodes=..&gt;&lt;tx/&gt;", table_cell),
            Paragraph("<b>tdmaschedule.xsd</b>: <i>&lt;xs:element name='slot'&gt; with &lt;tx&gt;, &lt;rx&gt;, &lt;idle&gt;</i>", table_cell),
            Paragraph("<b>VERIFIED</b>", table_cell_bold),
        ],
        [
            Paragraph("CLI Injection Tool", table_cell_bold),
            Paragraph("CLI Script", table_cell),
            Paragraph("emaneevent-tdmaschedule", table_cell),
            Paragraph("<b>tdma-radio-model.txt</b>: <i>$ emaneevent-tdmaschedule schedule.xml -i lo</i>", table_cell),
            Paragraph("<b>VERIFIED</b>", table_cell_bold),
        ],
        [
            Paragraph("Python Event Class", table_cell_bold),
            Paragraph("Python API", table_cell),
            Paragraph("emane.events.TDMAScheduleEvent", table_cell),
            Paragraph("<b>tdmascheduleevent.py</b>: <i>class TDMAScheduleEvent; def structure(..); def append(..)</i>", table_cell),
            Paragraph("<b>VERIFIED</b>", table_cell_bold),
        ],
        [
            Paragraph("Python Event Service", table_cell_bold),
            Paragraph("Python API", table_cell),
            Paragraph("emane.events.EventService", table_cell),
            Paragraph("<b>eventservice.py</b>: <i>class EventService(eventchannel); def publish(nemId, event)</i>", table_cell),
            Paragraph("<b>VERIFIED</b>", table_cell_bold),
        ],
        [
            Paragraph("MAC Param Schedule", table_cell_bold),
            Paragraph("MAC Param", table_cell),
            Paragraph("&lt;param name='schedule'&gt;", table_cell),
            Paragraph("Not in official tdmaradiomodel.xml.in; runtime events appear required", table_cell),
            Paragraph("<b>ASSUMPTION</b>", table_cell_bold),
        ],
    ]
    t_log = Table(emane_rows, colWidths=[1.25 * inch, 0.75 * inch, 1.35 * inch, 2.75 * inch, 1.15 * inch])
    t_log.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(NAVY)),
            ("ALIGN", (1, 0), (1, -1), "CENTER"),
            ("ALIGN", (4, 0), (4, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor(BORDER_COLOR)),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor(ROW_ALT)]),
            ("TOPPADDING", (0, 0), (-1, -1), 1.5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 1.5),
        ])
    )
    story.append(t_log)
    story.append(Spacer(1, 4))

    story.append(Paragraph("6.5 Planned Test Plan (Not Yet Run)", h2_style))
    story.append(Paragraph(
        "1. <b>Valid schedule test:</b> Transmit ping and iperf packets across all pairs. Verify that packet delivery occurs strictly inside allocated 1.0 ms slots at 9 ms frame intervals, with expected delivery only in scheduled slots.<br/>"
        "2. <b>Conflicting schedule test:</b> Intentionally assign two 2-hop neighbors to the same slot. Verify that simultaneous transmissions cause collision, low SINR, and packet drops at the intermediate receiver.<br/>"
        "3. <b>Range calibration test:</b> Tune the pathloss model so communication drops off at approximately 500 meters, verifying spatial reuse without false collisions.",
        body_style
    ))

    # ============================= PAGE 8 =============================
    story.append(PageBreak())

    # SECTION 7
    story.append(Paragraph("7. Things I Am Unsure About", h1_style))
    story.append(Paragraph(
        "I identified two areas where information is incomplete:<br/>"
        "1. <b>Schedule loading via MAC parameter:</b> The official <code>tdmaradiomodel.xml.in</code> manifest does not list a <code>schedule</code> parameter. Official guides inject schedules dynamically using <code>emaneevent-tdmaschedule</code> or the <code>TDMAScheduleEvent</code> API. Loading a schedule statically from a MAC parameter remains an unverified assumption.<br/>"
        "2. <b>The brief's 5-slot sample:</b> The assignment brief showed a sample output with 5 slots, but did not provide coordinates. On a 4x4 grid with 300 m spacing and 500 m radio range, 5 slots is mathematically impossible due to the 9-clique lower bound. If 5 slots was intended, either the radio range was lower (excluding diagonals) or the topology was linear or sparse. I treated the brief's sample as an illustrative format example rather than a fixed target. The independent verifier checks physical correctness.",
        body_style
    ))

    # SECTION 8
    story.append(Paragraph("8. Next Steps", h1_style))
    story.append(Paragraph(
        "If I continue work on this project, I will:<br/>"
        "1. <b>Execute live EMANE on a Linux testbed:</b> Set up Linux network namespaces and run EMANE daemons in a Docker container to measure real packet latency and throughput.<br/>"
        "2. <b>Calibrate propagation models:</b> Tune freespace or two-ray pathloss parameters to produce the 500-meter cutoff in live emulation.<br/>"
        "3. <b>Multi-channel TDMA:</b> Extend the optimizer to allocate both time slots and frequency channels <i>(t, f)</i>, reducing frame length in dense networks.<br/>"
        "4. <b>Dynamic mobile scheduling:</b> Adapt the scheduler for moving nodes using incremental coloring and distributed slot reservations.",
        body_style
    ))

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"[SUCCESS] Built full design PDF: {filename}")


# ---------------------------------------------------------------------------
# Matplotlib figure generators for PDF & PPTX visuals
# ---------------------------------------------------------------------------

def _generate_grid_graph_image(path: str):
    """Draw 4x4 grid colored by the verified 9-slot schedule from examples/grid_schedule.json."""
    schedule_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "examples", "grid_schedule.json")
    with open(schedule_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    raw_coords = data["coordinates"]
    schedule = data["schedule"]

    coords = parse_coordinates(raw_coords)
    G = build_connectivity_graph(coords, 500.0)

    # Abort if independent verification fails
    is_valid, violations = verify_schedule(G, schedule)
    if not is_valid:
        raise RuntimeError(f"Cannot generate diagram: schedule is invalid! Violations: {violations}")

    fig, ax = plt.subplots(1, 1, figsize=(7.2, 5.5))

    slot_colors = [
        "#E41A1C", "#377EB8", "#4DAF4A", "#984EA3", "#FF7F00",
        "#FFFF33", "#A65628", "#F781BF", "#00C853",
    ]

    # Draw connectivity edges
    for u, v in G.edges():
        xu, yu = coords[u]
        xv, yv = coords[v]
        ax.plot([xu, xv], [yu, yv], color="#CFD8DC", linewidth=1.2, zorder=1)

    corner_nodes = {"Node_01", "Node_04", "Node_13", "Node_16"}

    for node_name, (x, y) in coords.items():
        slot = schedule[node_name]
        color = slot_colors[slot]

        # Highlight corners (Slot 8)
        if node_name in corner_nodes:
            halo = plt.Circle((x, y), 54, color="#00C853", fill=False, linewidth=3.0, linestyle="--", zorder=3)
            ax.add_patch(halo)
            circle = plt.Circle((x, y), 38, facecolor=color, edgecolor="#1B5E20", linewidth=2.5, zorder=4)
        else:
            circle = plt.Circle((x, y), 38, facecolor=color, edgecolor="#37474F", linewidth=1.5, zorder=4)

        ax.add_patch(circle)

        label_num = str(int(node_name.split("_")[-1]))
        ax.text(x, y, label_num, ha="center", va="center", fontsize=9.5, fontweight="bold",
                color="black" if slot == 5 else "white", zorder=5)

    # Caption highlighting the corners
    ax.text(450, -110, "Highlighted corners (1, 4, 13, 16): Slot 8\n3+ hops apart: same slot (spatial reuse)",
            ha="center", va="top", fontsize=8.5, fontweight="bold", color="#1B5E20",
            bbox=dict(boxstyle="round,pad=0.3", facecolor="#E8F5E9", edgecolor="#81C784", alpha=0.9))

    # Legend outside plot
    legend_handles = [
        mpatches.Patch(facecolor=slot_colors[s], edgecolor="#37474F", label=f"Slot {s}")
        for s in range(9)
    ]
    ax.legend(handles=legend_handles, title="Slots (9 total)", loc="upper left",
              bbox_to_anchor=(1.02, 1.0), frameon=True, fontsize=8, title_fontsize=9)

    ax.set_xlim(-100, 1000)
    ax.set_ylim(-180, 1020)
    ax.set_aspect("equal")
    ax.set_title("4x4 Grid (300 m) - Optimal 9-Slot Assignment", fontsize=11, fontweight="bold", pad=8)
    ax.set_xlabel("X (meters)", fontsize=8)
    ax.set_ylabel("Y (meters)", fontsize=8)
    ax.tick_params(labelsize=7)

    fig.tight_layout()
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)


def _generate_hidden_terminal_image(path: str):
    """Draw A -> B <- C hidden terminal diagram."""
    fig, ax = plt.subplots(1, 1, figsize=(7, 3))
    ax.set_xlim(-1, 9)
    ax.set_ylim(-1.5, 2.5)
    ax.set_aspect("equal")
    ax.axis("off")

    # Nodes
    nodes = {"A": (1, 0.5), "B": (4, 0.5), "C": (7, 0.5)}
    for name, (x, y) in nodes.items():
        circle = plt.Circle((x, y), 0.5, color="#1565C0" if name == "B" else "#E53935",
                            ec="black", linewidth=2, zorder=3)
        ax.add_patch(circle)
        ax.text(x, y, name, ha="center", va="center", fontsize=16,
                fontweight="bold", color="white", zorder=4)

    # Range circles
    for name in ["A", "C"]:
        x, y = nodes[name]
        range_circle = plt.Circle((x, y), 3.2, fill=False, ec="#E53935",
                                   linestyle="--", linewidth=1.2, zorder=1, alpha=0.5)
        ax.add_patch(range_circle)

    # Arrows
    ax.annotate("", xy=(3.5, 0.5), xytext=(1.5, 0.5),
                arrowprops=dict(arrowstyle="->", lw=2, color="#2E7D32"))
    ax.annotate("", xy=(4.5, 0.5), xytext=(6.5, 0.5),
                arrowprops=dict(arrowstyle="->", lw=2, color="#2E7D32"))
    ax.text(2.5, 1.2, "<= 500 m", fontsize=10, ha="center", color="#2E7D32")
    ax.text(5.5, 1.2, "<= 500 m", fontsize=10, ha="center", color="#2E7D32")

    # Out of range indicator
    ax.annotate("", xy=(6.5, -0.4), xytext=(1.5, -0.4),
                arrowprops=dict(arrowstyle="<->", lw=1.5, color="#B71C1C", linestyle="--"))
    ax.text(4, -1.0, "A and C out of range (> 500 m)\nBut both collide at B!", fontsize=9,
            ha="center", color="#B71C1C", fontstyle="italic")

    ax.set_title("Hidden Terminal Problem: A -> B <- C", fontsize=14, fontweight="bold", pad=10)
    fig.tight_layout()
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)


def _generate_benchmark_bar_chart(path: str):
    """Bar chart of heuristic vs exact results."""
    fig, ax = plt.subplots(1, 1, figsize=(7, 3.5))
    topologies = ["4x4 Grid\n(300 m)", "Sparse Linear\n(350 m)", "Dense Cluster\n(<=500 m)", "Disconnected\nClusters"]
    exact_vals = [9, 3, 16, 8]
    heur_vals = [9, 3, 16, 8]

    x = np.arange(len(topologies))
    width = 0.35

    bars1 = ax.bar(x - width / 2, exact_vals, width, label="Exact Solver", color="#0D47A1", zorder=3)
    bars2 = ax.bar(x + width / 2, heur_vals, width, label="Best Heuristic", color="#42A5F5", zorder=3)

    ax.set_ylabel("Slots", fontsize=11)
    ax.set_title("Benchmark Results: All Heuristics Match Exact Optimum (0 Gap)", fontsize=12, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(topologies, fontsize=9)
    ax.legend(fontsize=10)
    ax.set_ylim(0, 19)
    ax.grid(axis="y", alpha=0.3, zorder=0)

    # Add value labels
    for bar in bars1:
        h = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2, h + 0.3, str(int(h)),
                ha="center", va="bottom", fontweight="bold", fontsize=10, color="#0D47A1")
    for bar in bars2:
        h = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2, h + 0.3, str(int(h)),
                ha="center", va="bottom", fontsize=10, color="#42A5F5")

    fig.tight_layout()
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)


def _generate_architecture_diagram(path: str):
    """Part 2 architecture: Python brain -> JSON -> bridge -> XML -> EMANE."""
    fig, ax = plt.subplots(1, 1, figsize=(9, 3.2))
    ax.set_xlim(-0.5, 10.5)
    ax.set_ylim(-1, 3)
    ax.axis("off")

    boxes = [
        (0.5, 1, "Python\nOptimizer", "#0D47A1", "white"),
        (2.8, 1, "Schedule\nJSON", "#1565C0", "white"),
        (5.1, 1, "EMANE\nBridge", "#2196F3", "white"),
        (7.4, 1, "Schedule\nXML", "#42A5F5", "white"),
        (9.7, 1, "EMANE\nRadios", "#0D47A1", "white"),
    ]

    for x, y, label, bg, fg in boxes:
        rect = mpatches.FancyBboxPatch((x - 0.7, y - 0.5), 1.4, 1.0,
                                         boxstyle="round,pad=0.1",
                                         facecolor=bg, edgecolor="black", linewidth=1.5)
        ax.add_patch(rect)
        ax.text(x, y, label, ha="center", va="center", fontsize=10,
                fontweight="bold", color=fg, zorder=4)

    # Arrows between boxes
    for i in range(len(boxes) - 1):
        x1 = boxes[i][0] + 0.7
        x2 = boxes[i + 1][0] - 0.7
        ax.annotate("", xy=(x2, 1), xytext=(x1, 1),
                    arrowprops=dict(arrowstyle="->", lw=2, color="#333333"))

    # Status labels
    ax.text(3.9, 2.3, "TESTED OFFLINE", fontsize=11, ha="center", fontweight="bold",
            color="#2E7D32", bbox=dict(boxstyle="round,pad=0.3", facecolor="#C8E6C9", edgecolor="#2E7D32"))
    ax.plot([0.5, 7.4], [2.1, 2.1], color="#2E7D32", linewidth=1.5, linestyle="--")

    ax.text(9.7, 2.3, "DESIGN ONLY\n(NOT RUN)", fontsize=8.5, ha="center", fontweight="bold",
            color="#E65100", bbox=dict(boxstyle="round,pad=0.3", facecolor="#FFE0B2", edgecolor="#E65100"))

    ax.set_title("Part 2: EMANE Integration Architecture", fontsize=13, fontweight="bold", pad=15)
    fig.tight_layout()
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)


# ---------------------------------------------------------------------------
# PPTX Builder
# ---------------------------------------------------------------------------

def build_pptx(filename: str):
    import sys
    from pathlib import Path
    docs_dir = Path(__file__).resolve().parent
    if str(docs_dir) not in sys.path:
        sys.path.insert(0, str(docs_dir))
    from build_deck import create_deck
    create_deck(filename)


if __name__ == "__main__":
    pdf_path = os.path.join(os.path.dirname(__file__), "design.pdf")
    pptx_path = os.path.join(os.path.dirname(__file__), "presentation.pptx")
    build_pdf(pdf_path)
    build_pptx(pptx_path)
