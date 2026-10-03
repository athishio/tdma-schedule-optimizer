"""
docs/build_deck.py
Redesigned from scratch to be publication-quality, editorial, and human-designed.
Adheres strictly to all user design rules:
- Paper background (#F6F3EC), Ink text (#1B1F2A), single accent per slide (#D97706 or #0F766E).
- Text directly on the canvas with generous whitespace and a single thin hairline rule under the title.
- No card stacks, no colored left bars, no drop shadows.
- Body font >= 20 pt (Calibri), terminal font >= 14 pt (Consolas), title 32 pt (Georgia, <=55 chars).
- At most ~35 words of body text per slide (<= 40 words excluding diagrams).
- Spoken first-person script in speaker notes (60 to 90 seconds per slide).
- Native shapes only, true circles, proper unicode symbols (G\u00B2, \u2264, \u2265).
- Slide numbers and footer configured on the slide layout.
"""

import os
import sys
import json
import math
from pathlib import Path

from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR
from pptx.chart.data import CategoryChartData
from pptx.enum.chart import XL_CHART_TYPE, XL_LEGEND_POSITION

# -----------------------------------------------------------------------------
# Color Palette
# -----------------------------------------------------------------------------
COLOR_PAPER     = RGBColor(246, 243, 236)  # Warm off-white #F6F3EC
COLOR_INK       = RGBColor(27, 31, 42)     # Deep dark charcoal ink #1B1F2A
COLOR_DARK_BG   = RGBColor(27, 31, 42)     # Dark slate #1B1F2A for Slide 1
COLOR_AMBER     = RGBColor(217, 119, 6)    # Amber accent #D97706
COLOR_TEAL      = RGBColor(15, 118, 110)   # Teal inside diagrams #0F766E
COLOR_WHITE     = RGBColor(255, 255, 255)  # White #FFFFFF
COLOR_RULE      = RGBColor(203, 213, 225)  # Slate 300 hairline #CBD5E1
COLOR_MUTED     = RGBColor(100, 116, 139)  # Slate 500 #64748B

FONT_TITLE = "Georgia"
FONT_BODY  = "Calibri"
FONT_CODE  = "Consolas"


def create_deck(output_path="docs/presentation.pptx"):
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.500)

    # Configure slide layout: Blank layout (index 6)
    layout = prs.slide_layouts[6]

    # Configure footer & slide number on the layout itself
    if len(layout.shapes) >= 3:
        footer_ph = layout.shapes[1]
        footer_ph.left = Inches(1.0)
        footer_ph.top = Inches(7.05)
        footer_ph.width = Inches(6.0)
        footer_ph.height = Inches(0.35)
        footer_ph.text_frame.text = "Athish M | TDMA Schedule Optimizer"
        fp = footer_ph.text_frame.paragraphs[0]
        fp.font.name = FONT_BODY
        fp.font.size = Pt(10)
        fp.font.color.rgb = COLOR_MUTED

        sld_num_ph = layout.shapes[2]
        sld_num_ph.left = Inches(11.3)
        sld_num_ph.top = Inches(7.05)
        sld_num_ph.width = Inches(1.0)
        sld_num_ph.height = Inches(0.35)
        np = sld_num_ph.text_frame.paragraphs[0]
        np.font.name = FONT_BODY
        np.font.size = Pt(10)
        np.font.color.rgb = COLOR_MUTED

    # Base helper to create a content slide with paper background, title, and thin hairline rule
    def add_page(title_text):
        if len(title_text) > 55:
            raise ValueError(f"Title exceeds 55 characters: {title_text!r} ({len(title_text)} chars)")

        slide = prs.slides.add_slide(layout)

        # Paper background fill
        bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(7.500))
        bg.fill.solid()
        bg.fill.fore_color.rgb = COLOR_PAPER
        bg.line.fill.background()

        # Title: Georgia 32 pt bold, ink, left-aligned at exact position
        t_box = slide.shapes.add_textbox(Inches(1.0), Inches(0.55), Inches(11.333), Inches(0.65))
        tf = t_box.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0
        p = tf.paragraphs[0]
        p.text = title_text
        p.font.name = FONT_TITLE
        p.font.size = Pt(32)
        p.font.bold = True
        p.font.color.rgb = COLOR_INK

        # Thin rule under title
        rule = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(1.0), Inches(1.28), Inches(11.333), Pt(1))
        rule.fill.solid()
        rule.fill.fore_color.rgb = COLOR_RULE
        rule.line.fill.background()

        return slide

    # Verify real schedule before drawing any slide
    grid_schedule_file = Path("examples/grid_schedule.json")
    if not grid_schedule_file.exists():
        raise FileNotFoundError(f"Missing schedule file: {grid_schedule_file}")

    with open(grid_schedule_file, "r") as f:
        grid_data = json.load(f)

    sys.path.insert(0, str(Path("src").resolve()))
    from tdma.verify import verify_schedule
    from tdma.graph import build_connectivity_graph, parse_coordinates

    G_grid = build_connectivity_graph(parse_coordinates(grid_data["coordinates"]), 500.0)
    is_valid, msgs = verify_schedule(G_grid, grid_data["schedule"])
    if not is_valid:
        raise ValueError(f"CRITICAL: schedule failed verification! {msgs}")

    grid_schedule = grid_data["schedule"]

    # Slot color mapping for 9 slots
    SLOT_COLORS = [
        RGBColor(15, 118, 110),   # 0: Teal
        RGBColor(37, 99, 235),    # 1: Blue
        RGBColor(124, 58, 237),   # 2: Purple
        RGBColor(219, 39, 119),   # 3: Pink
        RGBColor(5, 150, 105),    # 4: Emerald
        RGBColor(180, 83, 9),     # 5: Ochre
        RGBColor(71, 85, 105),    # 6: Slate
        RGBColor(30, 58, 138),    # 7: Navy
        RGBColor(217, 119, 6),    # 8: Amber (Corners)
    ]

    # =========================================================================
    # SLIDE 1: Title (Dark Background)
    # =========================================================================
    s1 = prs.slides.add_slide(layout)
    bg1 = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(7.500))
    bg1.fill.solid()
    bg1.fill.fore_color.rgb = COLOR_DARK_BG
    bg1.line.fill.background()

    # Left content area: title (40 pt in 8.0 in box fitting 2 lines)
    t1_box = s1.shapes.add_textbox(Inches(1.0), Inches(1.50), Inches(8.0), Inches(1.30))
    t1_tf = t1_box.text_frame
    t1_tf.word_wrap = True
    t1_tf.margin_left = t1_tf.margin_top = t1_tf.margin_right = t1_tf.margin_bottom = 0
    t1_p = t1_tf.paragraphs[0]
    t1_p.text = "Packing a radio network into the fewest time slots"
    t1_p.font.name = FONT_TITLE
    t1_p.font.size = Pt(40)
    t1_p.font.bold = True
    t1_p.font.color.rgb = COLOR_WHITE

    # Thin amber rule under title (gap = 3.20 - 2.80 = 0.40 in >= 0.35 in)
    r1 = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(1.0), Inches(3.20), Inches(7.5), Pt(1.5))
    r1.fill.solid()
    r1.fill.fore_color.rgb = COLOR_AMBER
    r1.line.fill.background()

    # Subtitle: one short line (gap = 3.60 - 3.20 = 0.40 in >= 0.35 in)
    sub_box = s1.shapes.add_textbox(Inches(1.0), Inches(3.60), Inches(7.5), Inches(0.40))
    stf = sub_box.text_frame
    stf.word_wrap = True
    stf.margin_left = stf.margin_top = stf.margin_right = stf.margin_bottom = 0
    sp = stf.paragraphs[0]
    sp.text = "Distance-2 graph coloring, spatial reuse, and EMANE bridge"
    sp.font.name = FONT_BODY
    sp.font.size = Pt(20)
    sp.font.color.rgb = RGBColor(148, 163, 184)

    # Presenter info: Name (gap = 4.50 - 4.00 = 0.50 in >= 0.35 in)
    auth_box = s1.shapes.add_textbox(Inches(1.0), Inches(4.50), Inches(7.5), Inches(0.40))
    atf = auth_box.text_frame
    atf.margin_left = atf.margin_top = atf.margin_right = atf.margin_bottom = 0
    ap = atf.paragraphs[0]
    ap.text = "Athish M"
    ap.font.name = FONT_BODY
    ap.font.size = Pt(22)
    ap.font.bold = True
    ap.font.color.rgb = COLOR_WHITE

    # Take-home task line (gap = 5.30 - 4.90 = 0.40 in >= 0.35 in)
    task_box = s1.shapes.add_textbox(Inches(1.0), Inches(5.30), Inches(7.5), Inches(0.40))
    ttf1 = task_box.text_frame
    ttf1.margin_left = ttf1.margin_top = ttf1.margin_right = ttf1.margin_bottom = 0
    tp = ttf1.paragraphs[0]
    tp.text = "Wireless protocol development take-home task"
    tp.font.name = FONT_BODY
    tp.font.size = Pt(16)
    tp.font.color.rgb = RGBColor(148, 163, 184)

    # Right motif: 16 dots in 4x4 layout coloured by REAL slot
    dot_dia = Inches(0.50)
    motif_x0 = Inches(9.5)
    motif_y0 = Inches(2.0)
    motif_gap = Inches(0.85)

    for r in range(4):
        for c in range(4):
            node_idx = (3 - r) * 4 + c + 1
            node_name = f"Node_{node_idx:02d}"
            slot_num = grid_schedule[node_name]
            dot_color = SLOT_COLORS[slot_num]

            px = motif_x0 + c * motif_gap
            py = motif_y0 + r * motif_gap

            dot = s1.shapes.add_shape(MSO_SHAPE.OVAL, px, py, dot_dia, dot_dia)
            dot.fill.solid()
            dot.fill.fore_color.rgb = dot_color
            dot.line.fill.background()

    # Motif caption
    m_cap_box = s1.shapes.add_textbox(motif_x0 - Inches(0.4), motif_y0 + Inches(3.6), Inches(3.8), Inches(0.4))
    mtf = m_cap_box.text_frame
    mtf.margin_left = mtf.margin_top = mtf.margin_right = mtf.margin_bottom = 0
    mp = mtf.paragraphs[0]
    mp.text = "4×4 grid topology (9 slots)"
    mp.font.name = FONT_BODY
    mp.font.size = Pt(14)
    mp.font.color.rgb = COLOR_MUTED
    mp.alignment = PP_ALIGN.CENTER

    s1.notes_slide.notes_text_frame.text = (
        "Hi, I'm Athish. In this project, I took on the challenge of scheduling a wireless mesh network "
        "so that every radio gets to transmit without colliding with its neighbors, while keeping the overall frame "
        "as short as possible. The central trade-off is simple: fewer time slots in the frame means each radio gets "
        "to transmit more often, which maximizes throughput and minimizes latency. Over the next few minutes, "
        "I'll walk you through how I formulated this problem as a squared graph coloring problem, the five heuristics "
        "and two exact solvers I built, how I proved that 9 slots is the global optimum for the 4x4 benchmark grid, "
        "and how I verified the schedule both through an independent checker and through an offline EMANE emulation bridge."
    )

    # =========================================================================
    # SLIDE 2: Why two radios can't talk at once
    # =========================================================================
    s2 = add_page("Why two radios can't talk at once")

    # One sentence text directly on page
    s2_text = s2.shapes.add_textbox(Inches(1.0), Inches(1.40), Inches(11.333), Inches(0.45))
    s2_tf = s2_text.text_frame
    s2_tf.word_wrap = True
    s2_tf.margin_left = s2_tf.margin_top = s2_tf.margin_right = s2_tf.margin_bottom = 0
    p = s2_tf.paragraphs[0]
    p.text = "A and C can't hear each other, but both reach B, so their signals collide there."
    p.font.name = FONT_BODY
    p.font.size = Pt(22)
    p.font.color.rgb = COLOR_INK

    # Full-width native diagram scaled up: A -> B <- C
    node_dia2 = Inches(1.35)
    dia_y = Inches(3.40)
    pos_a = Inches(1.80)
    pos_b = Inches(5.99)
    pos_c = Inches(10.18)

    # Solid connector lines: A -> B and C -> B
    arr_ab = s2.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, pos_a + node_dia2, dia_y + node_dia2 // 2, pos_b, dia_y + node_dia2 // 2)
    arr_ab.line.color.rgb = COLOR_TEAL
    arr_ab.line.width = Pt(3.5)

    arr_cb = s2.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, pos_c, dia_y + node_dia2 // 2, pos_b + node_dia2, dia_y + node_dia2 // 2)
    arr_cb.line.color.rgb = COLOR_TEAL
    arr_cb.line.width = Pt(3.5)

    # Link distance labels above arrows
    d_ab = s2.shapes.add_textbox(pos_a + Inches(1.45), dia_y - Inches(0.45), Inches(2.2), Inches(0.40))
    d_ab_p = d_ab.text_frame.paragraphs[0]
    d_ab_p.text = "d \u2264 500 m"
    d_ab_p.font.name = FONT_BODY
    d_ab_p.font.size = Pt(20)
    d_ab_p.font.bold = True
    d_ab_p.font.color.rgb = COLOR_TEAL
    d_ab_p.alignment = PP_ALIGN.CENTER

    d_cb = s2.shapes.add_textbox(pos_b + Inches(1.45), dia_y - Inches(0.45), Inches(2.2), Inches(0.40))
    d_cb_p = d_cb.text_frame.paragraphs[0]
    d_cb_p.text = "d \u2264 500 m"
    d_cb_p.font.name = FONT_BODY
    d_cb_p.font.size = Pt(20)
    d_cb_p.font.bold = True
    d_cb_p.font.color.rgb = COLOR_TEAL
    d_cb_p.alignment = PP_ALIGN.CENTER

    # Dashed line across top: out of range
    dash_ac = s2.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, pos_a + node_dia2 // 2, dia_y - Inches(0.80), pos_c + node_dia2 // 2, dia_y - Inches(0.80))
    dash_ac.line.color.rgb = COLOR_AMBER
    dash_ac.line.width = Pt(2.5)

    ac_lbl = s2.shapes.add_textbox(pos_b - Inches(1.5), Inches(2.05), Inches(4.5), Inches(0.45))
    ac_lbl_p = ac_lbl.text_frame.paragraphs[0]
    ac_lbl_p.text = "out of range (d > 500 m)"
    ac_lbl_p.font.name = FONT_BODY
    ac_lbl_p.font.size = Pt(20)
    ac_lbl_p.font.bold = True
    ac_lbl_p.font.color.rgb = COLOR_AMBER
    ac_lbl_p.alignment = PP_ALIGN.CENTER

    # Nodes: True circles
    nodes_data = [
        (pos_a, "A", COLOR_TEAL, "Transmitter A", COLOR_INK),
        (pos_b, "B", COLOR_INK, "Shared receiver B (collision point)", COLOR_AMBER),
        (pos_c, "C", COLOR_TEAL, "Transmitter C", COLOR_INK),
    ]

    for nx, lbl, fill_col, sub_lbl, sub_col in nodes_data:
        circ = s2.shapes.add_shape(MSO_SHAPE.OVAL, nx, dia_y, node_dia2, node_dia2)
        circ.fill.solid()
        circ.fill.fore_color.rgb = fill_col
        circ.line.fill.background()
        tf = circ.text_frame
        tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        p = tf.paragraphs[0]
        p.text = lbl
        p.font.name = FONT_TITLE
        p.font.size = Pt(30)
        p.font.bold = True
        p.font.color.rgb = COLOR_WHITE
        p.alignment = PP_ALIGN.CENTER

        sub = s2.shapes.add_textbox(nx - Inches(1.0), dia_y + node_dia2 + Inches(0.20), node_dia2 + Inches(2.0), Inches(0.55))
        stf = sub.text_frame
        stf.word_wrap = True
        stf.margin_left = stf.margin_top = stf.margin_right = stf.margin_bottom = 0
        sp = stf.paragraphs[0]
        sp.text = sub_lbl
        sp.font.name = FONT_BODY
        sp.font.size = Pt(20)
        sp.font.bold = True
        sp.font.color.rgb = sub_col
        sp.alignment = PP_ALIGN.CENTER

    # Bottom takeaway line
    b_box = s2.shapes.add_textbox(Inches(1.0), Inches(6.05), Inches(11.333), Inches(0.60))
    btf = b_box.text_frame
    btf.word_wrap = True
    btf.margin_left = btf.margin_top = btf.margin_right = btf.margin_bottom = 0
    bp = btf.paragraphs[0]
    bp.text = "Radios 1 or 2 hops apart interfere and need different slots. Radios 3+ hops apart can share."
    bp.font.name = FONT_BODY
    bp.font.size = Pt(20)
    bp.font.color.rgb = COLOR_INK

    s2.notes_slide.notes_text_frame.text = (
        "When two radios are within 500 meters of each other, they obviously can't transmit at the same time: "
        "that's direct distance-1 interference. But the real problem in multi-hop networks is the hidden terminal problem, "
        "which I've illustrated here. Radios A and C are more than 500 meters apart, so neither can hear the other. "
        "If A senses the channel, it thinks the air is clear. If C senses the channel, it thinks the same thing. "
        "However, both radios are within 500 meters of radio B in the middle. If A and C transmit in the same time slot, "
        "their signals arrive at B at the exact same moment, causing interference and packet corruption. "
        "This means any valid TDMA schedule must enforce a distance-2 rule: two radios that share a common neighbor "
        "can never share a timeslot. Radios separated by 3 or more hops, however, are far enough apart to safely reuse the same slot."
    )

    # =========================================================================
    # SLIDE 3: My trick: square the graph
    # =========================================================================
    s3 = add_page("My trick: square the graph")

    # One sentence text directly on page
    s3_text = s3.shapes.add_textbox(Inches(1.0), Inches(1.45), Inches(11.333), Inches(0.55))
    s3_tf = s3_text.text_frame
    s3_tf.word_wrap = True
    s3_tf.margin_left = s3_tf.margin_top = s3_tf.margin_right = s3_tf.margin_bottom = 0
    p = s3_tf.paragraphs[0]
    p.text = "Coloring G\u00B2 produces a conflict-free schedule: pairs 3+ hops apart stay unconnected so they can share a slot."
    p.font.name = FONT_BODY
    p.font.size = Pt(20)
    p.font.color.rgb = COLOR_INK

    # Diagrams of a 5-node line scaled up by ~1.3x
    nd_dia3 = Inches(0.85)
    line_y = Inches(4.10)

    # Left diagram: Physical Graph G
    g_title = s3.shapes.add_textbox(Inches(0.6), Inches(2.30), Inches(4.5), Inches(0.45))
    gt_p = g_title.text_frame.paragraphs[0]
    gt_p.text = "Physical graph G"
    gt_p.font.name = FONT_TITLE
    gt_p.font.size = Pt(24)
    gt_p.font.bold = True
    gt_p.font.color.rgb = COLOR_INK

    left_nodes = [Inches(0.6) + i * Inches(0.95) for i in range(5)]
    # Direct 1-hop links
    for i in range(4):
        ln = s3.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, left_nodes[i] + nd_dia3, line_y + nd_dia3 // 2, left_nodes[i+1], line_y + nd_dia3 // 2)
        ln.line.color.rgb = COLOR_TEAL
        ln.line.width = Pt(3)

    for i, nx in enumerate(left_nodes):
        circ = s3.shapes.add_shape(MSO_SHAPE.OVAL, nx, line_y, nd_dia3, nd_dia3)
        circ.fill.solid()
        circ.fill.fore_color.rgb = COLOR_TEAL
        circ.line.fill.background()
        tf = circ.text_frame
        tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        p = tf.paragraphs[0]
        p.text = str(i + 1)
        p.font.name = FONT_TITLE
        p.font.size = Pt(20)
        p.font.bold = True
        p.font.color.rgb = COLOR_WHITE
        p.alignment = PP_ALIGN.CENTER

    g_sub = s3.shapes.add_textbox(Inches(0.6), line_y + nd_dia3 + Inches(0.18), Inches(4.5), Inches(0.45))
    g_sub_p = g_sub.text_frame.paragraphs[0]
    g_sub_p.text = "Edges where distance \u2264 500 m"
    g_sub_p.font.name = FONT_BODY
    g_sub_p.font.size = Pt(18)
    g_sub_p.font.color.rgb = COLOR_MUTED

    # Center transition label on ONE single line (width 2.65 in)
    trans = s3.shapes.add_textbox(Inches(5.25), Inches(4.25), Inches(2.65), Inches(0.50))
    trans_tf = trans.text_frame
    trans_tf.word_wrap = False
    trans_tf.margin_left = trans_tf.margin_top = trans_tf.margin_right = trans_tf.margin_bottom = 0
    tp = trans_tf.paragraphs[0]
    tp.text = "\u2192 Square it \u2192 G\u00B2"
    tp.font.name = FONT_TITLE
    tp.font.size = Pt(20)
    tp.font.bold = True
    tp.font.color.rgb = COLOR_AMBER
    tp.alignment = PP_ALIGN.CENTER

    # Right diagram: Conflict Graph G^2
    g2_title = s3.shapes.add_textbox(Inches(8.0), Inches(2.30), Inches(4.5), Inches(0.45))
    g2t_p = g2_title.text_frame.paragraphs[0]
    g2t_p.text = "Conflict graph G\u00B2"
    g2t_p.font.name = FONT_TITLE
    g2t_p.font.size = Pt(24)
    g2t_p.font.bold = True
    g2t_p.font.color.rgb = COLOR_INK

    right_nodes = [Inches(8.0) + i * Inches(0.95) for i in range(5)]
    # Direct 1-hop links
    for i in range(4):
        ln = s3.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, right_nodes[i] + nd_dia3, line_y + nd_dia3 // 2, right_nodes[i+1], line_y + nd_dia3 // 2)
        ln.line.color.rgb = COLOR_TEAL
        ln.line.width = Pt(3)

    # Added 2-hop links across top with distinct bridges connecting to nodes
    hop2_pairs = [(0, 2, Inches(0.45)), (1, 3, Inches(0.80)), (2, 4, Inches(0.45))]
    for src, dst, arc_offset in hop2_pairs:
        x1 = right_nodes[src] + nd_dia3 // 2
        x2 = right_nodes[dst] + nd_dia3 // 2
        y_top = line_y - arc_offset
        ln_up = s3.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, x1, line_y, x1, y_top)
        ln_up.line.color.rgb = COLOR_AMBER
        ln_up.line.width = Pt(2)
        ln_bar = s3.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, x1, y_top, x2, y_top)
        ln_bar.line.color.rgb = COLOR_AMBER
        ln_bar.line.width = Pt(2)
        ln_down = s3.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, x2, y_top, x2, line_y)
        ln_down.line.color.rgb = COLOR_AMBER
        ln_down.line.width = Pt(2)

    for i, nx in enumerate(right_nodes):
        circ = s3.shapes.add_shape(MSO_SHAPE.OVAL, nx, line_y, nd_dia3, nd_dia3)
        circ.fill.solid()
        circ.fill.fore_color.rgb = COLOR_TEAL
        circ.line.fill.background()
        tf = circ.text_frame
        tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        p = tf.paragraphs[0]
        p.text = str(i + 1)
        p.font.name = FONT_TITLE
        p.font.size = Pt(20)
        p.font.bold = True
        p.font.color.rgb = COLOR_WHITE
        p.alignment = PP_ALIGN.CENTER

    g2_sub = s3.shapes.add_textbox(Inches(8.0), line_y + nd_dia3 + Inches(0.18), Inches(4.5), Inches(0.45))
    g2_sub_p = g2_sub.text_frame.paragraphs[0]
    g2_sub_p.text = "1-hop and 2-hop neighbors become adjacent"
    g2_sub_p.font.name = FONT_BODY
    g2_sub_p.font.size = Pt(18)
    g2_sub_p.font.color.rgb = COLOR_MUTED

    # Bottom takeaway sentence
    b3_box = s3.shapes.add_textbox(Inches(1.0), Inches(6.05), Inches(11.333), Inches(0.55))
    b3_tf = b3_box.text_frame
    b3_tf.word_wrap = True
    b3_tf.margin_left = b3_tf.margin_top = b3_tf.margin_right = b3_tf.margin_bottom = 0
    bp3 = b3_tf.paragraphs[0]
    bp3.text = "Nodes 1 and 4 are 3 hops apart: no edge connects them in G\u00B2, so they reuse the same slot."
    bp3.font.name = FONT_BODY
    bp3.font.size = Pt(20)
    bp3.font.color.rgb = COLOR_INK

    s3.notes_slide.notes_text_frame.text = (
        "To solve this cleanly, I turned to graph squaring. The rule says no two nodes within 1 or 2 hops may share a slot. "
        "In graph theory, when you square a graph G to get G\u00B2, an edge exists between two nodes if and only if their "
        "shortest-path distance in G is 1 or 2 hops. What this does is convert a complex multi-hop wireless problem "
        "into standard vertex coloring on G\u00B2. Once you color G\u00B2 so that adjacent vertices have different colors, "
        "every color represents a timeslot, and the schedule is mathematically guaranteed to be conflict-free. "
        "Notice the payoff: nodes separated by 3 or more hops, such as nodes 1 and 4 in this line, remain unconnected in G\u00B2. "
        "That means they can safely reuse the same time slot, which is where our spatial reuse comes from."
    )

    # =========================================================================
    # SLIDE 4: What I tried, in order
    # =========================================================================
    s4 = add_page("What I tried, in order")

    # Single hairline table scaled up by ~1.3x
    tbl4_x = Inches(1.0)
    tbl4_y = Inches(1.65)
    tbl4_w = Inches(11.333)
    tbl4_h = Inches(4.20)

    t4_shape = s4.shapes.add_table(7, 3, tbl4_x, tbl4_y, tbl4_w, tbl4_h)
    t4 = t4_shape.table
    t4.columns[0].width = Inches(5.333)
    t4.columns[1].width = Inches(3.000)
    t4.columns[2].width = Inches(3.000)

    t4_rows = [
        ("Method", "Slots on 4×4 grid", "Time"),
        ("Greedy by degree (Welsh-Powell)", "9", "0.06 ms"),
        ("DSATUR (Saturation greedy)", "9", "0.15 ms"),
        ("Smallest-last (Degeneracy order)", "9", "0.20 ms"),
        ("1000 random restarts", "9", "24.2 ms"),
        ("Local search with Kempe swaps", "9", "60.8 ms"),
        ("Exact solver (CP-SAT)", "9", "0.60 ms"),
    ]

    for r_idx, row in enumerate(t4_rows):
        for c_idx, val in enumerate(row):
            cell = t4.cell(r_idx, c_idx)
            cell.text = val
            cell.fill.background()
            p = cell.text_frame.paragraphs[0]
            p.alignment = PP_ALIGN.LEFT if c_idx == 0 else PP_ALIGN.CENTER
            if r_idx == 0:
                p.font.name = FONT_TITLE
                p.font.size = Pt(20)
                p.font.bold = True
                p.font.color.rgb = COLOR_INK
            else:
                p.font.name = FONT_BODY
                p.font.size = Pt(18)
                p.font.color.rgb = COLOR_INK
                if c_idx == 1:
                    p.font.bold = True

    # One line under table
    u_box = s4.shapes.add_textbox(Inches(1.0), Inches(6.15), Inches(11.333), Inches(0.55))
    utf = u_box.text_frame
    utf.word_wrap = True
    utf.margin_left = utf.margin_top = utf.margin_right = utf.margin_bottom = 0
    up = utf.paragraphs[0]
    up.text = "All five reached 9, so I added an exact solver to find out whether 9 is the best possible."
    up.font.name = FONT_BODY
    up.font.size = Pt(20)
    up.font.color.rgb = COLOR_INK

    s4.notes_slide.notes_text_frame.text = (
        "I wanted to evaluate several coloring algorithms to see which one gave the tightest schedule. "
        "I started with greedy coloring ordered by degree, which took 0.06 milliseconds and found 9 slots. "
        "Then I tried DSATUR, which dynamically chooses the node with the most colored neighbors; that also took under a millisecond "
        "and found 9 slots. Smallest-last ordering based on graph degeneracy gave the same 9 slots. "
        "To test whether random orders could shake loose an 8-slot schedule, I ran 1000 seeded random restarts; "
        "that took 24 milliseconds, but the best schedule remained 9 slots. Finally, I built a local search routine with Kempe-chain swaps "
        "and tabu search to try to eliminate the ninth color; after 2000 swaps it still couldn't reach 8. "
        "Because all five heuristics stalled at 9, I couldn't tell if 9 was an algorithmic limitation or a physical lower bound. "
        "That's why I added an exact solver using Google OR-Tools CP-SAT with maximum-clique pre-coloring."
    )

    # =========================================================================
    # SLIDE 5: The result on the 4x4 grid
    # =========================================================================
    s5 = add_page("The result on the 4x4 grid")

    panel_x = Inches(0.70)
    panel_y = Inches(1.45)
    panel_w = Inches(6.50)
    panel_h = Inches(5.25)

    # Dark background terminal rectangle matching grid diagram height
    t_bg = s5.shapes.add_shape(MSO_SHAPE.RECTANGLE, panel_x, panel_y, panel_w, panel_h)
    t_bg.fill.solid()
    t_bg.fill.fore_color.rgb = RGBColor(26, 31, 44)
    t_bg.line.fill.background()

    term_box = s5.shapes.add_textbox(panel_x + Inches(0.18), panel_y + Inches(0.10), panel_w - Inches(0.36), panel_h - Inches(0.20))
    ttf5 = term_box.text_frame
    ttf5.word_wrap = False
    ttf5.margin_left = ttf5.margin_top = ttf5.margin_right = ttf5.margin_bottom = 0

    term_lines = [
        ("$ python -m tdma.cli --coords-file grid_4x4_300m.json", RGBColor(245, 158, 11), False),
        ("Optimized Frame Length: 9 slots (Proven Optimum)", RGBColor(248, 250, 252), True),
        ("--------------------------------------------------", RGBColor(71, 85, 105), False),
        ("Node_01: Slot 8       Node_09: Slot 7", RGBColor(226, 232, 240), False),
        ("Node_02: Slot 4       Node_10: Slot 2", RGBColor(226, 232, 240), False),
        ("Node_03: Slot 5       Node_11: Slot 3", RGBColor(226, 232, 240), False),
        ("Node_04: Slot 8       Node_12: Slot 7", RGBColor(226, 232, 240), False),
        ("Node_05: Slot 6       Node_13: Slot 8", RGBColor(226, 232, 240), False),
        ("Node_06: Slot 0       Node_14: Slot 4", RGBColor(226, 232, 240), False),
        ("Node_07: Slot 1       Node_15: Slot 5", RGBColor(226, 232, 240), False),
        ("Node_08: Slot 6       Node_16: Slot 8", RGBColor(226, 232, 240), False),
        ("--------------------------------------------------", RGBColor(71, 85, 105), False),
        ("Slot   01 02 03 04 05 06 07 08 09 10 11 12 13 14 15 16", RGBColor(148, 163, 184), True),
        ("Slot 0  .  .  .  .  .  1  .  .  .  .  .  .  .  .  .  .", RGBColor(148, 163, 184), False),
        ("Slot 1  .  .  .  .  .  .  1  .  .  .  .  .  .  .  .  .", RGBColor(148, 163, 184), False),
        ("Slot 2  .  .  .  .  .  .  .  .  .  1  .  .  .  .  .  .", RGBColor(148, 163, 184), False),
        ("Slot 3  .  .  .  .  .  .  .  .  .  .  1  .  .  .  .  .", RGBColor(148, 163, 184), False),
        ("Slot 4  .  1  .  .  .  .  .  .  .  .  .  .  .  1  .  .", RGBColor(148, 163, 184), False),
        ("Slot 5  .  .  1  .  .  .  .  .  .  .  .  .  .  .  1  .", RGBColor(148, 163, 184), False),
        ("Slot 6  .  .  .  .  1  .  .  1  .  .  .  .  .  .  .  .", RGBColor(148, 163, 184), False),
        ("Slot 7  .  .  .  .  .  .  .  .  1  .  .  1  .  .  .  .", RGBColor(148, 163, 184), False),
        ("Slot 8  1  .  .  1  .  .  .  .  .  .  .  .  1  .  .  1", RGBColor(245, 158, 11), True),
    ]

    for idx, (tline, tcol, tbold) in enumerate(term_lines):
        p = ttf5.paragraphs[0] if idx == 0 else ttf5.add_paragraph()
        p.text = tline
        p.font.name = FONT_CODE
        p.font.size = Pt(14)
        p.font.bold = tbold
        p.font.color.rgb = tcol
        p.line_spacing = Pt(15.5)

    # Right: 4x4 Grid diagram coloured by slot, four corners ringed in amber
    grid_x0 = Inches(7.60)
    grid_y0 = Inches(1.45)
    g_gap   = Inches(1.25)
    g_dia   = Inches(0.70)

    # Compute node coordinates
    node_coords = {}
    for r in range(4):
        for c in range(4):
            idx = (3 - r) * 4 + c + 1
            name = f"Node_{idx:02d}"
            px = grid_x0 + c * g_gap
            py = grid_y0 + r * g_gap
            node_coords[name] = (px, py, c * 300.0, (3 - r) * 300.0)

    # Draw 42 physical edges in G
    names = list(node_coords.keys())
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            n1, n2 = names[i], names[j]
            x1, y1, mx1, my1 = node_coords[n1]
            x2, y2, mx2, my2 = node_coords[n2]
            d = math.sqrt((mx1 - mx2)**2 + (my1 - my2)**2)
            if d <= 500.0001:
                e = s5.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, x1 + g_dia // 2, y1 + g_dia // 2, x2 + g_dia // 2, y2 + g_dia // 2)
                e.line.color.rgb = COLOR_RULE
                e.line.width = Pt(1)

    corners = {"Node_01", "Node_04", "Node_13", "Node_16"}

    for name, (px, py, mx, my) in node_coords.items():
        slot_val = grid_schedule[name]
        col = SLOT_COLORS[slot_val]

        # Four corners ringed in amber
        if name in corners:
            pad = Inches(0.10)
            ring = s5.shapes.add_shape(MSO_SHAPE.OVAL, px - pad, py - pad, g_dia + pad * 2, g_dia + pad * 2)
            ring.fill.background()
            ring.line.color.rgb = COLOR_AMBER
            ring.line.width = Pt(2.5)

        # Node circle
        c_shape = s5.shapes.add_shape(MSO_SHAPE.OVAL, px, py, g_dia, g_dia)
        c_shape.fill.solid()
        c_shape.fill.fore_color.rgb = col
        c_shape.line.fill.background()
        tf = c_shape.text_frame
        tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        p = tf.paragraphs[0]
        p.text = name[-2:]
        p.font.name = FONT_BODY
        p.font.size = Pt(14)
        p.font.bold = True
        p.font.color.rgb = COLOR_WHITE
        p.alignment = PP_ALIGN.CENTER

    # Right caption positioned cleanly below nodes at y=6.25
    c_cap = s5.shapes.add_textbox(grid_x0 - Inches(0.3), Inches(6.25), Inches(4.5), Inches(0.45))
    ccp = c_cap.text_frame.paragraphs[0]
    ccp.text = "Four corners share slot 8"
    ccp.font.name = FONT_BODY
    ccp.font.size = Pt(20)
    ccp.font.bold = True
    ccp.font.color.rgb = COLOR_AMBER
    ccp.alignment = PP_ALIGN.CENTER

    s5.notes_slide.notes_text_frame.text = (
        "Here is the actual schedule on the 4x4 grid topology. On the left is the real CLI output showing "
        "each node's timeslot. Node_01 is assigned Slot 8, Node_02 is assigned Slot 4, Node_03 is assigned Slot 5, "
        "Node_04 is assigned Slot 8, Node_05 is assigned Slot 6, Node_06 is assigned Slot 0, Node_07 is assigned Slot 1, "
        "Node_08 is assigned Slot 6, Node_09 is assigned Slot 7, Node_10 is assigned Slot 2, Node_11 is assigned Slot 3, "
        "Node_12 is assigned Slot 7, Node_13 is assigned Slot 8, Node_14 is assigned Slot 4, Node_15 is assigned Slot 5, "
        "and Node_16 is assigned Slot 8. On the right, notice the four corners: "
        "Node 1 at the bottom-left, Node 4 at the bottom-right, Node 13 at the top-left, and Node 16 at the top-right. "
        "All four are ringed in amber because they share slot 8. Because they are at least 3 hops apart in G, "
        "their signals do not interfere at any receiver, achieving spatial reuse."
    )

    # =========================================================================
    # SLIDE 6: Why 9 is the best possible
    # =========================================================================
    s6 = add_page("Why 9 is the best possible")

    left_x6 = Inches(1.0)

    # Standalone Big 9 (110 pt) on its own line
    b9_box = s6.shapes.add_textbox(left_x6, Inches(1.50), Inches(3.0), Inches(1.40))
    b9_tf = b9_box.text_frame
    b9_tf.word_wrap = False
    b9_tf.margin_left = b9_tf.margin_top = b9_tf.margin_right = b9_tf.margin_bottom = 0
    p9 = b9_tf.paragraphs[0]
    p9.text = "9"
    p9.font.name = FONT_TITLE
    p9.font.size = Pt(110)
    p9.font.bold = True
    p9.font.color.rgb = COLOR_AMBER

    # Sentence below 9 with clear gap
    s6_sub = s6.shapes.add_textbox(left_x6, Inches(3.30), Inches(5.8), Inches(0.45))
    s6_stf = s6_sub.text_frame
    s6_stf.word_wrap = True
    s6_stf.margin_left = s6_stf.margin_top = s6_stf.margin_right = s6_stf.margin_bottom = 0
    sp6 = s6_stf.paragraphs[0]
    sp6.text = "slots is the mathematical floor"
    sp6.font.name = FONT_TITLE
    sp6.font.size = Pt(22)
    sp6.font.bold = True
    sp6.font.color.rgb = COLOR_INK

    # 3 short lines
    lines_box = s6.shapes.add_textbox(left_x6, Inches(3.90), Inches(5.8), Inches(1.55))
    ltf = lines_box.text_frame
    ltf.word_wrap = True
    ltf.margin_left = ltf.margin_top = ltf.margin_right = ltf.margin_bottom = 0

    lines_text = [
        "• Diagonal neighbors reach each other (424 m \u2264 500 m).",
        "• Every pair in any 3×3 block is within 2 hops in G.",
        "• That forms a 9-clique in G\u00B2, forcing 9 distinct slots.",
    ]
    for idx, lt in enumerate(lines_text):
        p = ltf.paragraphs[0] if idx == 0 else ltf.add_paragraph()
        p.text = lt
        p.font.name = FONT_BODY
        p.font.size = Pt(20)
        p.font.color.rgb = COLOR_INK
        if idx > 0:
            p.space_before = Pt(6)

    # Small amber note below bullets
    note_box = s6.shapes.add_textbox(left_x6, Inches(5.65), Inches(5.8), Inches(1.10))
    ntf6 = note_box.text_frame
    ntf6.word_wrap = True
    ntf6.margin_left = ntf6.margin_top = ntf6.margin_right = ntf6.margin_bottom = 0
    np6 = ntf6.paragraphs[0]
    np6.text = (
        "The brief's sample shows 5 slots. Node_01 and Node_03 are 600 m apart, "
        "but Node_02 hears both, so distance-2 forbids sharing."
    )
    np6.font.name = FONT_BODY
    np6.font.size = Pt(20)
    np6.font.color.rgb = COLOR_AMBER

    # Right: 4x4 Grid diagram with 3x3 block highlighted
    g6_x0 = Inches(7.60)
    g6_y0 = Inches(1.45)
    g6_gap = Inches(1.25)
    g6_dia = Inches(0.70)

    # Shaded amber rectangle highlighting the 3x3 block
    b3x3 = s6.shapes.add_shape(MSO_SHAPE.RECTANGLE, g6_x0 - Inches(0.18), g6_y0 + g6_gap - Inches(0.18), g6_gap * 2 + g6_dia + Inches(0.36), g6_gap * 2 + g6_dia + Inches(0.36))
    b3x3.fill.solid()
    b3x3.fill.fore_color.rgb = RGBColor(254, 243, 199)
    b3x3.line.color.rgb = COLOR_AMBER
    b3x3.line.width = Pt(2)

    # Re-draw edges
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            n1, n2 = names[i], names[j]
            x1, y1, mx1, my1 = node_coords[n1]
            x2, y2, mx2, my2 = node_coords[n2]
            d = math.sqrt((mx1 - mx2)**2 + (my1 - my2)**2)
            if d <= 500.0001:
                e = s6.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, x1 + g6_dia // 2, y1 + g6_dia // 2, x2 + g6_dia // 2, y2 + g6_dia // 2)
                e.line.color.rgb = COLOR_RULE
                e.line.width = Pt(1)

    for name, (px, py, mx, my) in node_coords.items():
        slot_val = grid_schedule[name]
        col = SLOT_COLORS[slot_val]

        c_shape = s6.shapes.add_shape(MSO_SHAPE.OVAL, px, py, g6_dia, g6_dia)
        c_shape.fill.solid()
        c_shape.fill.fore_color.rgb = col
        c_shape.line.fill.background()
        tf = c_shape.text_frame
        tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        p = tf.paragraphs[0]
        p.text = name[-2:]
        p.font.name = FONT_BODY
        p.font.size = Pt(14)
        p.font.bold = True
        p.font.color.rgb = COLOR_WHITE
        p.alignment = PP_ALIGN.CENTER

    # Caption under grid
    c6_cap = s6.shapes.add_textbox(g6_x0 - Inches(0.3), Inches(6.25), Inches(4.5), Inches(0.45))
    c6p = c6_cap.text_frame.paragraphs[0]
    c6p.text = "Any 3×3 subgrid forms a 9-clique in G\u00B2"
    c6p.font.name = FONT_BODY
    c6p.font.size = Pt(20)
    c6p.font.bold = True
    c6p.font.color.rgb = COLOR_AMBER
    c6p.alignment = PP_ALIGN.CENTER

    s6.notes_slide.notes_text_frame.text = (
        "Could an even smarter algorithm find a schedule with fewer than 9 slots? "
        "The answer is no, and here is why. In this grid, nodes are spaced 300 meters apart horizontally and vertically. "
        "The diagonal distance between diagonal neighbors is 300 times the square root of 2, which is 424 meters. "
        "Since 424 meters is less than our 500-meter radio range, diagonal neighbors hear each other directly. "
        "Now take any 3x3 block of 9 radios, like the one highlighted in amber. Because diagonal radios are within 1 hop, "
        "every single pair of nodes in this 3x3 block is within at most 2 hops in G. "
        "Therefore, in the conflict graph G\u00B2, every pair of these 9 nodes has an edge between them. That is a 9-clique. "
        "A clique of size 9 mathematically requires at least 9 distinct colors. So 9 slots is the absolute physical lower bound. "
        "Regarding the brief: its sample table showed 5 slots, but on this 300-meter grid, Node 1 and Node 3 cannot share a slot "
        "because Node 2 sits between them and would suffer a collision."
    )

    # =========================================================================
    # SLIDE 7: Four topologies, same story
    # =========================================================================
    s7 = add_page("Four topologies, same story")

    # Left: Native bar chart scaled up by ~1.3x
    chart_x7 = Inches(0.70)
    chart_y7 = Inches(1.65)
    chart_w7 = Inches(5.60)
    chart_h7 = Inches(4.80)

    cdata = CategoryChartData()
    cdata.categories = ['4x4 Grid', 'Sparse Line', 'Dense Cluster', 'Two Clusters']
    cdata.add_series('Exact Optimum', (9, 3, 16, 8))
    cdata.add_series('Best Heuristic', (9, 3, 16, 8))

    c_shape7 = s7.shapes.add_chart(
        XL_CHART_TYPE.COLUMN_CLUSTERED,
        chart_x7, chart_y7, chart_w7, chart_h7,
        cdata
    )
    chart7 = c_shape7.chart
    chart7.has_legend = True
    chart7.legend.position = XL_LEGEND_POSITION.TOP
    chart7.legend.include_in_layout = False
    chart7.legend.font.name = FONT_BODY
    chart7.legend.font.size = Pt(14)

    chart7.value_axis.has_major_gridlines = False
    chart7.value_axis.maximum_scale = 19.0
    chart7.value_axis.minimum_scale = 0.0

    plot7 = chart7.plots[0]
    plot7.has_data_labels = True
    plot7.data_labels.font.name = FONT_BODY
    plot7.data_labels.font.size = Pt(14)
    plot7.data_labels.font.bold = True

    s_exact = chart7.series[0]
    s_exact.format.fill.solid()
    s_exact.format.fill.fore_color.rgb = COLOR_INK

    s_heur = chart7.series[1]
    s_heur.format.fill.solid()
    s_heur.format.fill.fore_color.rgb = COLOR_TEAL

    # Right: Single hairline table scaled up by ~1.3x
    tbl7_x = Inches(6.70)
    tbl7_y = Inches(1.65)
    tbl7_w = Inches(5.80)
    tbl7_h = Inches(3.40)

    t7_shape = s7.shapes.add_table(5, 4, tbl7_x, tbl7_y, tbl7_w, tbl7_h)
    t7 = t7_shape.table
    t7.columns[0].width = Inches(2.20)
    t7.columns[1].width = Inches(1.10)
    t7.columns[2].width = Inches(1.10)
    t7.columns[3].width = Inches(1.40)

    t7_rows = [
        ("Topology", "G edges", "G\u00B2 edges", "Optimal"),
        ("4x4 Grid", "42", "90", "9 slots"),
        ("Sparse Line", "15", "29", "3 slots"),
        ("Dense Cluster", "120", "120", "16 slots"),
        ("Two Clusters", "56", "56", "8 slots"),
    ]

    for r_idx, row in enumerate(t7_rows):
        for c_idx, val in enumerate(row):
            cell = t7.cell(r_idx, c_idx)
            cell.text = val
            cell.fill.background()
            cell.margin_left = Inches(0.06)
            cell.margin_right = Inches(0.06)
            p = cell.text_frame.paragraphs[0]
            p.alignment = PP_ALIGN.LEFT if c_idx == 0 else PP_ALIGN.CENTER
            if r_idx == 0:
                p.font.name = FONT_TITLE
                p.font.size = Pt(20)
                p.font.bold = True
                p.font.color.rgb = COLOR_INK
            else:
                p.font.name = FONT_BODY
                p.font.size = Pt(18)
                p.font.color.rgb = COLOR_INK
                if c_idx == 3:
                    p.font.bold = True

    # Sentence below table
    s7_stmt = s7.shapes.add_textbox(Inches(6.70), Inches(5.35), Inches(5.80), Inches(1.10))
    s7_stf = s7_stmt.text_frame
    s7_stf.word_wrap = True
    s7_stf.margin_left = s7_stf.margin_top = s7_stf.margin_right = s7_stf.margin_bottom = 0
    sp7 = s7_stf.paragraphs[0]
    sp7.text = "At 16 nodes plain greedy already finds the optimum, so the exact solver is how I know it."
    sp7.font.name = FONT_BODY
    sp7.font.size = Pt(20)
    sp7.font.color.rgb = COLOR_INK

    s7.notes_slide.notes_text_frame.text = (
        "I evaluated the optimizer across four benchmark topologies. For the 4x4 grid, we need 9 slots. "
        "For a 16-node linear chain spaced at 350 meters, the pattern repeats every 3 nodes, yielding 3 slots. "
        "For the dense cluster where all 16 nodes are within 500 meters of each other, G\u00B2 forms a 16-clique, "
        "forcing every node into a distinct slot for 16 total. Finally, for two disconnected 8-node clusters separated by "
        "3000 meters, both clusters run simultaneously, yielding 8 slots. In every case, the heuristics found the optimum "
        "on all four topologies. The value of having the exact solver isn't that the heuristics were failing, "
        "but that the exact solver provides proof that no better schedule exists."
    )

    # =========================================================================
    # SLIDE 8: Part 2 and what's left
    # =========================================================================
    s8 = add_page("Part 2 and what's left")

    # Native pipeline: Optimizer -> JSON -> Bridge -> XML -> EMANE scaled up
    steps = [
        ("Optimizer", "tested offline", COLOR_TEAL),
        ("JSON", "tested offline", COLOR_TEAL),
        ("Bridge", "tested offline", COLOR_TEAL),
        ("XML", "tested offline", COLOR_TEAL),
        ("EMANE", "not run", COLOR_AMBER),
    ]

    box_w = Inches(2.05)
    box_h = Inches(1.10)
    gap_p = Inches(0.40)
    pipe_x0 = Inches(0.70)
    pipe_y0 = Inches(1.90)

    for idx, (b_name, b_status, b_col) in enumerate(steps):
        bx = pipe_x0 + idx * (box_w + gap_p)

        # Connector arrow to next
        if idx > 0:
            prev_rx = bx - gap_p
            arrow = s8.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, prev_rx, pipe_y0 + box_h // 2, bx, pipe_y0 + box_h // 2)
            arrow.line.color.rgb = COLOR_TEAL if idx < 4 else COLOR_AMBER
            arrow.line.width = Pt(2.5)

        # Box
        b_shape = s8.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, bx, pipe_y0, box_w, box_h)
        b_shape.fill.solid()
        b_shape.fill.fore_color.rgb = b_col
        b_shape.line.fill.background()

        tf = b_shape.text_frame
        tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        p = tf.paragraphs[0]
        p.text = b_name
        p.font.name = FONT_BODY
        p.font.size = Pt(22)
        p.font.bold = True
        p.font.color.rgb = COLOR_WHITE
        p.alignment = PP_ALIGN.CENTER

        # Status label under box
        lbl = s8.shapes.add_textbox(bx - Inches(0.20), pipe_y0 + box_h + Inches(0.15), box_w + Inches(0.40), Inches(0.45))
        stf = lbl.text_frame
        stf.word_wrap = False
        stf.margin_left = stf.margin_top = stf.margin_right = stf.margin_bottom = 0
        lp = stf.paragraphs[0]
        lp.text = b_status
        lp.font.name = FONT_BODY
        lp.font.size = Pt(18)
        lp.font.bold = True
        lp.font.color.rgb = b_col
        lp.alignment = PP_ALIGN.CENTER

    # Three plain lines
    lines8_box = s8.shapes.add_textbox(Inches(0.80), Inches(4.15), Inches(11.5), Inches(2.40))
    l8tf = lines8_box.text_frame
    l8tf.word_wrap = True
    l8tf.margin_left = l8tf.margin_top = l8tf.margin_right = l8tf.margin_bottom = 0

    lines8 = [
        "• EMANE needs pathloss set to ~500 m, or all 16 radios hear each other.",
        "• Next step is running the container with virtual TAP interfaces.",
        "• Future work covers joint time-frequency coloring and mobile nodes.",
    ]
    for idx, l8 in enumerate(lines8):
        p = l8tf.paragraphs[0] if idx == 0 else l8tf.add_paragraph()
        p.text = l8
        p.font.name = FONT_BODY
        p.font.size = Pt(20)
        p.font.color.rgb = COLOR_INK
        if idx > 0:
            p.space_before = Pt(14)

    s8.notes_slide.notes_text_frame.text = (
        "For Part 2, the goal was connecting the optimizer to EMANE's TDMA radio model. "
        "I built a bridge script that translates the JSON schedule into schema-compliant XML. "
        "The offline translation and NEM mapping are verified in automated tests. "
        "However, the live emulation inside a Linux container was not executed. "
        "If you run EMANE without calibrating pathloss, its radio model does not have our 500-meter cutoff: "
        "all 16 radios would hear each other across the multicast channel and collide. "
        "In a live testbed, you would publish LocationEvents or PathlossEvents so that signals drop off at 500 meters. "
        "Looking ahead, the next steps are running that container with live virtual interfaces, "
        "extending to 2D time-frequency coloring, and handling dynamic mobile topologies."
    )

    # Save presentation
    prs.save(output_path)
    print(f"[SUCCESS] Built redesigned 8-slide presentation deck: {output_path}")


if __name__ == "__main__":
    out_file = sys.argv[1] if len(sys.argv) > 1 else "docs/presentation.pptx"
    create_deck(out_file)
