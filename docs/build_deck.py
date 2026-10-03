"""
docs/build_deck.py
Builds the professional, publication-quality 8-slide presentation deck
for TDMA Schedule Optimizer in 16:9 widescreen format (13.333 x 7.5 in).
All diagrams, tables, and charts are rendered with native PowerPoint shapes and charts.
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
from pptx.enum.chart import XL_CHART_TYPE, XL_LEGEND_POSITION, XL_TICK_MARK

# -----------------------------------------------------------------------------
# Color Palette & Font Hierarchy
# -----------------------------------------------------------------------------
COLOR_BG_CONTENT   = RGBColor(246, 243, 236)  # Warm off-white #F6F3EC
COLOR_BG_DARK      = RGBColor(18, 60, 70)     # Deep teal-navy #123C46
COLOR_TITLE        = RGBColor(18, 60, 70)     # Deep teal-navy #123C46
COLOR_TEAL         = RGBColor(15, 118, 110)   # Teal accent #0F766E
COLOR_AMBER        = RGBColor(217, 119, 6)    # Amber highlight #D97706
COLOR_RED          = RGBColor(180, 35, 24)    # Muted conflict red #B42318
COLOR_WHITE        = RGBColor(255, 255, 255)  # White #FFFFFF
COLOR_BORDER       = RGBColor(228, 223, 211)  # Warm grey border #E4DFD3
COLOR_TEXT_DARK    = RGBColor(30, 41, 59)     # Slate 800 #1E293B
COLOR_TEXT_MUTED   = RGBColor(100, 116, 139)  # Slate 500 #64748B
COLOR_BADGE_AMBER  = RGBColor(254, 243, 199)  # Light amber #FEF3C7
COLOR_BADGE_TEAL   = RGBColor(204, 251, 241)  # Light teal #CCFBF1
COLOR_LINE_GREY    = RGBColor(203, 213, 225)  # Slate 300 #CBD5E1

FONT_TITLE = "Georgia"
FONT_BODY  = "Calibri"


def create_deck(output_path="docs/presentation.pptx"):
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.500)
    blank_layout = prs.slide_layouts[6]

    # -------------------------------------------------------------------------
    # Base Helper Functions
    # -------------------------------------------------------------------------
    def add_base_content_slide(title_text, slide_num):
        slide = prs.slides.add_slide(blank_layout)

        # Background fill
        bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(7.500))
        bg.fill.solid()
        bg.fill.fore_color.rgb = COLOR_BG_CONTENT
        bg.line.fill.background()

        # Left slim accent bar
        bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(0.14), Inches(7.500))
        bar.fill.solid()
        bar.fill.fore_color.rgb = COLOR_TEAL
        bar.line.fill.background()

        # Title (Full sentence statement)
        t_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.45), Inches(11.8), Inches(0.85))
        tf = t_box.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0
        p = tf.paragraphs[0]
        p.text = title_text
        p.font.name = FONT_TITLE
        p.font.size = Pt(28)
        p.font.bold = True
        p.font.color.rgb = COLOR_TITLE

        # Footer line & text
        footer_box = slide.shapes.add_textbox(Inches(0.8), Inches(7.05), Inches(7.0), Inches(0.35))
        ftf = footer_box.text_frame
        ftf.margin_left = ftf.margin_top = ftf.margin_right = ftf.margin_bottom = 0
        fp = ftf.paragraphs[0]
        fp.text = "Athish M | TDMA Schedule Optimizer"
        fp.font.name = FONT_BODY
        fp.font.size = Pt(10)
        fp.font.color.rgb = COLOR_TEXT_MUTED

        # Slide Number
        num_box = slide.shapes.add_textbox(Inches(11.5), Inches(7.05), Inches(1.0), Inches(0.35))
        ntf = num_box.text_frame
        ntf.margin_left = ntf.margin_top = ntf.margin_right = ntf.margin_bottom = 0
        np = ntf.paragraphs[0]
        np.text = f"{slide_num} / 8"
        np.alignment = PP_ALIGN.RIGHT
        np.font.name = FONT_BODY
        np.font.size = Pt(10)
        np.font.color.rgb = COLOR_TEXT_MUTED

        return slide

    def add_card(slide, left, top, width, height, bg_color=COLOR_WHITE, border_color=COLOR_BORDER, stripe_color=None, stripe_width=0.08):
        card = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top, width, height)
        card.fill.solid()
        card.fill.fore_color.rgb = bg_color
        if border_color:
            card.line.color.rgb = border_color
            card.line.width = Pt(1)
        else:
            card.line.fill.background()

        if stripe_color:
            stripe = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top, Inches(stripe_width), height)
            stripe.fill.solid()
            stripe.fill.fore_color.rgb = stripe_color
            stripe.line.fill.background()

        return card

    # =========================================================================
    # SLIDE 1: TITLE (Dark Background)
    # =========================================================================
    s1 = prs.slides.add_slide(blank_layout)
    bg1 = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(7.500))
    bg1.fill.solid()
    bg1.fill.fore_color.rgb = COLOR_BG_DARK
    bg1.line.fill.background()

    # Left accent bar in amber
    bar1 = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(0.18), Inches(7.500))
    bar1.fill.solid()
    bar1.fill.fore_color.rgb = COLOR_AMBER
    bar1.line.fill.background()

    # Kicker
    k_box = s1.shapes.add_textbox(Inches(1.2), Inches(1.1), Inches(11.0), Inches(0.4))
    ktf = k_box.text_frame
    ktf.margin_left = ktf.margin_top = ktf.margin_right = ktf.margin_bottom = 0
    kp = ktf.paragraphs[0]
    kp.text = "WIRELESS PROTOCOL DEVELOPMENT | TAKE-HOME TASK"
    kp.font.name = FONT_BODY
    kp.font.size = Pt(13)
    kp.font.bold = True
    kp.font.color.rgb = COLOR_AMBER

    # Title
    t1_box = s1.shapes.add_textbox(Inches(1.2), Inches(1.55), Inches(11.0), Inches(1.2))
    t1_tf = t1_box.text_frame
    t1_tf.word_wrap = True
    t1_tf.margin_left = t1_tf.margin_top = t1_tf.margin_right = t1_tf.margin_bottom = 0
    t1_p = t1_tf.paragraphs[0]
    t1_p.text = "Packing a radio network into the fewest time slots"
    t1_p.font.name = FONT_TITLE
    t1_p.font.size = Pt(40)
    t1_p.font.bold = True
    t1_p.font.color.rgb = COLOR_WHITE

    # One-line Subtitle
    sub1_box = s1.shapes.add_textbox(Inches(1.2), Inches(2.9), Inches(11.0), Inches(0.5))
    sub1_tf = sub1_box.text_frame
    sub1_tf.margin_left = sub1_tf.margin_top = sub1_tf.margin_right = sub1_tf.margin_bottom = 0
    sub1_p = sub1_tf.paragraphs[0]
    sub1_p.text = "distance-2 graph coloring, spatial reuse, exact-optimum benchmark, EMANE bridge"
    sub1_p.font.name = FONT_BODY
    sub1_p.font.size = Pt(17)
    sub1_p.font.color.rgb = RGBColor(209, 213, 219)

    # 3 Stat Cards (Horizontal row)
    stat_data = [
        ("16", "radios, 500 m range"),
        ("9", "slots on the 4x4 grid, proven optimal"),
        ("47", "automated tests passing"),
    ]
    card_w = Inches(3.45)
    card_h = Inches(1.80)
    start_x = Inches(1.2)
    gap_x = Inches(0.32)
    top_y = Inches(3.70)

    for idx, (num, desc) in enumerate(stat_data):
        cx = start_x + idx * (card_w + gap_x)
        c = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, cx, top_y, card_w, card_h)
        c.fill.solid()
        c.fill.fore_color.rgb = RGBColor(24, 76, 88)
        c.line.color.rgb = RGBColor(45, 120, 135)
        c.line.width = Pt(1)

        # Top amber line on stat card
        t_line = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, cx, top_y, card_w, Inches(0.06))
        t_line.fill.solid()
        t_line.fill.fore_color.rgb = COLOR_AMBER
        t_line.line.fill.background()

        st_box = s1.shapes.add_textbox(cx + Inches(0.25), top_y + Inches(0.25), card_w - Inches(0.5), Inches(1.3))
        stf = st_box.text_frame
        stf.word_wrap = True
        stf.margin_left = stf.margin_top = stf.margin_right = stf.margin_bottom = 0
        p_num = stf.paragraphs[0]
        p_num.text = num
        p_num.font.name = FONT_TITLE
        p_num.font.size = Pt(44)
        p_num.font.bold = True
        p_num.font.color.rgb = COLOR_AMBER

        p_desc = stf.add_paragraph()
        p_desc.text = desc
        p_desc.font.name = FONT_BODY
        p_desc.font.size = Pt(14)
        p_desc.font.color.rgb = COLOR_WHITE
        p_desc.space_before = Pt(4)

    # Author
    auth_box = s1.shapes.add_textbox(Inches(1.2), Inches(6.15), Inches(11.0), Inches(0.4))
    atf = auth_box.text_frame
    atf.margin_left = atf.margin_top = atf.margin_right = atf.margin_bottom = 0
    ap = atf.paragraphs[0]
    ap.text = "Athish M  •  athishm2007@gmail.com"
    ap.font.name = FONT_BODY
    ap.font.size = Pt(14)
    ap.font.color.rgb = RGBColor(156, 163, 175)

    s1.notes_slide.notes_text_frame.text = (
        "Wireless Protocol Development Take-Home Presentation.\n"
        "Presenter: Athish M.\n"
        "Core Technical Achievement:\n"
        "- Complete TDMA scheduling engine that minimizes frame length K under joint Distance-1 and Distance-2 constraints.\n"
        "- Implements 5 heuristics and 2 exact solvers with symmetry breaking.\n"
        "- Mathematically proves the 4x4 grid optimum is exactly 9 slots.\n"
        "- Independent BFS verifier validates correctness with zero shared code.\n"
        "- Offline EMANE integration bridge translates schedules into schema-compliant XML."
    )

    # =========================================================================
    # SLIDE 2: THE PROBLEM
    # =========================================================================
    s2 = add_base_content_slide("Two ways to collide, one way to save slots", 2)

    # Left Column: Intro + 3 Rule Cards
    left_x = Inches(0.8)
    left_w = Inches(5.6)

    # Intro sentence
    intro_box = s2.shapes.add_textbox(left_x, Inches(1.45), left_w, Inches(0.75))
    itf = intro_box.text_frame
    itf.word_wrap = True
    itf.margin_left = itf.margin_top = itf.margin_right = itf.margin_bottom = 0
    ip = itf.paragraphs[0]
    ip.text = (
        "TDMA: one frequency, repeating frame of K slots, fewer slots means "
        "each radio talks more often. Transmission constraints govern conflict-freedom:"
    )
    ip.font.name = FONT_BODY
    ip.font.size = Pt(14)
    ip.font.color.rgb = COLOR_TEXT_DARK

    # 3 Rule Cards
    rules = [
        ("Rule 1: Direct Link Collision", "Adjacent radios within 500 m direct range collide if transmitting concurrently. Requires distinct slots.", COLOR_RED),
        ("Rule 2: Hidden Terminal Collision", "Two non-adjacent radios with a shared neighbour corrupt reception at that mutual node. Requires distinct slots.", COLOR_RED),
        ("Rule 3: Spatial Reuse", "Radios 3+ hops apart cannot interfere with each other's receptions and safely share the same timeslot, saving frame capacity.", COLOR_TEAL),
    ]
    card_y = Inches(2.35)
    card_h = Inches(1.35)
    gap_y = Inches(0.18)

    for r_title, r_desc, col in rules:
        add_card(s2, left_x, card_y, left_w, card_h, stripe_color=col, stripe_width=0.10)
        c_box = s2.shapes.add_textbox(left_x + Inches(0.25), card_y + Inches(0.15), left_w - Inches(0.4), card_h - Inches(0.3))
        ctf = c_box.text_frame
        ctf.word_wrap = True
        ctf.margin_left = ctf.margin_top = ctf.margin_right = ctf.margin_bottom = 0
        cp1 = ctf.paragraphs[0]
        cp1.text = r_title
        cp1.font.name = FONT_BODY
        cp1.font.size = Pt(15)
        cp1.font.bold = True
        cp1.font.color.rgb = col

        cp2 = ctf.add_paragraph()
        cp2.text = r_desc
        cp2.font.name = FONT_BODY
        cp2.font.size = Pt(14)
        cp2.font.color.rgb = COLOR_TEXT_DARK
        cp2.space_before = Pt(4)

        card_y += card_h + gap_y

    # Right Column: Native Diagram Panel
    right_x = Inches(6.75)
    right_w = Inches(5.75)
    panel_h = Inches(5.35)
    add_card(s2, right_x, Inches(1.45), right_w, panel_h)

    # Panel Title
    pt_box = s2.shapes.add_textbox(right_x + Inches(0.4), Inches(1.70), right_w - Inches(0.8), Inches(0.4))
    pt_tf = pt_box.text_frame
    pt_tf.margin_left = pt_tf.margin_top = pt_tf.margin_right = pt_tf.margin_bottom = 0
    pt_p = pt_tf.paragraphs[0]
    pt_p.text = "Hidden Terminal Collision Mechanism"
    pt_p.font.name = FONT_TITLE
    pt_p.font.size = Pt(17)
    pt_p.font.bold = True
    pt_p.font.color.rgb = COLOR_TITLE

    # Draw Native Diagram: A -> B <- C
    node_dia = Inches(0.85)
    node_y = Inches(3.0)
    node_a_x = right_x + Inches(0.65)
    node_b_x = right_x + Inches(2.45)
    node_c_x = right_x + Inches(4.25)

    # Solid line A-B
    line_ab = s2.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, node_a_x + node_dia // 2, node_y + node_dia // 2, node_b_x + node_dia // 2, node_y + node_dia // 2)
    line_ab.line.color.rgb = COLOR_RED
    line_ab.line.width = Pt(3)

    # Solid line B-C
    line_bc = s2.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, node_b_x + node_dia // 2, node_y + node_dia // 2, node_c_x + node_dia // 2, node_y + node_dia // 2)
    line_bc.line.color.rgb = COLOR_TITLE
    line_bc.line.width = Pt(3)

    # Distance labels
    d1_box = s2.shapes.add_textbox(node_a_x + Inches(0.6), node_y - Inches(0.45), Inches(1.3), Inches(0.35))
    d1_tf = d1_box.text_frame
    d1_p = d1_tf.paragraphs[0]
    d1_p.text = "under 500 m"
    d1_p.font.name = FONT_BODY
    d1_p.font.size = Pt(12)
    d1_p.font.bold = True
    d1_p.font.color.rgb = COLOR_RED
    d1_p.alignment = PP_ALIGN.CENTER

    d2_box = s2.shapes.add_textbox(node_b_x + Inches(0.6), node_y - Inches(0.45), Inches(1.3), Inches(0.35))
    d2_tf = d2_box.text_frame
    d2_p = d2_tf.paragraphs[0]
    d2_p.text = "under 500 m"
    d2_p.font.name = FONT_BODY
    d2_p.font.size = Pt(12)
    d2_p.font.bold = True
    d2_p.font.color.rgb = COLOR_TITLE
    d2_p.alignment = PP_ALIGN.CENTER

    # Dashed red arc between A and C across the top
    arc = s2.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, node_a_x + node_dia // 2, node_y - Inches(0.6), node_c_x + node_dia // 2, node_y - Inches(0.6))
    arc.line.color.rgb = COLOR_RED
    arc.line.width = Pt(2)
    # python-pptx doesn't have direct dash enum, but line is clearly styled and labeled

    arc_box = s2.shapes.add_textbox(node_a_x + Inches(1.2), node_y - Inches(1.0), Inches(2.2), Inches(0.35))
    atf2 = arc_box.text_frame
    ap2 = atf2.paragraphs[0]
    ap2.text = "--- out of range (> 500 m) ---"
    ap2.font.name = FONT_BODY
    ap2.font.size = Pt(12)
    ap2.font.bold = True
    ap2.font.color.rgb = COLOR_RED
    ap2.alignment = PP_ALIGN.CENTER

    # Nodes (True circles: width == height)
    nodes_info = [
        (node_a_x, "A", COLOR_RED, "Hidden Terminal A"),
        (node_b_x, "B", COLOR_TEAL, "Shared Receiver B"),
        (node_c_x, "C", COLOR_TITLE, "Hidden Terminal C"),
    ]
    for nx, label, col, sub in nodes_info:
        circ = s2.shapes.add_shape(MSO_SHAPE.OVAL, nx, node_y, node_dia, node_dia)
        circ.fill.solid()
        circ.fill.fore_color.rgb = col
        circ.line.fill.background()
        tf = circ.text_frame
        tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        p = tf.paragraphs[0]
        p.text = label
        p.font.name = FONT_TITLE
        p.font.size = Pt(22)
        p.font.bold = True
        p.font.color.rgb = COLOR_WHITE
        p.alignment = PP_ALIGN.CENTER

        # Sub label below node
        s_box = s2.shapes.add_textbox(nx - Inches(0.35), node_y + node_dia + Inches(0.1), node_dia + Inches(0.7), Inches(0.55))
        stf = s_box.text_frame
        stf.word_wrap = True
        stf.margin_left = stf.margin_top = stf.margin_right = stf.margin_bottom = 0
        sp = stf.paragraphs[0]
        sp.text = sub
        sp.font.name = FONT_BODY
        sp.font.size = Pt(13)
        sp.font.bold = True
        sp.font.color.rgb = col
        sp.alignment = PP_ALIGN.CENTER

    # Warning / collision caption box at bottom of panel
    c_cap = s2.shapes.add_shape(MSO_SHAPE.RECTANGLE, right_x + Inches(0.4), Inches(5.1), right_w - Inches(0.8), Inches(1.3))
    c_cap.fill.solid()
    c_cap.fill.fore_color.rgb = COLOR_BADGE_AMBER
    c_cap.line.color.rgb = COLOR_AMBER
    c_cap.line.width = Pt(1)

    cap_tf = c_cap.text_frame
    cap_tf.word_wrap = True
    cap_tf.margin_left = Inches(0.2)
    cap_tf.margin_right = Inches(0.2)
    cap_p = cap_tf.paragraphs[0]
    cap_p.text = "A and C are out of range, yet if both transmit in the same slot they collide at B."
    cap_p.font.name = FONT_BODY
    cap_p.font.size = Pt(14)
    cap_p.font.bold = True
    cap_p.font.color.rgb = RGBColor(146, 64, 14)
    cap_p.alignment = PP_ALIGN.CENTER

    s2.notes_slide.notes_text_frame.text = (
        "The Physical Challenge of Multi-Hop TDMA:\n"
        "- Single omnidirectional carrier frequency with radio range R = 500.0 m.\n"
        "- Direct collision: radios within 500 m must not share timeslots.\n"
        "- Hidden terminal problem: A and C cannot hear each other, but if both emit in slot t, packet superposition at shared receiver B causes unrecoverable SINR degradation.\n"
        "- Distance-2 coloring requirement: two radios sharing a neighbor cannot share a slot.\n"
        "- Spatial reuse: radios separated by 3 or more hops can safely transmit concurrently."
    )

    # =========================================================================
    # SLIDE 3: THE MODEL
    # =========================================================================
    s3 = add_base_content_slide("Distance-2 coloring is just ordinary coloring of the squared graph", 3)

    # Left Column: 3 Numbered Steps
    left_x = Inches(0.8)
    left_w = Inches(5.6)
    step_y = Inches(1.45)
    step_h = Inches(1.65)
    step_gap = Inches(0.18)

    steps_data = [
        ("Step 1: Build Physical Graph G", "(1) Build G, edge if distance <= 500 m (exactly 500 counts, 1e-9 tolerance). Represents direct radio visibility.", COLOR_TEAL),
        ("Step 2: Construct Conflict Graph G²", "(2) Square it, G^2, using nx.power(G, 2). Adds edges between 2-hop neighbours so hidden terminals become adjacent.", COLOR_TEAL),
        ("Step 3: Vertex Color the Conflict Graph G²", "(3) Colour G^2, colour = slot, pairs 3+ hops apart stay unconnected so they may reuse a colour. Distance-2 coloring on G ≡ ordinary coloring on G².", COLOR_AMBER),
    ]

    for title_s, desc_s, col_s in steps_data:
        add_card(s3, left_x, step_y, left_w, step_h, stripe_color=col_s, stripe_width=0.10)
        s_box = s3.shapes.add_textbox(left_x + Inches(0.25), step_y + Inches(0.15), left_w - Inches(0.4), step_h - Inches(0.3))
        stf = s_box.text_frame
        stf.word_wrap = True
        stf.margin_left = stf.margin_top = stf.margin_right = stf.margin_bottom = 0
        p1 = stf.paragraphs[0]
        p1.text = title_s
        p1.font.name = FONT_TITLE
        p1.font.size = Pt(16)
        p1.font.bold = True
        p1.font.color.rgb = col_s

        p2 = stf.add_paragraph()
        p2.text = desc_s
        p2.font.name = FONT_BODY
        p2.font.size = Pt(14)
        p2.font.color.rgb = COLOR_TEXT_DARK
        p2.space_before = Pt(4)

        step_y += step_h + step_gap

    # Right Column: Top Diagram + Bottom Bounds Card
    right_x = Inches(6.75)
    right_w = Inches(5.75)

    # Right Top Panel: 4-Node Line Diagram
    top_panel_h = Inches(2.55)
    add_card(s3, right_x, Inches(1.45), right_w, top_panel_h)

    rtt_box = s3.shapes.add_textbox(right_x + Inches(0.35), Inches(1.65), right_w - Inches(0.7), Inches(0.35))
    rttf = rtt_box.text_frame
    rttf.margin_left = rttf.margin_top = rttf.margin_right = rttf.margin_bottom = 0
    rtp = rttf.paragraphs[0]
    rtp.text = "4-Node Line: Safe Spatial Reuse Across 3 Hops"
    rtp.font.name = FONT_TITLE
    rtp.font.size = Pt(16)
    rtp.font.bold = True
    rtp.font.color.rgb = COLOR_TITLE

    # Draw 4 nodes A-B-C-D in line
    line_nodes = [
        (right_x + Inches(0.55), "A", "Slot 0", COLOR_AMBER),
        (right_x + Inches(1.85), "B", "Slot 1", COLOR_TEAL),
        (right_x + Inches(3.15), "C", "Slot 2", COLOR_TITLE),
        (right_x + Inches(4.45), "D", "Slot 0", COLOR_AMBER),
    ]
    node_dia4 = Inches(0.68)
    line_node_y = Inches(2.25)

    # Physical edges A-B, B-C, C-D
    for i in range(3):
        x1 = line_nodes[i][0] + node_dia4 // 2
        x2 = line_nodes[i+1][0] + node_dia4 // 2
        ln = s3.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, x1, line_node_y + node_dia4 // 2, x2, line_node_y + node_dia4 // 2)
        ln.line.color.rgb = COLOR_LINE_GREY
        ln.line.width = Pt(3)

    for nx, lbl, slot_lbl, col in line_nodes:
        c = s3.shapes.add_shape(MSO_SHAPE.OVAL, nx, line_node_y, node_dia4, node_dia4)
        c.fill.solid()
        c.fill.fore_color.rgb = col
        c.line.fill.background()
        tf = c.text_frame
        tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        p = tf.paragraphs[0]
        p.text = lbl
        p.font.name = FONT_TITLE
        p.font.size = Pt(17)
        p.font.bold = True
        p.font.color.rgb = COLOR_WHITE
        p.alignment = PP_ALIGN.CENTER

        # Slot badge below
        s_box = s3.shapes.add_textbox(nx - Inches(0.2), line_node_y + node_dia4 + Inches(0.08), node_dia4 + Inches(0.4), Inches(0.3))
        stf = s_box.text_frame
        stf.margin_left = stf.margin_top = stf.margin_right = stf.margin_bottom = 0
        sp = stf.paragraphs[0]
        sp.text = slot_lbl
        sp.font.name = FONT_BODY
        sp.font.size = Pt(13)
        sp.font.bold = True
        sp.font.color.rgb = col
        sp.alignment = PP_ALIGN.CENTER

    # Caption note for 4-node line
    note_box = s3.shapes.add_textbox(right_x + Inches(0.35), Inches(3.45), right_w - Inches(0.7), Inches(0.45))
    ntf = note_box.text_frame
    ntf.word_wrap = True
    ntf.margin_left = ntf.margin_top = ntf.margin_right = ntf.margin_bottom = 0
    np = ntf.paragraphs[0]
    np.text = "A and D are 3 hops apart, so they reuse slot 0"
    np.font.name = FONT_BODY
    np.font.size = Pt(14)
    np.font.bold = True
    np.font.color.rgb = COLOR_AMBER
    np.alignment = PP_ALIGN.CENTER

    # Right Bottom Panel: Bounds & Complexity Card
    btm_panel_y = Inches(4.20)
    btm_panel_h = Inches(2.60)
    add_card(s3, right_x, btm_panel_y, right_w, btm_panel_h, stripe_color=COLOR_TEAL, stripe_width=0.10)

    bt_box = s3.shapes.add_textbox(right_x + Inches(0.35), btm_panel_y + Inches(0.2), right_w - Inches(0.6), btm_panel_h - Inches(0.4))
    bttf = bt_box.text_frame
    bttf.word_wrap = True
    bttf.margin_left = bttf.margin_top = bttf.margin_right = bttf.margin_bottom = 0

    bp1 = bttf.paragraphs[0]
    bp1.text = "Mathematical Bounds on Chromatic Number"
    bp1.font.name = FONT_TITLE
    bp1.font.size = Pt(16)
    bp1.font.bold = True
    bp1.font.color.rgb = COLOR_TITLE

    bp2 = bttf.add_paragraph()
    bp2.text = "clique number <= minimum slots <= max degree of G^2 + 1"
    bp2.font.name = FONT_TITLE
    bp2.font.size = Pt(16)
    bp2.font.bold = True
    bp2.font.color.rgb = COLOR_TEAL
    bp2.space_before = Pt(8)

    bp3 = bttf.add_paragraph()
    bp3.text = "ω(G²)  ≤  χ(G²)  ≤  Δ(G²) + 1"
    bp3.font.name = FONT_BODY
    bp3.font.size = Pt(15)
    bp3.font.bold = True
    bp3.font.color.rgb = COLOR_TITLE
    bp3.space_before = Pt(4)

    bp4 = bttf.add_paragraph()
    bp4.text = (
        "Finding the true minimum is NP-hard so heuristics are used. "
        "The clique lower bound ω(G²) proves when a heuristic has reached true optimality."
    )
    bp4.font.name = FONT_BODY
    bp4.font.size = Pt(14)
    bp4.font.color.rgb = COLOR_TEXT_DARK
    bp4.space_before = Pt(6)

    s3.notes_slide.notes_text_frame.text = (
        "Mathematical Graph Formulation:\n"
        "- Graph squaring: nx.power(G, 2) creates edges between all vertex pairs with shortest-path distance <= 2.\n"
        "- Equivalence theorem: distance-2 vertex coloring on physical topology G is mathematically isomorphic to ordinary vertex coloring on conflict graph G^2.\n"
        "- Exact 500.0 m boundary condition: Euclidean distance with 1e-9 tolerance ensures physical boundary nodes are connected.\n"
        "- Complexity: graph coloring on general graphs and unit disk graphs is NP-hard.\n"
        "- Lower bound: maximum clique size of G^2 (omega).\n"
        "- Upper bound: maximum conflict degree + 1 (Delta + 1)."
    )

    # =========================================================================
    # SLIDE 4: ALGORITHMS
    # =========================================================================
    s4 = add_base_content_slide("Five heuristics, two exact solvers, one independent checker", 4)

    # Native Table: Method | Idea | Cost
    tbl_x = Inches(0.8)
    tbl_y = Inches(1.45)
    tbl_w = Inches(11.733)
    tbl_h = Inches(3.70)

    rows = 8
    cols = 3
    t_shape = s4.shapes.add_table(rows, cols, tbl_x, tbl_y, tbl_w, tbl_h)
    tbl = t_shape.table
    tbl.columns[0].width = Inches(2.9)
    tbl.columns[1].width = Inches(6.0)
    tbl.columns[2].width = Inches(2.833)

    table_data = [
        ("Method", "Idea", "Cost"),
        ("Largest-degree-first", "Orders nodes by conflict degree; colors high-degree bottlenecks first", "O(V log V + E) (~0.06 ms)"),
        ("DSATUR", "Greedy saturation: picks node with highest colored-neighbor diversity", "O(V^2 + E) (~0.15 ms)"),
        ("Smallest-last", "Reverse elimination ordering bounded by smallest degree in subgraph", "O(V + E) (~0.20 ms)"),
        ("Random restarts", "1000 seeded orders, keep the best schedule discovered", "1000 orders (~24 ms)"),
        ("Local search", "Kempe-chain swaps plus tabu search, up to 2000 steps to trim top color", "Local search (~50 ms)"),
        ("CP-SAT exact", "0-1 ILP with maximum-clique pre-coloring for symmetry breaking", "Exact optimum (~0.8 ms)"),
        ("Branch and bound exact", "Backtracking with DSATUR branching, no dependencies, used as fallback", "Pure Python fallback"),
    ]

    for r_idx, row in enumerate(table_data):
        for c_idx, cell_text in enumerate(row):
            cell = tbl.cell(r_idx, c_idx)
            cell.text = cell_text
            p = cell.text_frame.paragraphs[0]
            p.alignment = PP_ALIGN.LEFT if c_idx < 2 else PP_ALIGN.CENTER
            if r_idx == 0:
                p.font.name = FONT_BODY
                p.font.size = Pt(14)
                p.font.bold = True
                p.font.color.rgb = COLOR_WHITE
                cell.fill.solid()
                cell.fill.fore_color.rgb = COLOR_TITLE
            else:
                p.font.name = FONT_BODY
                p.font.size = Pt(13)
                p.font.color.rgb = COLOR_TEXT_DARK
                if c_idx == 0:
                    p.font.bold = True
                cell.fill.solid()
                cell.fill.fore_color.rgb = COLOR_WHITE if r_idx % 2 == 1 else RGBColor(241, 245, 249)

    # Bottom Card: Solver & Checker Architecture
    card_b_y = Inches(5.35)
    card_b_h = Inches(1.45)
    add_card(s4, tbl_x, card_b_y, tbl_w, card_b_h, stripe_color=COLOR_AMBER, stripe_width=0.10)

    cb_box = s4.shapes.add_textbox(tbl_x + Inches(0.25), card_b_y + Inches(0.15), tbl_w - Inches(0.5), card_b_h - Inches(0.3))
    cbtf = cb_box.text_frame
    cbtf.word_wrap = True
    cbtf.margin_left = cbtf.margin_top = ctf.margin_right = ctf.margin_bottom = 0

    cbp1 = cbtf.paragraphs[0]
    cbp1.text = "Best-of-Heuristics + Exact Yardstick + Independent Verifier"
    cbp1.font.name = FONT_TITLE
    cbp1.font.size = Pt(16)
    cbp1.font.bold = True
    cbp1.font.color.rgb = COLOR_TITLE

    cbp2 = cbtf.add_paragraph()
    cbp2.text = (
        "the schedule is the best result across methods, the exact solver is the yardstick, "
        "and a separate BFS verifier checks the final schedule. Zero shared code between "
        "schedule generation and schedule verification."
    )
    cbp2.font.name = FONT_BODY
    cbp2.font.size = Pt(14)
    cbp2.font.color.rgb = COLOR_TEXT_DARK
    cbp2.space_before = Pt(4)

    s4.notes_slide.notes_text_frame.text = (
        "Algorithmic Architecture:\n"
        "1. Largest-Degree-First (Welsh-Powell): rapid baseline coloring conflict hubs first.\n"
        "2. DSATUR (Brelaz): dynamic saturation tracking provides high-quality heuristic bounds.\n"
        "3. Smallest-Last: orders vertices based on degeneracy, bounding chromatic number.\n"
        "4. Randomized Restarts: explores 1000 pseudo-random seeded orderings deterministically.\n"
        "5. Local Search: executes Kempe-chain 2-color interchanges to eliminate highest color classes.\n"
        "6. Google OR-Tools CP-SAT: exact integer programming with max-clique symmetry breaking.\n"
        "7. Pure-Python Branch-and-Bound: fallback exact solver when external C-libraries are unavailable.\n"
        "8. Independent Verifier: checks BFS hop-distances on physical graph G with zero shared logic."
    )

    # =========================================================================
    # SLIDE 5: THE 4x4 GRID
    # =========================================================================
    # Run verifier before drawing grid
    grid_schedule_file = Path("examples/grid_schedule.json")
    if not grid_schedule_file.exists():
        raise FileNotFoundError(f"Missing required schedule file: {grid_schedule_file}")

    with open(grid_schedule_file, "r") as f:
        grid_data = json.load(f)

    # Import verifier and verify
    sys.path.insert(0, str(Path("src").resolve()))
    from tdma.verify import verify_schedule
    from tdma.graph import build_connectivity_graph, parse_coordinates

    G_grid = build_connectivity_graph(parse_coordinates(grid_data["coordinates"]), 500.0)
    is_valid, msgs = verify_schedule(G_grid, grid_data["schedule"])
    if not is_valid:
        raise ValueError(f"CRITICAL: grid_schedule.json failed verifier! {msgs}")

    s5 = add_base_content_slide("The 4x4 grid needs 9 slots, and four corners share one", 5)

    # Left Column: Native 4x4 Grid Diagram Panel
    left_x = Inches(0.8)
    left_w = Inches(5.6)
    panel5_h = Inches(5.35)
    add_card(s5, left_x, Inches(1.45), left_w, panel5_h)

    # Slot Palette for 9 Slots
    SLOT_COLORS = [
        RGBColor(15, 118, 110),   # 0: Teal
        RGBColor(37, 99, 235),    # 1: Blue
        RGBColor(124, 58, 237),   # 2: Purple
        RGBColor(219, 39, 119),   # 3: Pink
        RGBColor(5, 150, 105),    # 4: Emerald
        RGBColor(202, 138, 4),    # 5: Ochre
        RGBColor(71, 85, 105),    # 6: Slate
        RGBColor(30, 58, 138),    # 7: Dark Blue
        RGBColor(217, 119, 6),    # 8: Amber (Corners!)
    ]

    # Grid geometry
    # 4 columns (x=0, 300, 600, 900)
    # 4 rows (y=900 at top to y=0 at bottom)
    grid_start_x = left_x + Inches(0.65)
    grid_gap_x   = Inches(1.35)
    grid_start_y = Inches(1.85)
    grid_gap_y   = Inches(1.10)
    n_dia        = Inches(0.65)

    # Compute node screen positions
    node_positions = {}
    for r in range(4): # visual row 0 at top (y=900) down to row 3 at bottom (y=0)
        math_y = (3 - r) * 300.0
        for c in range(4):
            math_x = c * 300.0
            node_idx = (3 - r) * 4 + c + 1
            node_name = f"Node_{node_idx:02d}"
            px = grid_start_x + c * grid_gap_x
            py = grid_start_y + r * grid_gap_y
            node_positions[node_name] = (px, py, math_x, math_y)

    # Draw Physical Edges (dist <= 500 m)
    # Horizontal (300 m), Vertical (300 m), Diagonal (424.26 m)
    node_names_list = list(node_positions.keys())
    for i in range(len(node_names_list)):
        for j in range(i + 1, len(node_names_list)):
            n1 = node_names_list[i]
            n2 = node_names_list[j]
            x1, y1, mx1, my1 = node_positions[n1]
            x2, y2, mx2, my2 = node_positions[n2]
            dist = math.sqrt((mx1 - mx2)**2 + (my1 - my2)**2)
            if dist <= 500.0001:
                edge = s5.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, x1 + n_dia // 2, y1 + n_dia // 2, x2 + n_dia // 2, y2 + n_dia // 2)
                edge.line.color.rgb = COLOR_LINE_GREY
                edge.line.width = Pt(1)

    # Draw Nodes & Rings for corners
    schedule = grid_data["schedule"]
    corners = {"Node_01", "Node_04", "Node_13", "Node_16"}

    for node_name, (px, py, mx, my) in node_positions.items():
        slot_num = schedule[node_name]
        col = SLOT_COLORS[slot_num]

        # If corner, draw dashed amber ring around it
        if node_name in corners:
            ring_pad = Inches(0.12)
            ring = s5.shapes.add_shape(MSO_SHAPE.OVAL, px - ring_pad, py - ring_pad, n_dia + ring_pad*2, n_dia + ring_pad*2)
            ring.fill.background()
            ring.line.color.rgb = COLOR_AMBER
            ring.line.width = Pt(2.5)

        # Node circle (True circle)
        c_shape = s5.shapes.add_shape(MSO_SHAPE.OVAL, px, py, n_dia, n_dia)
        c_shape.fill.solid()
        c_shape.fill.fore_color.rgb = col
        c_shape.line.fill.background()

        tf = c_shape.text_frame
        tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0
        p1 = tf.paragraphs[0]
        p1.text = node_name[-2:]
        p1.font.name = FONT_BODY
        p1.font.size = Pt(13)
        p1.font.bold = True
        p1.font.color.rgb = COLOR_WHITE
        p1.alignment = PP_ALIGN.CENTER

        p2 = tf.add_paragraph()
        p2.text = f"s{slot_num}"
        p2.font.name = FONT_BODY
        p2.font.size = Pt(10)
        p2.font.color.rgb = COLOR_WHITE
        p2.alignment = PP_ALIGN.CENTER

    # Caption at bottom of grid panel
    grid_cap_box = s5.shapes.add_textbox(left_x + Inches(0.3), Inches(6.25), left_w - Inches(0.6), Inches(0.45))
    gtf = grid_cap_box.text_frame
    gtf.margin_left = gtf.margin_top = gtf.margin_right = gtf.margin_bottom = 0
    gp = gtf.paragraphs[0]
    gp.text = "Four corners (Node_01, 04, 13, 16) ringed in amber: all reuse Slot 8"
    gp.font.name = FONT_BODY
    gp.font.size = Pt(13)
    gp.font.bold = True
    gp.font.color.rgb = COLOR_AMBER
    gp.alignment = PP_ALIGN.CENTER

    # Right Column: Big Stats + Proof Steps + Note Card
    right_x = Inches(6.75)
    right_w = Inches(5.75)

    # 3 Big Stats
    grid_stats = [
        ("42", "edges in G"),
        ("90", "edges in G^2"),
        ("15", "max degree in G^2"),
    ]
    s_w = Inches(1.80)
    s_h = Inches(1.05)
    for idx, (s_num, s_desc) in enumerate(grid_stats):
        sx = right_x + idx * (s_w + Inches(0.17))
        add_card(s5, sx, Inches(1.45), s_w, s_h, stripe_color=COLOR_TEAL, stripe_width=0.06)
        st_box = s5.shapes.add_textbox(sx + Inches(0.12), Inches(1.52), s_w - Inches(0.2), s_h - Inches(0.15))
        stf = st_box.text_frame
        stf.word_wrap = True
        stf.margin_left = stf.margin_top = stf.margin_right = stf.margin_bottom = 0
        p1 = stf.paragraphs[0]
        p1.text = s_num
        p1.font.name = FONT_TITLE
        p1.font.size = Pt(28)
        p1.font.bold = True
        p1.font.color.rgb = COLOR_TITLE
        p2 = stf.add_paragraph()
        p2.text = s_desc
        p2.font.name = FONT_BODY
        p2.font.size = Pt(12)
        p2.font.color.rgb = COLOR_TEXT_MUTED

    # "Why 9 is the floor" Card
    proof_y = Inches(2.65)
    proof_h = Inches(2.75)
    add_card(s5, right_x, proof_y, right_w, proof_h, stripe_color=COLOR_AMBER, stripe_width=0.10)

    pf_box = s5.shapes.add_textbox(right_x + Inches(0.25), proof_y + Inches(0.15), right_w - Inches(0.4), proof_h - Inches(0.3))
    pftf = pf_box.text_frame
    pftf.word_wrap = True
    pftf.margin_left = pftf.margin_top = pftf.margin_right = pftf.margin_bottom = 0

    pfp0 = pftf.paragraphs[0]
    pfp0.text = "Why 9 is the floor:"
    pfp0.font.name = FONT_TITLE
    pfp0.font.size = Pt(16)
    pfp0.font.bold = True
    pfp0.font.color.rgb = COLOR_TITLE

    proof_steps = [
        "(1) diagonal 300*sqrt(2) = 424 m is in range (<= 500 m).",
        "(2) any 3x3 block has all pairs within 2 hops in physical graph G.",
        "(3) so 9 radios form a 9-clique in G^2 (every pair conflicts).",
        "(4) no schedule can use fewer than 9 and the solver finds exactly 9.",
    ]
    for step_text in proof_steps:
        p = pftf.add_paragraph()
        p.text = step_text
        p.font.name = FONT_BODY
        p.font.size = Pt(13)
        p.font.color.rgb = COLOR_TEXT_DARK
        p.space_before = Pt(4)

    # Note Card at bottom
    note_card_y = Inches(5.55)
    note_card_h = Inches(1.25)
    add_card(s5, right_x, note_card_y, right_w, note_card_h, bg_color=RGBColor(248, 250, 252))

    nc_box = s5.shapes.add_textbox(right_x + Inches(0.2), note_card_y + Inches(0.12), right_w - Inches(0.4), note_card_h - Inches(0.24))
    nctf = nc_box.text_frame
    nctf.word_wrap = True
    nctf.margin_left = nctf.margin_top = nctf.margin_right = nctf.margin_bottom = 0
    ncp = nctf.paragraphs[0]
    ncp.text = "the brief's 5-slot sample is a format example with partial coordinates, not a target. The mathematical 9-clique lower bound proves 9 slots is the global optimum."
    ncp.font.name = FONT_BODY
    ncp.font.size = Pt(13)
    ncp.font.color.rgb = COLOR_TEXT_MUTED

    s5.notes_slide.notes_text_frame.text = (
        "4x4 Grid Benchmark Analysis:\n"
        "Node-to-slot assignment verified against CLI output:\n"
        "Node_01: Slot 8, Node_02: Slot 4, Node_03: Slot 5, Node_04: Slot 8, "
        "Node_05: Slot 6, Node_06: Slot 0, Node_07: Slot 1, Node_08: Slot 6, "
        "Node_09: Slot 7, Node_10: Slot 2, Node_11: Slot 3, Node_12: Slot 7, "
        "Node_13: Slot 8, Node_14: Slot 4, Node_15: Slot 5, Node_16: Slot 8.\n"
        "Spatial reuse proof:\n"
        "- The four corners (Node_01, Node_04, Node_13, Node_16) are separated by 3 or more hops in G.\n"
        "- They safely share Slot 8 without mutual collision.\n"
        "- All heuristics and both exact solvers converge on 9 slots."
    )

    # =========================================================================
    # SLIDE 6: BENCHMARKS
    # =========================================================================
    s6 = add_base_content_slide("Every heuristic matched the exact optimum on all four topologies", 6)

    # Left Column: Native Clustered Bar Chart
    left_x = Inches(0.8)
    left_w = Inches(5.6)
    chart_y = Inches(1.45)
    chart_h = Inches(5.35)

    add_card(s6, left_x, chart_y, left_w, chart_h)

    # Add Native Chart
    chart_data = CategoryChartData()
    chart_data.categories = ['4x4 Grid', 'Sparse Line', 'Dense Cluster', 'Two Clusters']
    chart_data.add_series('Exact Optimum', (9, 3, 16, 8))
    chart_data.add_series('Best Heuristic', (9, 3, 16, 8))

    chart_shape = s6.shapes.add_chart(
        XL_CHART_TYPE.COLUMN_CLUSTERED,
        left_x + Inches(0.2), chart_y + Inches(0.3), left_w - Inches(0.4), chart_h - Inches(0.6),
        chart_data
    )
    chart = chart_shape.chart
    chart.has_legend = True
    chart.legend.position = XL_LEGEND_POSITION.TOP
    chart.legend.include_in_layout = False
    chart.legend.font.name = FONT_BODY
    chart.legend.font.size = Pt(12)

    plot = chart.plots[0]
    plot.has_data_labels = True
    plot.data_labels.font.name = FONT_BODY
    plot.data_labels.font.size = Pt(12)
    plot.data_labels.font.bold = True

    chart.value_axis.has_major_gridlines = False
    chart.value_axis.maximum_scale = 19.0
    chart.value_axis.minimum_scale = 0.0

    series_exact = chart.series[0]
    series_exact.format.fill.solid()
    series_exact.format.fill.fore_color.rgb = COLOR_TITLE

    series_heur = chart.series[1]
    series_heur.format.fill.solid()
    series_heur.format.fill.fore_color.rgb = COLOR_TEAL

    # Right Column: Table + 2 Cards
    right_x = Inches(6.75)
    right_w = Inches(5.75)

    # Native Table: Topology | G edges | G^2 edges | Optimal
    t6_shape = s6.shapes.add_table(5, 4, right_x, Inches(1.45), right_w, Inches(1.95))
    t6 = t6_shape.table
    t6.columns[0].width = Inches(2.3)
    t6.columns[1].width = Inches(1.1)
    t6.columns[2].width = Inches(1.1)
    t6.columns[3].width = Inches(1.25)

    t6_data = [
        ("Topology", "G edges", "G^2 edges", "Optimal"),
        ("4x4 Grid (300 m)", "42", "90", "9 slots"),
        ("Sparse Linear", "15", "29", "3 slots"),
        ("Dense Cluster", "120", "120", "16 slots"),
        ("Two Clusters", "56", "56", "8 slots"),
    ]
    for r_idx, row in enumerate(t6_data):
        for c_idx, val in enumerate(row):
            cell = t6.cell(r_idx, c_idx)
            cell.text = val
            p = cell.text_frame.paragraphs[0]
            p.alignment = PP_ALIGN.LEFT if c_idx == 0 else PP_ALIGN.CENTER
            if r_idx == 0:
                p.font.name = FONT_BODY
                p.font.size = Pt(13)
                p.font.bold = True
                p.font.color.rgb = COLOR_WHITE
                cell.fill.solid()
                cell.fill.fore_color.rgb = COLOR_TITLE
            else:
                p.font.name = FONT_BODY
                p.font.size = Pt(12)
                p.font.color.rgb = COLOR_TEXT_DARK
                if c_idx == 3:
                    p.font.bold = True
                    p.font.color.rgb = COLOR_TEAL
                cell.fill.solid()
                cell.fill.fore_color.rgb = COLOR_WHITE if r_idx % 2 == 1 else RGBColor(241, 245, 249)

    # Card 1: What the numbers say
    c1_y = Inches(3.60)
    c1_h = Inches(1.55)
    add_card(s6, right_x, c1_y, right_w, c1_h, stripe_color=COLOR_TEAL, stripe_width=0.10)
    c1_box = s6.shapes.add_textbox(right_x + Inches(0.25), c1_y + Inches(0.12), right_w - Inches(0.4), c1_h - Inches(0.24))
    c1_tf = c1_box.text_frame
    c1_tf.word_wrap = True
    c1_tf.margin_left = c1_tf.margin_top = c1_tf.margin_right = c1_tf.margin_bottom = 0
    p1 = c1_tf.paragraphs[0]
    p1.text = "What the numbers say:"
    p1.font.name = FONT_TITLE
    p1.font.size = Pt(15)
    p1.font.bold = True
    p1.font.color.rgb = COLOR_TITLE
    p2 = c1_tf.add_paragraph()
    p2.text = (
        "dense cluster is a 16-clique so 16 is forced; "
        "two clusters 3000 m apart reuse slots 0 to 7, halving the frame."
    )
    p2.font.name = FONT_BODY
    p2.font.size = Pt(13)
    p2.font.color.rgb = COLOR_TEXT_DARK
    p2.space_before = Pt(4)

    # Card 2: Cost on 16 nodes
    c2_y = Inches(5.30)
    c2_h = Inches(1.50)
    add_card(s6, right_x, c2_y, right_w, c2_h, stripe_color=COLOR_AMBER, stripe_width=0.10)
    c2_box = s6.shapes.add_textbox(right_x + Inches(0.25), c2_y + Inches(0.12), right_w - Inches(0.4), c2_h - Inches(0.24))
    c2_tf = c2_box.text_frame
    c2_tf.word_wrap = True
    c2_tf.margin_left = c2_tf.margin_top = c2_tf.margin_right = c2_tf.margin_bottom = 0
    p1 = c2_tf.paragraphs[0]
    p1.text = "Cost on 16 nodes:"
    p1.font.name = FONT_TITLE
    p1.font.size = Pt(15)
    p1.font.bold = True
    p1.font.color.rgb = COLOR_TITLE
    p2 = c2_tf.add_paragraph()
    p2.text = (
        "greedy and DSATUR under 0.3 ms, 1000 restarts about 15 to 37 ms, "
        "exact solve about 0.2 to 1.2 ms."
    )
    p2.font.name = FONT_BODY
    p2.font.size = Pt(13)
    p2.font.color.rgb = COLOR_TEXT_DARK
    p2.space_before = Pt(4)

    s6.notes_slide.notes_text_frame.text = (
        "Benchmark Results Analysis:\n"
        "At 16 nodes simple greedy already reaches the optimum, and the exact solver is what lets us prove it; "
        "heuristics matter more as n grows.\n"
        "Key topology insights:\n"
        "- 4x4 Grid: 42 physical edges, 90 conflict edges -> exactly 9 slots.\n"
        "- Sparse Line: 15 physical edges, 29 conflict edges -> exactly 3 slots.\n"
        "- Dense Cluster: 120 physical edges, full 16-clique -> 16 slots forced (0 spatial reuse).\n"
        "- Two Clusters (3000 m separation): full spatial reuse across disjoint components -> 8 slots (50% frame compression)."
    )

    # =========================================================================
    # SLIDE 7: VERIFICATION AND PART 2
    # =========================================================================
    s7 = add_base_content_slide("Verified independently; EMANE bridge designed and tested offline", 7)

    # Top Row: Two Cards
    card_w7 = Inches(5.6)
    card_h7 = Inches(2.65)
    top_y7  = Inches(1.45)

    # Top Left Card: Independent Verifier
    add_card(s7, Inches(0.8), top_y7, card_w7, card_h7, stripe_color=COLOR_TEAL, stripe_width=0.10)
    v_box = s7.shapes.add_textbox(Inches(1.05), top_y7 + Inches(0.15), card_w7 - Inches(0.4), card_h7 - Inches(0.3))
    vtf = v_box.text_frame
    vtf.word_wrap = True
    vtf.margin_left = vtf.margin_top = vtf.margin_right = vtf.margin_bottom = 0
    vp1 = vtf.paragraphs[0]
    vp1.text = "Independent Verifier"
    vp1.font.name = FONT_TITLE
    vp1.font.size = Pt(16)
    vp1.font.bold = True
    vp1.font.color.rgb = COLOR_TITLE

    v_bullets = [
        "BFS hop distances on raw G, no shared code with colouring.",
        "Checks one slot per node, contiguous slots 0..K-1, no pair within 2 hops shares a slot.",
        "47 of 47 tests pass, including property tests and a fallback solver that matches CP-SAT.",
    ]
    for b in v_bullets:
        p = vtf.add_paragraph()
        p.text = "• " + b
        p.font.name = FONT_BODY
        p.font.size = Pt(13)
        p.font.color.rgb = COLOR_TEXT_DARK
        p.space_before = Pt(3)

    # Top Right Card: EMANE Range Modelling
    add_card(s7, Inches(6.9), top_y7, card_w7, card_h7, stripe_color=COLOR_AMBER, stripe_width=0.10)
    e_box = s7.shapes.add_textbox(Inches(7.15), top_y7 + Inches(0.15), card_w7 - Inches(0.4), card_h7 - Inches(0.3))
    etf = e_box.text_frame
    etf.word_wrap = True
    etf.margin_left = etf.margin_top = etf.margin_right = etf.margin_bottom = 0
    ep1 = etf.paragraphs[0]
    ep1.text = "EMANE Range Modelling (Design Only)"
    ep1.font.name = FONT_TITLE
    ep1.font.size = Pt(16)
    ep1.font.bold = True
    ep1.font.color.rgb = COLOR_TITLE

    e_bullets = [
        "EMANE does not know the 500 m rule natively.",
        "Locations and pathloss must be calibrated so effective range is about 500 m.",
        "Otherwise all 16 radios hear each other globally and the schedule would collide.",
        "Status: planned, not run on a live Linux kernel testbed.",
    ]
    for b in e_bullets:
        p = etf.add_paragraph()
        p.text = "• " + b
        p.font.name = FONT_BODY
        p.font.size = Pt(13)
        p.font.color.rgb = COLOR_TEXT_DARK
        p.space_before = Pt(3)

    # Bottom Pipeline Panel
    btm_p_y = Inches(4.30)
    btm_p_h = Inches(2.50)
    btm_p_w = Inches(11.7)
    add_card(s7, Inches(0.8), btm_p_y, btm_p_w, btm_p_h)

    pipe_title_box = s7.shapes.add_textbox(Inches(1.05), btm_p_y + Inches(0.12), btm_p_w - Inches(0.5), Inches(0.35))
    ptf = pipe_title_box.text_frame
    ptf.margin_left = ptf.margin_top = ptf.margin_right = ptf.margin_bottom = 0
    pp = ptf.paragraphs[0]
    pp.text = "EMANE Schedule Translation Pipeline & Boundary"
    pp.font.name = FONT_TITLE
    pp.font.size = Pt(16)
    pp.font.bold = True
    pp.font.color.rgb = COLOR_TITLE

    # 5 native boxes
    pipeline_steps = [
        ("Python\nOptimizer", COLOR_TEAL),
        ("Schedule\nJSON", COLOR_TEAL),
        ("Bridge\nScript", COLOR_TEAL),
        ("Schedule\nXML", COLOR_TEAL),
        ("EMANE\nNodes", COLOR_AMBER),
    ]
    box_w = Inches(1.75)
    box_h = Inches(0.75)
    box_y = btm_p_y + Inches(0.55)
    start_bx = Inches(1.1)
    gap_bx   = Inches(0.60)

    for idx, (b_text, b_col) in enumerate(pipeline_steps):
        bx = start_bx + idx * (box_w + gap_bx)
        b_shape = s7.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, bx, box_y, box_w, box_h)
        b_shape.fill.solid()
        b_shape.fill.fore_color.rgb = b_col
        b_shape.line.fill.background()

        tf = b_shape.text_frame
        tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0
        p = tf.paragraphs[0]
        p.text = b_text
        p.font.name = FONT_BODY
        p.font.size = Pt(13)
        p.font.bold = True
        p.font.color.rgb = COLOR_WHITE
        p.alignment = PP_ALIGN.CENTER

        # Connector arrow to next box
        if idx < 4:
            arr = s7.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, bx + box_w, box_y + box_h // 2, bx + box_w + gap_bx, box_y + box_h // 2)
            arr.line.color.rgb = COLOR_TEAL if idx < 3 else COLOR_AMBER
            arr.line.width = Pt(2.5)

    # Badges below boxes: Tested Offline vs Design Only
    b1_shape = s7.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(1.1), btm_p_y + Inches(1.45), Inches(8.45), Inches(0.85))
    b1_shape.fill.solid()
    b1_shape.fill.fore_color.rgb = COLOR_BADGE_TEAL
    b1_shape.line.color.rgb = COLOR_TEAL
    b1_shape.line.width = Pt(1)
    b1_tf = b1_shape.text_frame
    b1_tf.word_wrap = True
    b1_p = b1_tf.paragraphs[0]
    b1_p.text = "TESTED OFFLINE: JSON to XML translation, node-to-NEM mapping, round-trip schema check"
    b1_p.font.name = FONT_BODY
    b1_p.font.size = Pt(13)
    b1_p.font.bold = True
    b1_p.font.color.rgb = COLOR_TEAL
    b1_p.alignment = PP_ALIGN.CENTER

    b2_shape = s7.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(9.85), btm_p_y + Inches(1.45), Inches(2.35), Inches(0.85))
    b2_shape.fill.solid()
    b2_shape.fill.fore_color.rgb = COLOR_BADGE_AMBER
    b2_shape.line.color.rgb = COLOR_AMBER
    b2_shape.line.width = Pt(1)
    b2_tf = b2_shape.text_frame
    b2_tf.word_wrap = True
    b2_p = b2_tf.paragraphs[0]
    b2_p.text = "DESIGN ONLY:\nlive emulation, Docker build, packet-level slot enforcement"
    b2_p.font.name = FONT_BODY
    b2_p.font.size = Pt(11)
    b2_p.font.bold = True
    b2_p.font.color.rgb = COLOR_AMBER
    b2_p.alignment = PP_ALIGN.CENTER

    s7.notes_slide.notes_text_frame.text = (
        "Verification Architecture & EMANE Integration Boundary:\n"
        "- Independent BFS Verifier: checks all generated schedules against the raw physical graph G.\n"
        "- Complete coverage: confirms every node has exactly one slot assignment.\n"
        "- Contiguity: verifies slots form a contiguous interval 0..K-1.\n"
        "- Conflict-freedom: verifies no pairs within 1 or 2 hops share a timeslot.\n"
        "- Test Suite: 47 automated tests covering graph construction, coloring heuristics, exact solvers, CLI, and EMANE bridge.\n"
        "- Part 2 Tested vs Design Boundary:\n"
        "  * TESTED OFFLINE: automated XML translation, NEM ID mapping, round-trip schedule parsing.\n"
        "  * DESIGN ONLY: live RF emulation inside Linux network namespaces, requiring root and TAP interfaces."
    )

    # =========================================================================
    # SLIDE 8: STATUS
    # =========================================================================
    s8 = add_base_content_slide("What is proven, what is pending, and what comes next", 8)

    # 3 Tall Cards across width
    card_w8 = Inches(3.70)
    card_h8 = Inches(5.35)
    card_y8 = Inches(1.45)
    card_gap8 = Inches(0.31)

    cards_data = [
        ("PROVEN", COLOR_TEAL, [
            "9, 3, 16, 8 slots each equal to the exact optimum",
            "independent verifier passes on all topologies",
            "CP-SAT and pure-Python solver agree",
            "47 tests pass on a fresh clone",
            "Exact 500.0 m float tolerance (1e-9 m) and duplicate rejection",
        ]),
        ("NOT YET RUN", COLOR_AMBER, [
            "live EMANE emulation in multi-node container",
            "Docker build and live TAP interface setup",
            "packet-level slot enforcement with ping/iperf",
            "pathloss calibration to about 500 m",
            "deliberate conflict injection test",
        ]),
        ("NEXT", COLOR_TITLE, [
            "multi-channel time x frequency colouring across orthogonal bands",
            "mobility and re-scheduling (DRAND / C-TDMA protocols)",
            "link-level scheduling (directed spatial TDMA)",
            "larger topologies to stress the heuristics (n = 50 to 500)",
        ]),
    ]

    for idx, (head, col, bullets) in enumerate(cards_data):
        cx = Inches(0.8) + idx * (card_w8 + card_gap8)
        add_card(s8, cx, card_y8, card_w8, card_h8)

        # Header banner strip
        banner = s8.shapes.add_shape(MSO_SHAPE.RECTANGLE, cx, card_y8, card_w8, Inches(0.70))
        banner.fill.solid()
        banner.fill.fore_color.rgb = col
        banner.line.fill.background()

        btf = banner.text_frame
        btf.vertical_anchor = MSO_ANCHOR.MIDDLE
        p = btf.paragraphs[0]
        p.text = head
        p.font.name = FONT_TITLE
        p.font.size = Pt(20)
        p.font.bold = True
        p.font.color.rgb = COLOR_WHITE
        p.alignment = PP_ALIGN.CENTER

        # Bullets box
        b_box = s8.shapes.add_textbox(cx + Inches(0.25), card_y8 + Inches(0.85), card_w8 - Inches(0.5), card_h8 - Inches(1.0))
        btf2 = b_box.text_frame
        btf2.word_wrap = True
        btf2.margin_left = btf2.margin_top = btf2.margin_right = btf2.margin_bottom = 0

        for b_idx, b_text in enumerate(bullets):
            bp = btf2.paragraphs[0] if b_idx == 0 else btf2.add_paragraph()
            bp.text = "• " + b_text
            bp.font.name = FONT_BODY
            bp.font.size = Pt(14)
            bp.font.color.rgb = COLOR_TEXT_DARK
            bp.space_before = Pt(8)

    s8.notes_slide.notes_text_frame.text = (
        "Summary & Engineering Assessment:\n"
        "- Proven: mathematical formulation, 5 heuristics, 2 exact solvers, 9-slot grid optimum, independent BFS verifier, and 47 passing tests.\n"
        "- Pending / Not Yet Run: physical over-the-air packet transmission inside live Linux kernel network namespaces and pathloss calibration.\n"
        "- Next steps: multi-channel (time-frequency) coloring, distributed MANET mobility protocols, and link-level STDMA scheduling."
    )

    # Save presentation
    prs.save(output_path)
    print(f"[SUCCESS] Built 8-slide presentation deck: {output_path}")


if __name__ == "__main__":
    out_file = sys.argv[1] if len(sys.argv) > 1 else "docs/presentation.pptx"
    create_deck(out_file)
