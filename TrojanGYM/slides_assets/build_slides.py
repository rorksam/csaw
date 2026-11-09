#!/usr/bin/env python3
"""Build the TrojanGYM overview deck included with the AES course package."""

from pathlib import Path

from PIL import Image, ImageChops
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.xmlchemy import OxmlElement
from pptx.util import Inches, Pt


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "slides_assets"
OUT = ROOT / "TrojanGYM_Overview_Slides.pptx"
LOGO_SOURCE = ASSETS / "nyu_tandon_official.png"
LOGO_CROPPED = ASSETS / "nyu_tandon_logo_cropped.png"

NYU = RGBColor(0x57, 0x06, 0x8C)
DEEP = RGBColor(0x33, 0x06, 0x62)
TEAL = RGBColor(0x00, 0xA9, 0x9D)
INK = RGBColor(0x19, 0x18, 0x1B)
MID = RGBColor(0x62, 0x5C, 0x68)
PALE = RGBColor(0xF4, 0xF0, 0xF7)
LIGHT = RGBColor(0xF7, 0xF7, 0xF8)
LINE = RGBColor(0xD9, 0xD3, 0xDE)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
RED = RGBColor(0xC7, 0x2C, 0x41)
GREEN = RGBColor(0x12, 0x78, 0x64)
AMBER = RGBColor(0xED, 0xA4, 0x16)

FONT = "Arial"
PAPER = "Sreekumar et al., TrojanGYM, arXiv:2601.17178v3 (2026)"


def crop_logo() -> None:
    """Crop only the surrounding white canvas; preserve the official lockup."""
    im = Image.open(LOGO_SOURCE).convert("RGBA")
    rgb = Image.new("RGBA", im.size, (255, 255, 255, 255))
    diff = ImageChops.difference(im, rgb).convert("RGB")
    bbox = diff.getbbox()
    if bbox:
        pad = 30
        left = max(0, bbox[0] - pad)
        top = max(0, bbox[1] - pad)
        right = min(im.width, bbox[2] + pad)
        bottom = min(im.height, bbox[3] + pad)
        im = im.crop((left, top, right, bottom))
    im.save(LOGO_CROPPED)


def set_bg(slide, color):
    fill = slide.background.fill
    fill.solid()
    fill.fore_color.rgb = color


def add_text(
    slide,
    text,
    x,
    y,
    w,
    h,
    size=20,
    color=INK,
    bold=False,
    align=PP_ALIGN.LEFT,
    valign=MSO_ANCHOR.TOP,
    font=FONT,
    margin=0.0,
    line_spacing=1.0,
):
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = box.text_frame
    tf.clear()
    tf.margin_left = Inches(margin)
    tf.margin_right = Inches(margin)
    tf.margin_top = Inches(margin)
    tf.margin_bottom = Inches(margin)
    tf.vertical_anchor = valign
    p = tf.paragraphs[0]
    p.text = text
    p.alignment = align
    p.line_spacing = line_spacing
    p.space_after = Pt(0)
    # PowerPoint represents explicit line breaks as separate runs.  Style every
    # run so LibreOffice does not fall back to black/default text after a break.
    for run in p.runs:
        run.font.name = font
        run.font.size = Pt(size)
        run.font.bold = bold
        run.font.color.rgb = color
    return box


def add_rich_text(slide, runs, x, y, w, h, size=20, color=INK, align=PP_ALIGN.LEFT):
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = box.text_frame
    tf.clear()
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    p = tf.paragraphs[0]
    p.alignment = align
    for spec in runs:
        run = p.add_run()
        run.text = spec[0]
        run.font.name = FONT
        run.font.size = Pt(spec[1] if len(spec) > 1 else size)
        run.font.bold = spec[2] if len(spec) > 2 else False
        run.font.color.rgb = spec[3] if len(spec) > 3 else color
    return box


def add_box(
    slide,
    x,
    y,
    w,
    h,
    fill=WHITE,
    outline=LINE,
    radius=True,
    width=1.2,
):
    kind = MSO_SHAPE.ROUNDED_RECTANGLE if radius else MSO_SHAPE.RECTANGLE
    shape = slide.shapes.add_shape(kind, Inches(x), Inches(y), Inches(w), Inches(h))
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill
    shape.line.color.rgb = outline
    shape.line.width = Pt(width)
    return shape


def set_shape_text(shape, text, size=18, color=INK, bold=False, align=PP_ALIGN.CENTER):
    tf = shape.text_frame
    tf.clear()
    tf.margin_left = Inches(0.10)
    tf.margin_right = Inches(0.10)
    tf.margin_top = Inches(0.06)
    tf.margin_bottom = Inches(0.06)
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]
    p.text = text
    p.alignment = align
    p.space_after = Pt(0)
    for r in p.runs:
        r.font.name = FONT
        r.font.size = Pt(size)
        r.font.bold = bold
        r.font.color.rgb = color


def add_chevron(slide, x, y, w=0.36, h=0.52, color=NYU):
    s = slide.shapes.add_shape(MSO_SHAPE.CHEVRON, Inches(x), Inches(y), Inches(w), Inches(h))
    s.fill.solid()
    s.fill.fore_color.rgb = color
    s.line.fill.background()
    return s


def add_line(slide, x1, y1, x2, y2, color=NYU, width=2.0, dash=None):
    line = slide.shapes.add_connector(
        MSO_CONNECTOR.STRAIGHT, Inches(x1), Inches(y1), Inches(x2), Inches(y2)
    )
    line.line.color.rgb = color
    line.line.width = Pt(width)
    if dash is not None:
        line.line.dash_style = dash
    return line


def add_arrow_line(slide, x1, y1, x2, y2, color=NYU, width=2.0):
    """Add a connector with a visible arrowhead at its end point."""
    line = add_line(slide, x1, y1, x2, y2, color=color, width=width)
    ln = line.line._get_or_add_ln()
    tail = OxmlElement("a:tailEnd")
    tail.set("type", "triangle")
    tail.set("w", "med")
    tail.set("len", "med")
    ln.append(tail)
    return line


def add_logo(slide, x=10.55, y=0.24, w=2.25, white_card=False):
    if white_card:
        add_box(slide, x - 0.16, y - 0.11, w + 0.32, 0.80, fill=WHITE, outline=WHITE)
    slide.shapes.add_picture(str(LOGO_CROPPED), Inches(x), Inches(y), width=Inches(w))


def add_footer(slide, page, dark=False, source=PAPER):
    color = RGBColor(0xD9, 0xC8, 0xE5) if dark else MID
    add_text(slide, source, 0.55, 7.18, 10.8, 0.18, size=8.5, color=color)
    add_text(slide, f"{page:02d}", 12.30, 7.15, 0.46, 0.20, size=9, color=color, align=PP_ALIGN.RIGHT)


def add_title(slide, section, title, subtitle=None, dark=False):
    title_color = WHITE if dark else INK
    section_color = TEAL if dark else NYU
    add_text(slide, section.upper(), 0.55, 0.34, 4.7, 0.25, size=10, bold=True, color=section_color)
    add_text(slide, title, 0.55, 0.67, 10.8, 0.55, size=27, bold=True, color=title_color)
    if subtitle:
        sub_color = RGBColor(0xDD, 0xD4, 0xE4) if dark else MID
        add_text(slide, subtitle, 0.57, 1.26, 11.4, 0.38, size=13, color=sub_color)
    add_logo(slide, white_card=dark)


def add_bullet(slide, heading, body, x, y, w, accent=NYU, dark=False):
    body_color = RGBColor(0xE7, 0xE1, 0xEA) if dark else MID
    dot = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(x), Inches(y + 0.08), Inches(0.12), Inches(0.12))
    dot.fill.solid()
    dot.fill.fore_color.rgb = accent
    dot.line.fill.background()
    add_text(slide, heading, x + 0.22, y, w - 0.22, 0.28, size=16, bold=True, color=WHITE if dark else INK)
    add_text(slide, body, x + 0.22, y + 0.34, w - 0.22, 0.62, size=12.5, color=body_color, line_spacing=1.05)


def build_title_slide(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_bg(slide, DEEP)

    # Decorative feedback-loop motif.
    for i, color in enumerate((NYU, TEAL, RGBColor(0x8F, 0x5B, 0xB5))):
        ring = slide.shapes.add_shape(
            MSO_SHAPE.ARC, Inches(9.20 + i * 0.22), Inches(2.05 + i * 0.16), Inches(3.7 - i * 0.35), Inches(3.7 - i * 0.35)
        )
        ring.fill.background()
        ring.line.color.rgb = color
        ring.line.width = Pt(2.2)

    add_text(slide, "HARDWARE SECURITY • COURSE OVERVIEW", 0.66, 0.58, 6.8, 0.28, size=11, bold=True, color=TEAL)
    add_text(slide, "TrojanGYM", 0.66, 1.18, 7.8, 0.78, size=43, bold=True, color=WHITE)
    add_text(slide, "From one-shot GHOST to\na detector feedback loop", 0.66, 2.05, 7.6, 1.30, size=27, color=WHITE, bold=True)
    add_text(
        slide,
        "How TrojanGYM uses test and detector results to improve each attempt",
        0.70,
        3.55,
        7.4,
        0.52,
        size=15,
        color=RGBColor(0xD9, 0xC8, 0xE5),
    )

    add_box(slide, 8.65, 0.50, 4.05, 0.95, fill=WHITE, outline=WHITE)
    add_logo(slide, x=8.92, y=0.74, w=3.50)

    add_text(
        slide,
        "Saideep Sreekumar*, Zeng Wang*, Akashdeep Saha, Weihua Xiao, Minghao Shao,\n"
        "Muhammad Shafique, Ozgur Sinanoglu, Ramesh Karri, Johann Knechtel",
        0.68,
        5.28,
        11.9,
        0.68,
        size=12.3,
        color=WHITE,
        bold=True,
    )
    add_text(
        slide,
        "NYU Tandon School of Engineering, New York • NYU Abu Dhabi, Abu Dhabi\n"
        "* Equal contribution  |  Published at MLCAD 2026  |  arXiv:2601.17178v3",
        0.68,
        6.08,
        11.2,
        0.55,
        size=10.5,
        color=RGBColor(0xD9, 0xC8, 0xE5),
    )
    add_footer(slide, 1, dark=True)


def build_ghost_flow(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_bg(slide, WHITE)
    add_title(
        slide,
        "01 • Starting point",
        "GHOST: create and check code once",
        "The flow can make Trojan RTL and check whether it builds, but it does not test a detector.",
    )

    xs = [0.70, 3.72, 6.74, 9.76]
    labels = [
        ("INPUT", "Clean RTL\n+ Trojan request"),
        ("GENERATE", "LLM adds\nTrojan logic"),
        ("CHECK", "Compile • simulate\n• synthesize"),
        ("OUTPUT", "Generated\nTrojan RTL"),
    ]
    colors = [PALE, PALE, LIGHT, PALE]
    outlines = [NYU, NYU, AMBER, NYU]
    for i, (x, (tag, body)) in enumerate(zip(xs, labels)):
        add_box(slide, x, 2.04, 2.35, 1.64, fill=colors[i], outline=outlines[i], width=1.7)
        add_text(slide, tag, x + 0.18, 2.22, 1.99, 0.20, size=9.5, bold=True, color=outlines[i])
        add_text(slide, body, x + 0.18, 2.56, 1.99, 0.76, size=15, bold=True, color=INK, valign=MSO_ANCHOR.MIDDLE)
        if i < 3:
            add_chevron(slide, x + 2.51, 2.60, w=0.34, h=0.48, color=NYU)

    add_box(slide, 0.70, 4.33, 3.05, 1.03, fill=RGBColor(0xF1, 0xEC, 0xF5), outline=NYU)
    add_rich_text(
        slide,
        [("Automatic insertion  ", 15, True, INK), ("✓", 18, True, GREEN)],
        0.95,
        4.58,
        2.55,
        0.24,
    )
    add_text(slide, "The LLM can create many examples.", 0.95, 4.92, 2.48, 0.25, size=11, color=MID)

    add_box(slide, 4.02, 4.33, 3.15, 1.03, fill=RGBColor(0xFC, 0xF0, 0xF2), outline=RED)
    add_rich_text(
        slide,
        [("Detector test  ", 15, True, INK), ("×", 18, True, RED)],
        4.27,
        4.58,
        2.65,
        0.24,
    )
    add_text(slide, "No detector is used in this flow.", 4.27, 4.92, 2.65, 0.25, size=11, color=MID)

    # Crossed feedback path.
    add_line(slide, 11.55, 4.04, 4.10, 4.04, color=RED, width=1.4)
    add_text(slide, "NO DETECTOR IN THE FLOW", 7.10, 3.81, 2.42, 0.20, size=9.5, bold=True, color=RED, align=PP_ALIGN.CENTER)
    add_line(slide, 7.98, 3.83, 8.30, 4.25, color=RED, width=2.3)
    add_line(slide, 8.30, 3.83, 7.98, 4.25, color=RED, width=2.3)

    add_text(
        slide,
        "GHOST creates Trojan RTL and checks the code. Testing a detector is the next missing step.",
        0.72,
        5.87,
        11.82,
        0.62,
        size=16,
        bold=True,
        color=DEEP,
        align=PP_ALIGN.CENTER,
    )
    add_footer(slide, 2)


def build_gap(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_bg(slide, LIGHT)
    add_title(
        slide,
        "02 • The gap",
        "Why one run is not enough",
        "Creating valid RTL is useful, but it does not show whether a detector can find the Trojan.",
    )

    add_box(slide, 0.60, 1.92, 5.85, 3.77, fill=WHITE, outline=LINE)
    add_text(slide, "What GHOST can do", 0.93, 2.24, 4.9, 0.38, size=21, bold=True, color=NYU)
    add_bullet(slide, "Create code", "The LLM inserts Trojan logic into real RTL designs.", 0.94, 3.16, 4.95, accent=NYU)
    add_bullet(slide, "Check code", "Compile, simulation, and synthesis show whether the design can run.", 0.94, 4.42, 4.95, accent=NYU)

    add_box(slide, 6.86, 1.92, 5.85, 3.77, fill=DEEP, outline=DEEP)
    add_text(slide, "What is still missing", 7.19, 2.24, 4.9, 0.38, size=21, bold=True, color=TEAL)
    add_bullet(slide, "Test detectors", "Run a detector on each generated design.", 7.20, 2.88, 4.95, accent=TEAL, dark=True)
    add_bullet(slide, "Use the result", "Send the detector result back to the LLM and try again.", 7.20, 3.80, 4.95, accent=TEAL, dark=True)
    add_bullet(slide, "Improve the detector", "Use the new Trojan examples to make the detector stronger.", 7.20, 4.72, 4.95, accent=TEAL, dark=True)

    add_box(slide, 2.08, 6.00, 9.18, 0.60, fill=RGBColor(0xEE, 0xE7, 0xF3), outline=RGBColor(0xEE, 0xE7, 0xF3))
    add_text(slide, "TrojanGYM adds a detector and sends its result back to the LLM.", 2.30, 6.16, 8.76, 0.24, size=16, bold=True, color=DEEP, align=PP_ALIGN.CENTER)
    add_footer(slide, 3)


def build_trojangym_loop(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_bg(slide, DEEP)
    add_title(
        slide,
        "03 • TrojanGYM",
        "Use feedback to improve the next design",
        "If the code fails, fix it. If the GNN finds the Trojan, change it and try again.",
        dark=True,
    )

    # Clear left-to-right main path.
    xs = [0.42, 2.56, 4.70, 6.84]
    tags = ["1 • INPUT", "2 • CREATE", "3 • TEST", "4 • DETECT"]
    bodies = [
        "Clean RTL +\nTrojan request",
        "LLM creates\nTrojan RTL",
        "Compile + run\ntestbench",
        "Robust-GNN4TJ\nchecks the RTL",
    ]
    fills = [WHITE, WHITE, RGBColor(0xFA, 0xF3, 0xE4), RGBColor(0xE6, 0xF5, 0xF3)]
    accents = [NYU, NYU, AMBER, TEAL]
    for i, x in enumerate(xs):
        add_box(slide, x, 2.10, 1.78, 1.42, fill=fills[i], outline=accents[i], width=1.8)
        add_text(slide, tags[i], x + 0.13, 2.30, 1.52, 0.18, size=8.6, bold=True, color=accents[i])
        add_text(slide, bodies[i], x + 0.13, 2.67, 1.52, 0.58, size=13.4, bold=True, color=INK, valign=MSO_ANCHOR.MIDDLE)
        add_chevron(slide, x + 1.84, 2.57, w=0.25, h=0.45, color=NYU if i < 2 else TEAL)

    # Decision and successful exit.
    decision = slide.shapes.add_shape(MSO_SHAPE.DIAMOND, Inches(9.06), Inches(2.03), Inches(1.76), Inches(1.56))
    decision.fill.solid()
    decision.fill.fore_color.rgb = WHITE
    decision.line.color.rgb = RED
    decision.line.width = Pt(1.8)
    set_shape_text(decision, "Trojan\nfound?", size=12.2, color=INK, bold=True)
    add_text(slide, "5 • CHECK", 9.39, 1.86, 1.10, 0.18, size=8.4, bold=True, color=RED, align=PP_ALIGN.CENTER)
    add_chevron(slide, 10.87, 2.57, w=0.25, h=0.45, color=GREEN)
    add_text(slide, "NO", 10.79, 2.27, 0.40, 0.18, size=8.8, bold=True, color=GREEN, align=PP_ALIGN.CENTER)
    done = add_box(slide, 11.18, 2.15, 1.70, 1.34, fill=RGBColor(0xE5, 0xF4, 0xEF), outline=GREEN, width=1.8)
    add_text(slide, "6 • SAVE", 11.32, 2.35, 1.42, 0.18, size=8.6, bold=True, color=GREEN)
    add_text(slide, "Save the valid,\nhard-to-detect\ndesign", 11.32, 2.67, 1.42, 0.58, size=12.1, bold=True, color=GREEN, valign=MSO_ANCHOR.MIDDLE)

    # Labels on the main path.
    add_text(slide, "PASS", 6.45, 2.28, 0.50, 0.18, size=8.8, bold=True, color=GREEN, align=PP_ALIGN.CENTER)

    # Two simple feedback branches: code failure and detector hit.
    add_line(slide, 5.59, 3.52, 5.59, 4.10, color=AMBER, width=2.2)
    add_text(slide, "FAIL", 5.72, 3.75, 0.52, 0.18, size=8.8, bold=True, color=AMBER)
    error_box = add_box(slide, 3.98, 4.12, 3.20, 0.92, fill=RGBColor(0x48, 0x15, 0x70), outline=AMBER, width=1.7)
    set_shape_text(error_box, "Send the compiler or test log\nback to the LLM", size=12.0, color=WHITE, bold=True)

    add_line(slide, 9.94, 3.57, 9.94, 4.10, color=RED, width=2.2)
    add_text(slide, "YES", 10.06, 3.76, 0.52, 0.18, size=8.8, bold=True, color=RED)
    detector_box = add_box(slide, 7.64, 4.12, 4.12, 0.92, fill=RGBColor(0x48, 0x15, 0x70), outline=RED, width=1.7)
    set_shape_text(detector_box, "Send the detection result back\nand ask for a harder-to-detect design", size=11.6, color=WHITE, bold=True)

    retry = add_box(slide, 4.30, 5.49, 5.80, 0.66, fill=RGBColor(0xE8, 0xF4, 0xF2), outline=TEAL, width=1.7)
    set_shape_text(retry, "Update the prompt or RTL  •  Try again", size=13.0, color=DEEP, bold=True)
    add_arrow_line(slide, 5.59, 5.04, 5.59, 5.49, color=AMBER, width=1.8)
    add_arrow_line(slide, 9.70, 5.04, 9.70, 5.49, color=RED, width=1.8)
    add_line(slide, 4.30, 5.82, 3.45, 5.82, color=TEAL, width=2.0)
    add_line(slide, 3.45, 5.82, 3.45, 3.76, color=TEAL, width=2.0)
    up = slide.shapes.add_shape(MSO_SHAPE.UP_ARROW, Inches(3.28), Inches(3.42), Inches(0.34), Inches(0.47))
    up.fill.solid()
    up.fill.fore_color.rgb = TEAL
    up.line.fill.background()

    add_box(slide, 1.18, 6.47, 11.00, 0.38, fill=NYU, outline=NYU)
    add_text(
        slide,
        "TrojanGYM uses two kinds of feedback: fix broken code, or change code that the detector finds.",
        1.38,
        6.56,
        10.60,
        0.18,
        size=11.2,
        color=WHITE,
        bold=True,
        align=PP_ALIGN.CENTER,
    )
    add_footer(slide, 4, dark=True)


def build_comparison(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_bg(slide, WHITE)
    add_title(
        slide,
        "04 • What changed",
        "The detector now helps guide the next attempt",
        "GHOST creates and checks code once. TrojanGYM also tests the detector and uses its result.",
    )

    x0, x1, x2 = 0.55, 3.40, 7.68
    w0, w1, w2 = 2.70, 4.08, 5.10
    add_box(slide, x0, 1.90, w0, 0.61, fill=LIGHT, outline=LINE, radius=False)
    add_box(slide, x1, 1.90, w1, 0.61, fill=RGBColor(0xED, 0xE6, 0xF2), outline=NYU, radius=False)
    add_box(slide, x2, 1.90, w2, 0.61, fill=DEEP, outline=DEEP, radius=False)
    add_text(slide, "DIMENSION", x0 + 0.20, 2.10, w0 - 0.40, 0.20, size=10, bold=True, color=MID)
    add_text(slide, "GHOST", x1 + 0.20, 2.06, w1 - 0.40, 0.24, size=14, bold=True, color=NYU)
    add_text(slide, "TROJANGYM", x2 + 0.20, 2.06, w2 - 0.40, 0.24, size=14, bold=True, color=WHITE)

    rows = [
        ("Generation", "One attempt", "Try, get feedback, and try again"),
        ("Code/test results", "Used as a final check", "Used to fix the RTL"),
        ("Detector check", "Not included in the flow", "Run after the code passes"),
        ("Detector feedback", "None", "Sent back to the LLM"),
        ("Output", "Valid Trojan RTL", "Valid examples that show detector weak points"),
    ]
    y = 2.51
    for idx, (dim, ghost, gym) in enumerate(rows):
        fill = WHITE if idx % 2 == 0 else LIGHT
        for x, w in ((x0, w0), (x1, w1), (x2, w2)):
            add_box(slide, x, y, w, 0.73, fill=fill, outline=LINE, radius=False, width=0.8)
        add_text(slide, dim, x0 + 0.20, y + 0.22, w0 - 0.40, 0.25, size=12.5, bold=True, color=INK)
        add_text(slide, ghost, x1 + 0.20, y + 0.19, w1 - 0.40, 0.32, size=12.3, color=MID)
        add_text(slide, gym, x2 + 0.20, y + 0.19, w2 - 0.40, 0.32, size=12.3, bold=True, color=DEEP)
        y += 0.73

    add_rich_text(
        slide,
        [("Automatic insertion: ", 13, True, INK), ("both ✓", 13, True, GREEN), ("     Uses detector feedback: ", 13, True, INK), ("only TrojanGYM ✓", 13, True, NYU)],
        2.60,
        6.43,
        8.30,
        0.25,
        align=PP_ALIGN.CENTER,
    )
    add_footer(slide, 5)


def build_gnn4tj_detail(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_bg(slide, LIGHT)
    add_title(
        slide,
        "05 • GNN4TJ",
        "How GNN4TJ checks one RTL design",
        "First convert the design into a data-flow graph (DFG), then run four trained GNN models.",
    )

    # RTL-to-DFG path.
    stages = [
        (0.55, "1 • RTL DESIGN", "Verilog RTL\naes_128_… .v", NYU, PALE),
        (2.55, "2 • BUILD GRAPH", "Read signals and\nconnections", AMBER, RGBColor(0xFA, 0xF3, 0xE4)),
        (4.55, "3 • DFG", "Data-flow\ngraph", TEAL, RGBColor(0xE6, 0xF5, 0xF3)),
    ]
    for i, (x, tag, body, accent, fill) in enumerate(stages):
        add_box(slide, x, 2.12, 1.55, 1.34, fill=fill, outline=accent, width=1.7)
        add_text(slide, tag, x + 0.13, 2.33, 1.29, 0.18, size=8.3, bold=True, color=accent)
        add_text(slide, body, x + 0.13, 2.70, 1.29, 0.48, size=12.2, bold=True, color=INK, valign=MSO_ANCHOR.MIDDLE)
        if i < 2:
            add_chevron(slide, x + 1.69, 2.57, w=0.24, h=0.43, color=accent)

    add_box(slide, 0.55, 4.02, 5.55, 1.00, fill=WHITE, outline=LINE)
    add_text(slide, "WHAT IS IN THE DFG?", 0.82, 4.20, 2.20, 0.20, size=9.2, bold=True, color=NYU)
    add_text(slide, "Nodes", 0.82, 4.53, 0.62, 0.20, size=11.4, bold=True, color=INK)
    add_text(slide, "signals, constants, operations", 1.46, 4.53, 2.72, 0.20, size=10.6, color=MID)
    add_text(slide, "Edges", 4.17, 4.53, 0.55, 0.20, size=11.4, bold=True, color=INK)
    add_text(slide, "data flow", 4.73, 4.53, 1.05, 0.20, size=10.6, color=MID)

    add_box(slide, 0.55, 5.18, 5.55, 1.04, fill=RGBColor(0xED, 0xE7, 0xF2), outline=NYU, width=1.2)
    add_text(slide, "WHERE DID THE 4 MODELS COME FROM?", 0.82, 5.35, 3.45, 0.20, size=9.2, bold=True, color=NYU)
    add_text(
        slide,
        "Base method: GNN4TJ (DATE 2021) + HW2VEC (HOST 2021)\n"
        "Retrained in TrojanGYM: 884 clean VeriGen RTLs + 3,536 GHOST/GPT-4 Trojan designs",
        0.82,
        5.65,
        4.98,
        0.42,
        size=9.4,
        bold=True,
        color=DEEP,
    )

    # The same DFG is sent to four separately trained models.
    add_text(slide, "4 TRAINED MODELS", 6.68, 1.72, 2.30, 0.22, size=9.5, bold=True, color=NYU)
    add_text(slide, "EACH MODEL REPORTS", 9.55, 1.72, 2.80, 0.22, size=9.5, bold=True, color=TEAL)
    model_rows = [
        ("HT1 model", "trained: clean vs HT1", NYU),
        ("HT2 model", "trained: clean vs HT2", TEAL),
        ("HT3 model", "trained: clean vs HT3", AMBER),
        ("HT4 model", "trained: clean vs HT4", RED),
    ]
    row_y = [2.03, 2.84, 3.65, 4.46]

    # DFG fan-out bus.
    add_line(slide, 6.10, 2.79, 6.42, 2.79, color=TEAL, width=2.0)
    add_line(slide, 6.42, 2.34, 6.42, 4.77, color=TEAL, width=2.0)
    add_text(slide, "same DFG", 5.94, 1.97, 0.90, 0.20, size=8.4, bold=True, color=TEAL, align=PP_ALIGN.CENTER)

    for (name, trained, accent), y in zip(model_rows, row_y):
        add_arrow_line(slide, 6.42, y + 0.34, 6.68, y + 0.34, color=TEAL, width=1.5)
        add_box(slide, 6.68, y, 2.40, 0.68, fill=WHITE, outline=accent, width=1.5)
        add_text(slide, name, 6.84, y + 0.10, 1.12, 0.20, size=12.2, bold=True, color=accent)
        add_text(slide, trained, 7.82, y + 0.12, 1.08, 0.20, size=8.5, color=MID, align=PP_ALIGN.RIGHT)
        add_chevron(slide, 9.16, y + 0.13, w=0.24, h=0.40, color=accent)
        add_box(slide, 9.48, y, 3.28, 0.68, fill=RGBColor(0xF0, 0xED, 0xF3), outline=LINE, width=0.9)
        add_text(slide, "P(clean)  •  P(trojan)  •  vote", 9.70, y + 0.22, 2.84, 0.22, size=11.1, bold=True, color=DEEP, align=PP_ALIGN.CENTER)

    add_box(slide, 6.68, 5.38, 6.08, 0.84, fill=DEEP, outline=DEEP)
    add_text(slide, "COMBINE THE 4 VOTES", 6.95, 5.57, 1.75, 0.20, size=9.2, bold=True, color=TEAL)
    add_text(slide, "Any Trojan vote → Trojan   |   Otherwise → Clean", 8.55, 5.55, 3.92, 0.26, size=12.0, bold=True, color=WHITE, align=PP_ALIGN.CENTER)

    add_box(slide, 0.67, 6.33, 12.00, 0.43, fill=RGBColor(0xED, 0xE7, 0xF2), outline=RGBColor(0xED, 0xE7, 0xF2))
    add_text(
        slide,
        "The notebook prints all four probability pairs, each vote, the vote count, and mean/max P(trojan).",
        0.92,
        6.44,
        11.50,
        0.20,
        size=10.2,
        bold=True,
        color=DEEP,
        align=PP_ALIGN.CENTER,
    )
    add_footer(slide, 6)


def build_course_workflow(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_bg(slide, WHITE)
    add_title(
        slide,
        "06 • Course package",
        "AES-128: the course notebook flow",
        "Each step prints its log in the notebook, including four GNN probability results.",
    )

    # Left workflow rail.
    steps = [
        ("01", "Generate", "Portkey + Gemini creates a complete AES Trojan design", NYU),
        ("02", "Compile", "Extract Verilog and run iverilog", AMBER),
        ("03", "Test", "Run five AES-128 test vectors", GREEN),
        ("04", "Detect", "Run four GNN models and combine their votes", TEAL),
        ("05", "Report", "Show logs, probabilities, and file locations in the notebook", DEEP),
    ]
    y = 1.86
    for num, head, body, accent in steps:
        circle = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(0.72), Inches(y), Inches(0.56), Inches(0.56))
        circle.fill.solid()
        circle.fill.fore_color.rgb = accent
        circle.line.fill.background()
        set_shape_text(circle, num, size=10, color=WHITE, bold=True)
        add_text(slide, head, 1.50, y + 0.02, 1.45, 0.25, size=14.5, bold=True, color=INK)
        add_text(slide, body, 2.87, y + 0.01, 4.10, 0.40, size=11.5, color=MID)
        if num != "05":
            add_line(slide, 1.00, y + 0.56, 1.00, y + 0.83, color=LINE, width=2.0)
        y += 0.88

    # Inline report mock-up.
    add_box(slide, 7.33, 1.90, 5.38, 4.55, fill=RGBColor(0x1E, 0x1C, 0x22), outline=NYU, width=1.8)
    add_text(slide, "NOTEBOOK OUTPUT", 7.67, 2.19, 2.50, 0.22, size=9.5, bold=True, color=TEAL)
    add_text(slide, "detecting aes_128_…_A1.v", 7.67, 2.63, 4.40, 0.24, size=12.5, color=WHITE, font="Courier New")
    terminal_lines = [
        ("[syntax] PASS", GREEN),
        ("[AES TB] 5/5 vectors PASS", GREEN),
        ("HT1  P(clean)=…  P(trojan)=…", WHITE),
        ("HT2  P(clean)=…  P(trojan)=…", WHITE),
        ("HT3  P(clean)=…  P(trojan)=…", WHITE),
        ("HT4  P(clean)=…  P(trojan)=…", WHITE),
        ("ensemble vote + mean/max probability", TEAL),
    ]
    ty = 3.12
    for text, color in terminal_lines:
        add_text(slide, text, 7.67, ty, 4.55, 0.22, size=11.4, color=color, font="Courier New")
        ty += 0.41

    add_box(slide, 0.75, 6.45, 11.86, 0.35, fill=RGBColor(0xF0, 0xEA, 0xF4), outline=RGBColor(0xF0, 0xEA, 0xF4))
    add_text(
        slide,
        "AES note: the package uses a faster DFG method because exact processing of the large S-box tables can take too long.",
        0.98,
        6.54,
        11.38,
        0.18,
        size=9.8,
        color=DEEP,
        bold=True,
        align=PP_ALIGN.CENTER,
    )
    add_footer(slide, 7)


def build_student_extension(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_bg(slide, LIGHT)
    add_title(
        slide,
        "07 • Student extension",
        "Build and retrain your own detector",
        "Use the current models as a starting point, then train with data that matches your goal.",
    )

    steps = [
        ("1 • DATA", "Clean RTL +\nlabeled Trojan RTL", NYU, PALE),
        ("2 • DFG", "Use the same\n37 node types", TEAL, RGBColor(0xE6, 0xF5, 0xF3)),
        ("3 • SPLIT", "Train • validation\n• test", AMBER, RGBColor(0xFA, 0xF3, 0xE4)),
        ("4 • RETRAIN", "Continue training or\nbuild a new model", RED, RGBColor(0xFC, 0xF0, 0xF2)),
        ("5 • TEST", "Compare on\nunseen designs", GREEN, RGBColor(0xE5, 0xF4, 0xEF)),
    ]
    xs = [0.55, 3.10, 5.65, 8.20, 10.75]
    for i, (tag, body, accent, fill) in enumerate(steps):
        x = xs[i]
        add_box(slide, x, 1.95, 2.05, 1.42, fill=fill, outline=accent, width=1.7)
        add_text(slide, tag, x + 0.16, 2.17, 1.73, 0.18, size=8.8, bold=True, color=accent)
        add_text(slide, body, x + 0.16, 2.55, 1.73, 0.52, size=13.1, bold=True, color=INK, valign=MSO_ANCHOR.MIDDLE)
        if i < 4:
            add_chevron(slide, x + 2.14, 2.44, w=0.27, h=0.44, color=accent)

    add_box(slide, 0.62, 4.02, 5.82, 1.82, fill=WHITE, outline=NYU, width=1.3)
    add_text(slide, "POSSIBLE GOALS", 0.92, 4.31, 2.20, 0.20, size=9.5, bold=True, color=NYU)
    add_text(
        slide,
        "• Better accuracy on your own designs\n"
        "• Detect a new Trojan type or payload\n"
        "• Reduce false alarms\n"
        "• Handle larger or LLM-generated RTL",
        0.94,
        4.70,
        5.00,
        0.90,
        size=12.3,
        color=INK,
        line_spacing=1.12,
    )

    add_box(slide, 6.87, 4.02, 5.82, 1.82, fill=DEEP, outline=DEEP)
    add_text(slide, "WHAT STUDENTS SUBMIT", 7.17, 4.31, 2.80, 0.20, size=9.5, bold=True, color=TEAL)
    add_text(
        slide,
        "• New model.cfg + model.pth\n"
        "• Dataset description and data split\n"
        "• Accuracy, missed Trojans, and false alarms\n"
        "• Updated MODEL_PATHS entry in the notebook",
        7.19,
        4.70,
        4.98,
        0.90,
        size=12.0,
        color=WHITE,
        line_spacing=1.12,
    )

    add_box(slide, 1.08, 6.24, 11.18, 0.55, fill=RGBColor(0xED, 0xE7, 0xF2), outline=RGBColor(0xED, 0xE7, 0xF2))
    add_text(
        slide,
        "Important: test only on designs that were not used for training, and compare with the original model.",
        1.35,
        6.39,
        10.64,
        0.22,
        size=12.0,
        bold=True,
        color=DEEP,
        align=PP_ALIGN.CENTER,
    )
    add_footer(slide, 8)


def main():
    crop_logo()
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    prs.core_properties.title = "TrojanGYM: From One-Shot GHOST to Detector-in-the-Loop Generation"
    prs.core_properties.subject = "TrojanGYM AES course overview"
    prs.core_properties.author = "NYU Tandon School of Engineering"
    prs.core_properties.keywords = "TrojanGYM, GHOST, hardware Trojan, AES-128, GNN"

    build_title_slide(prs)
    build_ghost_flow(prs)
    build_gap(prs)
    build_trojangym_loop(prs)
    build_comparison(prs)
    build_gnn4tj_detail(prs)
    build_course_workflow(prs)
    build_student_extension(prs)

    prs.save(OUT)
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
