# =========================================================
# AIDEA — FULL REPORT PDF GENERATOR
# =========================================================
#
# Turns everything shown on the AIDEA Advanced Dashboard
# (RTL, AI explanation, truth table, FSM, timing, floorplan,
#  schematic, placement / routing / power / congestion charts,
#  verification, simulation, FPGA/ASIC summaries, ...) into a
#  single printable PDF file.
#
# This module is intentionally defensive: every section is
# wrapped in its own try/except so that one missing/odd piece
# of data (e.g. a chart engine that isn't installed) never
# prevents the rest of the report from being generated.
# =========================================================

import io
import os
import re
import base64
import datetime

from bs4 import BeautifulSoup, NavigableString, Tag

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    Preformatted,
    Image as RLImage,
)

MAX_TABLE_ROWS = 2048   # safety cap so a huge truth table can't blow up the PDF
MAX_LOG_CHARS = 80000    # safety cap for simulation logs

# =========================================================
# PRINT-SAFE COLOR PALETTE
# =========================================================
# Every color used for TEXT in this document must be dark (readable on
# white paper, ink-friendly when printed). Backgrounds are light tints;
# we never rely on white/light text over a dark fill, since that inverts
# poorly in print and wastes toner/ink.
# =========================================================
DARK_TEXT = colors.HexColor("#0f172a")     # near-black navy — primary text
ACCENT_TEXT = colors.HexColor("#1e3a8a")   # dark blue — subtitle / accents
MUTED_TEXT = colors.HexColor("#334155")    # dark slate gray — meta / italic
CODE_TEXT = colors.HexColor("#14532d")     # dark green — code, still print-dark
HEADER_BG = colors.HexColor("#e2e8f0")     # light slate — table/section header fill
ALT_ROW_BG = colors.HexColor("#f1f5f9")    # very light gray — zebra rows
GRID_COLOR = colors.HexColor("#94a3b8")    # mid gray — grid lines (structural, not text)
BORDER_COLOR = colors.HexColor("#0f172a")  # page border color


# =========================================================
# STYLES
# =========================================================

def _build_styles():
    base = getSampleStyleSheet()
    styles = {}

    styles["Title"] = ParagraphStyle(
        "AideaTitle", parent=base["Title"],
        fontSize=26, leading=30,
        textColor=DARK_TEXT,
        alignment=1, spaceAfter=6,
    )
    styles["Subtitle"] = ParagraphStyle(
        "AideaSubtitle", parent=base["Normal"],
        fontSize=14, textColor=ACCENT_TEXT,
        alignment=1, spaceAfter=4,
    )
    styles["Meta"] = ParagraphStyle(
        "AideaMeta", parent=base["Normal"],
        fontSize=10, textColor=MUTED_TEXT,
        alignment=1,
    )
    styles["Heading"] = ParagraphStyle(
        "AideaHeading", parent=base["Heading1"],
        fontSize=15, leading=18,
        textColor=DARK_TEXT, backColor=HEADER_BG,
        borderColor=DARK_TEXT, borderWidth=0.75,
        spaceBefore=2, spaceAfter=8,
        leftIndent=6, borderPadding=(6, 6, 6, 6),
    )
    styles["H2"] = ParagraphStyle(
        "AideaH2", parent=base["Heading2"],
        fontSize=12.5, textColor=DARK_TEXT, spaceBefore=6, spaceAfter=4,
    )
    styles["H3"] = ParagraphStyle(
        "AideaH3", parent=base["Heading3"],
        fontSize=11.5, textColor=DARK_TEXT, spaceBefore=4, spaceAfter=3,
    )
    styles["H4"] = styles["H3"]
    styles["Body"] = ParagraphStyle(
        "AideaBody", parent=base["Normal"],
        fontSize=9.7, leading=13.5, spaceAfter=3,
        textColor=DARK_TEXT,
    )
    styles["Italic"] = ParagraphStyle(
        "AideaItalic", parent=base["Normal"],
        fontSize=9, textColor=MUTED_TEXT,
        fontName="Helvetica-Oblique",
    )
    styles["Code"] = ParagraphStyle(
        "AideaCode", parent=base["Code"],
        fontSize=7.6, leading=10,
        backColor=colors.HexColor("#f8fafc"),
        textColor=CODE_TEXT,
        borderColor=GRID_COLOR, borderWidth=0.5,
        borderPadding=(6, 6, 6, 6),
    )
    styles["TableHeader"] = ParagraphStyle(
        "AideaTH", parent=base["Normal"],
        fontSize=8.8, textColor=DARK_TEXT, fontName="Helvetica-Bold",
    )
    styles["TableCell"] = ParagraphStyle(
        "AideaTD", parent=base["Normal"],
        fontSize=8.3, leading=10.5,
        textColor=DARK_TEXT,
    )
    styles["Caption"] = ParagraphStyle(
        "AideaCaption", parent=base["Normal"],
        fontSize=8.7, leading=11, alignment=1,
        textColor=MUTED_TEXT,
        fontName="Helvetica-Oblique",
        spaceBefore=4, spaceAfter=12,
    )
    return styles


# =========================================================
# SMALL HELPERS
# =========================================================

def _clean_text(text):
    return re.sub(r"\s+", " ", text or "").strip()


def _resolve_static_path(url_path, project_root):
    """Turns '/static/generated/x.png?t=123' into a real filesystem path."""
    if not url_path:
        return None
    p = str(url_path).split("?")[0].lstrip("/")
    return os.path.join(project_root, p)


def png_file_to_flowable(path, max_width, styles):
    try:
        img = RLImage(path)
        ratio = img.imageHeight / float(img.imageWidth)
        img.drawWidth = max_width
        img.drawHeight = max_width * ratio
        return img
    except Exception as e:
        return Paragraph(f"[Image unavailable in PDF export: {e}]", styles["Italic"])


def svg_file_to_flowable(path, max_width, styles):
    try:
        from svglib.svglib import svg2rlg
        drawing = svg2rlg(path)
        if drawing is None or not drawing.width:
            raise ValueError("could not parse SVG")
        scale = min(max_width / drawing.width, 1.0) if drawing.width > max_width else max_width / drawing.width
        drawing.width *= scale
        drawing.height *= scale
        drawing.scale(scale, scale)
        return drawing
    except Exception as e:
        return Paragraph(f"[Schematic unavailable in PDF export: {e}]", styles["Italic"])


def fig_to_image_flowable(fig, max_width, styles):
    """Rasterizes a Plotly figure (via kaleido) into a PDF-embeddable image."""
    if fig is None:
        return None
    try:
        png_bytes = fig.to_image(format="png", width=1100, height=650, scale=2)
        buf = io.BytesIO(png_bytes)
        img = RLImage(buf)
        ratio = img.imageHeight / float(img.imageWidth)
        img.drawWidth = max_width
        img.drawHeight = max_width * ratio
        return img
    except Exception as e:
        return Paragraph(
            f"[Chart unavailable in PDF export — install the 'kaleido' package "
            f"to embed this chart as an image. ({e})]",
            styles["Italic"],
        )


# =========================================================
# TIMING VISUALIZATION IMAGE PIPELINE
# =========================================================
#
# The Timing Dashboard produces two DISTINCT visuals:
#   1. timing_path_graph  -> network graph: INPUT -> Logic Cells -> OUTPUT
#   2. timing_slack_plot  -> slack bar chart / distribution
#
# These must never be conflated or overwritten with each other.
# Each may arrive as: a base64 string (optionally a data: URI), raw
# PNG bytes, a filesystem/static path, or a Plotly figure object
# (kept only for backward compatibility with older callers).
# =========================================================

_PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
_JPEG_MAGIC = b"\xff\xd8"


def _resolve_timing_image_bytes(value, project_root):
    """
    Normalizes a timing-image source into raw image bytes.
    Returns (bytes_or_None, source_kind) where source_kind is a short
    string used for debug logging.
    """
    if value is None:
        return None, "none"

    # Plotly figure object (legacy support)
    if hasattr(value, "to_image"):
        try:
            return value.to_image(format="png", width=1200, height=700, scale=2), "plotly_fig"
        except Exception as e:
            print(f"[PDF][TimingImage] Plotly figure rasterization failed: {e}")
            return None, "plotly_fig_error"

    # Raw bytes already
    if isinstance(value, (bytes, bytearray)):
        return bytes(value), "raw_bytes"

    if isinstance(value, str):
        s = value.strip()
        if not s:
            return None, "empty_string"

        # 1) Try as a filesystem / static path first (cheap check, no exceptions)
        if s.startswith("/") or s.startswith("./") or os.path.isabs(s):
            resolved_path = _resolve_static_path(s, project_root)
            if resolved_path and os.path.exists(resolved_path):
                try:
                    with open(resolved_path, "rb") as f:
                        return f.read(), "file_path"
                except Exception as e:
                    print(f"[PDF][TimingImage] Failed reading file '{resolved_path}': {e}")

        # 2) Try as base64 (optionally prefixed with a data: URI header)
        b64_str = s
        if s.startswith("data:image"):
            try:
                b64_str = s.split(",", 1)[1]
            except IndexError:
                b64_str = ""
        try:
            decoded = base64.b64decode(b64_str, validate=True)
            if decoded[:8] == _PNG_MAGIC or decoded[:2] == _JPEG_MAGIC or decoded[:5] in (b"<?xml", b"<svg "):
                return decoded, "base64"
        except Exception as e:
            print(f"[PDF][TimingImage] base64 decode failed: {e}")

    print(f"[PDF][TimingImage] Could not resolve image source of type {type(value).__name__}")
    return None, "unresolved"


def timing_image_to_flowables(value, project_root, max_width, styles, image_name,
                               caption_text=None, missing_text="No Timing Visualization Available"):
    """
    Turns a timing-image source (base64 / file path / Plotly figure) into a
    centered, aspect-ratio-preserving ReportLab flowable list with an
    optional caption underneath. Never raises — falls back to a
    "missing" message instead.
    """
    raw_size = len(value) if isinstance(value, (str, bytes, bytearray)) else 0
    print(f"[PDF][TimingImage] name='{image_name}' base64/raw_size={raw_size} chars/bytes")

    img_bytes, kind = _resolve_timing_image_bytes(value, project_root)

    if not img_bytes:
        print(f"[PDF][TimingImage] name='{image_name}' source_kind={kind} -> INSERTION FAILED (no usable image data)")
        return [Paragraph(f"<b>{missing_text}</b>", styles["Italic"])]

    try:
        buf = io.BytesIO(img_bytes)
        img = RLImage(buf)
        iw, ih = img.imageWidth, img.imageHeight
        ratio = ih / float(iw)

        draw_w = max_width
        draw_h = max_width * ratio
        img.drawWidth = draw_w
        img.drawHeight = draw_h
        img.hAlign = "CENTER"

        print(
            f"[PDF][TimingImage] name='{image_name}' source_kind={kind} "
            f"decoded_size={iw}x{ih}px draw_size={draw_w:.0f}x{draw_h:.0f}pt -> INSERTED OK"
        )

        out = [img]
        if caption_text:
            out.append(Spacer(1, 4))
            out.append(Paragraph(caption_text, styles["Caption"]))
        return out
    except Exception as e:
        print(f"[PDF][TimingImage] name='{image_name}' source_kind={kind} -> INSERTION FAILED ({e})")
        return [Paragraph(f"<b>{missing_text}</b> ({e})", styles["Italic"])]


def _split_html_at_marker(html_str, markers=("ai timing insight", "recommendation")):
    """
    Best-effort split of a timing HTML panel into (metrics_html, insight_html)
    so the two timing images can be inserted between the metrics table and
    the AI insight / recommendations, matching the dashboard layout. If no
    matching heading is found, everything is returned as metrics_html and
    insight_html is empty (safe fallback — nothing is lost).
    """
    if not html_str or not str(html_str).strip():
        return "", ""

    soup = BeautifulSoup(str(html_str), "html.parser")
    root = soup.body or soup

    before_parts, after_parts = [], []
    split_found = False

    for child in list(root.children):
        if not split_found and getattr(child, "name", None) in ("h1", "h2", "h3", "h4", "h5", "h6"):
            heading_text = child.get_text(" ", strip=True).lower()
            if any(marker in heading_text for marker in markers):
                split_found = True
        (after_parts if split_found else before_parts).append(str(child))

    return "".join(before_parts), "".join(after_parts)


# =========================================================
# GENERIC HTML FRAGMENT -> REPORTLAB FLOWABLES
# =========================================================

def html_fragment_to_flowables(html_str, styles, max_width, max_rows=MAX_TABLE_ROWS):
    flowables = []
    if not html_str or not str(html_str).strip():
        return flowables

    soup = BeautifulSoup(str(html_str), "html.parser")

    def render_inline(tag):
        out = []
        for child in tag.children:
            if isinstance(child, NavigableString):
                out.append(str(child))
            elif isinstance(child, Tag):
                if child.name in ("b", "strong"):
                    out.append(f"<b>{render_inline(child)}</b>")
                elif child.name in ("i", "em"):
                    out.append(f"<i>{render_inline(child)}</i>")
                elif child.name == "br":
                    out.append("<br/>")
                elif child.name == "code":
                    out.append(f"<font face='Courier'>{render_inline(child)}</font>")
                else:
                    out.append(render_inline(child))
        return "".join(out)

    def add_table(table_tag):
        rows = []
        for tr in table_tag.find_all("tr"):
            cells = tr.find_all(["th", "td"])
            if not cells:
                continue
            row = []
            for c in cells:
                text = _clean_text(c.get_text())
                style = styles["TableHeader"] if c.name == "th" else styles["TableCell"]
                row.append(Paragraph(text, style))
            rows.append(row)

        if not rows:
            return

        truncated = False
        if len(rows) > max_rows:
            rows = rows[:max_rows]
            truncated = True

        ncols = max(len(r) for r in rows)
        for r in rows:
            while len(r) < ncols:
                r.append(Paragraph("", styles["TableCell"]))

        col_width = max_width / ncols
        t = Table(rows, colWidths=[col_width] * ncols, repeatRows=1)
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), HEADER_BG),
            ("TEXTCOLOR", (0, 0), (-1, 0), DARK_TEXT),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, ALT_ROW_BG]),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]))
        flowables.append(t)
        if truncated:
            flowables.append(Spacer(1, 4))
            flowables.append(Paragraph(
                f"(table truncated to first {max_rows} rows for the PDF export)",
                styles["Italic"],
            ))
        flowables.append(Spacer(1, 10))

    def walk(node):
        for child in node.children:
            if isinstance(child, NavigableString):
                text = _clean_text(str(child))
                if text:
                    flowables.append(Paragraph(text, styles["Body"]))
                continue
            if not isinstance(child, Tag):
                continue

            name = child.name

            if name == "table":
                add_table(child)
            elif name in ("h1", "h2", "h3", "h4", "h5", "h6"):
                text = _clean_text(child.get_text())
                if text:
                    style_key = "H2" if name in ("h1", "h2") else "H3"
                    flowables.append(Paragraph(text, styles[style_key]))
            elif name == "pre":
                text = child.get_text()
                if text.strip():
                    flowables.append(Preformatted(text[:MAX_LOG_CHARS], styles["Code"]))
                    flowables.append(Spacer(1, 6))
            elif name in ("ul", "ol"):
                for li in child.find_all("li", recursive=False):
                    text = "•  " + _clean_text(li.get_text())
                    if text.strip("• "):
                        flowables.append(Paragraph(text, styles["Body"]))
            elif name in ("p", "div", "span", "section", "article"):
                if child.find("table") or child.find(["h1", "h2", "h3", "h4", "pre", "ul", "ol"]):
                    walk(child)
                else:
                    text = render_inline(child).strip()
                    if text:
                        flowables.append(Paragraph(text, styles["Body"]))
            else:
                walk(child)

    walk(soup.body or soup)
    return flowables


# =========================================================
# PAGE BORDER + COVER PAGE (drawn directly on the canvas so the
# layout is pixel-precise and independent of flowable content)
# =========================================================

def _draw_page_border(canvas, doc):
    """Draws a border frame on every page of the report."""
    canvas.saveState()
    canvas.setStrokeColor(BORDER_COLOR)
    canvas.setLineWidth(1)
    margin = 10 * mm
    page_w, page_h = A4
    canvas.rect(margin, margin, page_w - 2 * margin, page_h - 2 * margin)
    canvas.restoreState()


def _fit_image_in_box(canvas, image_path, box_x, box_y, box_w, box_h, padding=6 * mm):
    """Draws an image centered inside a box, preserving aspect ratio, never stretching."""
    try:
        reader = ImageReader(image_path)
        iw, ih = reader.getSize()
        avail_w = box_w - 2 * padding
        avail_h = box_h - 2 * padding
        scale = min(avail_w / float(iw), avail_h / float(ih))
        draw_w = iw * scale
        draw_h = ih * scale
        draw_x = box_x + (box_w - draw_w) / 2.0
        draw_y = box_y + (box_h - draw_h) / 2.0
        canvas.drawImage(
            reader, draw_x, draw_y, width=draw_w, height=draw_h,
            preserveAspectRatio=True, mask="auto",
        )
        return True
    except Exception as e:
        print(f"[PDF][CoverPage] Failed to draw logo image '{image_path}': {e}")
        return False


def _draw_cover_page(canvas, doc, context):
    """
    Page 1 layout:
      - top 50% of the cover box: Logo
      - bottom 50% of the cover box: Project / Top Module title, with the
        generation date printed at the left corner
      - a border frame around the full page
    """
    _draw_page_border(canvas, doc)

    canvas.saveState()
    page_w, page_h = A4

    inner_margin = 18 * mm  # cover box inset, inside the outer page border
    box_x = inner_margin
    box_y = inner_margin
    box_w = page_w - 2 * inner_margin
    box_h = page_h - 2 * inner_margin
    mid_y = box_y + box_h / 2.0

    # Outer cover box + divider between the logo half and the title half
    canvas.setStrokeColor(BORDER_COLOR)
    canvas.setLineWidth(1.1)
    canvas.rect(box_x, box_y, box_w, box_h)
    canvas.line(box_x, mid_y, box_x + box_w, mid_y)

    # ---- Top half (50%): Logo ----
    logo_path = context.get("logo_path") or os.path.join(context.get("static_path", ""), "AIEDA.png")
    top_box_h = box_h / 2.0
    drawn = bool(logo_path) and os.path.exists(logo_path) and _fit_image_in_box(
        canvas, logo_path, box_x, mid_y, box_w, top_box_h
    )
    if not drawn:
        canvas.setFont("Helvetica-Bold", 22)
        canvas.setFillColor(DARK_TEXT)
        canvas.drawCentredString(box_x + box_w / 2.0, mid_y + top_box_h / 2.0 - 8, "LOGO")

    # ---- Bottom half (50%): Title / Project Name ----
    bottom_box_h = box_h / 2.0
    title_text = str(context.get("top_module") or context.get("project_name") or "Untitled Project")

    canvas.setFillColor(DARK_TEXT)
    canvas.setFont("Helvetica-Bold", 24)
    canvas.drawCentredString(box_x + box_w / 2.0, box_y + bottom_box_h / 2.0 + 10, title_text)

    canvas.setFont("Helvetica", 12)
    canvas.setFillColor(ACCENT_TEXT)
    canvas.drawCentredString(
        box_x + box_w / 2.0, box_y + bottom_box_h / 2.0 - 10,
        "AIDEA — Full Chip Analysis Report",
    )

    # ---- Date, printed at the left corner (of the title half) ----
    date_str = context.get("report_date") or datetime.datetime.now().strftime("%d %B %Y")
    canvas.setFont("Helvetica", 10)
    canvas.setFillColor(MUTED_TEXT)
    canvas.drawString(box_x + 6 * mm, box_y + 8 * mm, f"Date: {date_str}")

    canvas.restoreState()


# =========================================================
# MAIN ASSEMBLER
# =========================================================

def generate_full_report_pdf(context, output_path):
    """
    context: dict with the same data used to render the AIDEA Advanced
             Dashboard (see app.py for the exact keys passed in).
    output_path: full filesystem path where the PDF should be written.
    """
    styles = _build_styles()
    project_root = context.get("project_root", "")

    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        topMargin=18 * mm,
        bottomMargin=16 * mm,
        leftMargin=16 * mm,
        rightMargin=16 * mm,
        title="AIDEA Full Chip Analysis Report",
    )
    usable_width = A4[0] - 32 * mm

    story = []

    # ---------------- COVER PAGE ----------------
    # The entire cover page (logo top half / title bottom half / date /
    # border) is drawn directly on the canvas via onFirstPage below, so
    # this page contributes no flowable content — just move on to the
    # rest of the report.
    story.append(PageBreak())

    # ---------------- SECTION HELPER ----------------
    def add_section(title, builder_fn):
        try:
            content = builder_fn() or []
            if not content:
                return
            story.append(Paragraph(title, styles["Heading"]))
            story.append(Spacer(1, 6))
            story.extend(content)
            story.append(Spacer(1, 14))
        except Exception as e:
            story.append(Paragraph(title, styles["Heading"]))
            story.append(Paragraph(f"[Section failed to generate: {e}]", styles["Italic"]))
            story.append(Spacer(1, 14))

    # 1. OVERVIEW
    def _overview():
        rows = [
            ["Top Module", str(context.get("top_module", ""))],
            ["RTL Lines", str(context.get("rtl_lines", ""))],
            ["Ports", str(len(context.get("ports") or []))],
            ["Inputs", str(len(context.get("inputs") or []))],
            ["Outputs", str(len(context.get("outputs") or []))],
            ["Logic Type", str(context.get("logic_type", ""))],
        ]
        t = Table(rows, colWidths=[140, usable_width - 140])
        t.setStyle(TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ("BACKGROUND", (0, 0), (0, -1), ALT_ROW_BG),
            ("TEXTCOLOR", (0, 0), (-1, -1), DARK_TEXT),
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        return [t]
    add_section(" Design Overview", _overview)

    # 2. RTL SOURCE
    add_section(" RTL Source Code",
                 lambda: [Preformatted((context.get("code") or "")[:20000], styles["Code"])])

    # 2b. TESTBENCH
    def _testbench():
        tb_code = (
            context.get("testbench_code")
            or context.get("testbench")
            or context.get("tb_code")
            or context.get("tb")
        )
        print(f"[PDF][Testbench] present={bool(tb_code and str(tb_code).strip())}")
        if tb_code and str(tb_code).strip():
            return [Preformatted(str(tb_code)[:20000], styles["Code"])]
        return [Paragraph("<b>No testbench available.</b>", styles["Body"])]
    add_section(" Testbench Code", _testbench)


    # 3. AI EXPLANATION
    add_section(" AI Analysis & Explanation",
                 lambda: html_fragment_to_flowables(context.get("explanation_html", ""), styles, usable_width))

    # 4. SYNTHESIS / ABC SUMMARY
    add_section(" Synthesis Summary (ABC)",
                 lambda: html_fragment_to_flowables(context.get("abc_summary_html", ""), styles, usable_width))

    # 5. TRUTH TABLE
    add_section(" Truth Table",
                 lambda: html_fragment_to_flowables(context.get("truth_html", ""), styles, usable_width))

     # 6. FSM
    def _fsm():
        out = []

        # ---- FSM Diagram (title + image) ----
        out.append(Paragraph("FSM Diagram", styles["H2"]))

        # Prefer PNG if available, otherwise fall back to SVG.
        # Never regenerate — only render whatever image already exists.
        png_path = _resolve_static_path(context.get("fsm_png"), project_root)
        svg_path = _resolve_static_path(context.get("fsm_svg"), project_root)

        if png_path and os.path.exists(png_path):
            out.append(png_file_to_flowable(png_path, usable_width, styles))
        elif svg_path and os.path.exists(svg_path):
            out.append(svg_file_to_flowable(svg_path, usable_width, styles))
        else:
            out.append(Paragraph("<b>No FSM diagram available.</b>", styles["Body"]))

        out.append(Spacer(1, 12))

        # ---- FSM Summary ----
        fsm_summary = context.get("fsm_summary") or {}
        if fsm_summary:
            out.append(Paragraph("FSM Summary", styles["H2"]))
            rows = [["Metric", "Value"]]
            for k, v in fsm_summary.items():
                rows.append([str(k).replace("_", " ").title(), str(v)])
            t = Table(rows, colWidths=[200, usable_width - 200])
            t.setStyle(TableStyle([
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ("BACKGROUND", (0, 0), (-1, 0), HEADER_BG),
                ("TEXTCOLOR", (0, 0), (-1, 0), DARK_TEXT),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]))
            out.append(t)
            out.append(Spacer(1, 12))

        # ---- State List ----
        fsm_states = context.get("fsm_states") or []
        if fsm_states:
            out.append(Paragraph("States", styles["H2"]))
            for state in fsm_states:
                out.append(Paragraph(f"•  {state}", styles["Body"]))
            out.append(Spacer(1, 12))

        # ---- Transition Table ----
        fsm_transitions = context.get("fsm_transitions") or []
        if fsm_transitions:
            out.append(Paragraph("Transition Table", styles["H2"]))
            rows = [["Current State", "Next State", "Condition"]]
            for transition in fsm_transitions:
                rows.append([
                    Paragraph(str(transition.get("from", "")), styles["TableCell"]),
                    Paragraph(str(transition.get("to", "")), styles["TableCell"]),
                    Paragraph(str(transition.get("condition", "")), styles["TableCell"]),
                ])
            t = Table(rows, colWidths=[usable_width * 0.3, usable_width * 0.3, usable_width * 0.4], repeatRows=1)
            t.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), HEADER_BG),
                ("TEXTCOLOR", (0, 0), (-1, 0), DARK_TEXT),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, ALT_ROW_BG]),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]))
            out.append(t)

        return out

    add_section(" Finite State Machine Analysis", _fsm)

    # 7. TIMING
    def _timing():
        out = []

        # ---- Validation / debug logging for the two required image keys ----
        for req_key in ("timing_path_graph", "timing_slack_plot"):
            present = req_key in context
            val = context.get(req_key)
            size = len(val) if isinstance(val, (str, bytes, bytearray)) else 0
            print(
                f"[PDF][TimingSection] key='{req_key}' present_in_context={present} "
                f"value_type={type(val).__name__} size={size}"
            )

        # ---- Timing Metrics (summary cards + timing table) ----
        panel_html = context.get("timing_panel_html", "")
        metrics_html, insight_html = _split_html_at_marker(panel_html)
        out.extend(html_fragment_to_flowables(metrics_html or panel_html, styles, usable_width))

        # ---- Timing Path Visualization (INPUT -> Logic Cells -> OUTPUT) ----
        # This must be the SAME network graph shown on the dashboard —
        # it is never generated here, only read from context.
        out.append(Spacer(1, 10))
        out.append(Paragraph("Timing Path Visualization", styles["H2"]))
        path_source = (
            context.get("timing_path_graph")
            or context.get("timing_path_fig")
            or context.get("timing_network_fig")
        )
        out.extend(timing_image_to_flowables(
            path_source, project_root, usable_width, styles,
            image_name="timing_path_graph",
            caption_text="Figure 1: Critical Timing Path Visualization",
        ))

        # ---- Slack Analysis (kept as an independent figure, never merged
        #      with / overwritten by the path visualization above) ----
        out.append(Spacer(1, 14))
        out.append(Paragraph("Slack Analysis", styles["H2"]))
        slack_source = (
            context.get("timing_slack_plot")
            or context.get("timing_slack_fig")
            # legacy fallback: older callers stored the slack chart under
            # this generic key, which is what caused it to appear in place
            # of the path visualization in the first place.
            or context.get("timing_fig")
            or context.get("timing_plot")
        )
        out.extend(timing_image_to_flowables(
            slack_source, project_root, usable_width, styles,
            image_name="timing_slack_plot",
            caption_text="Figure 2: Slack Distribution Across Critical Paths",
        ))

        # ---- AI Timing Insight / Recommendations ----
        if insight_html:
            out.append(Spacer(1, 14))
            out.extend(html_fragment_to_flowables(insight_html, styles, usable_width))

        return out

    add_section(" Timing Analysis", _timing)

    # 8. FLOORPLAN
    def _floorplan():
        out = []
        fm = context.get("floorplan_metrics") or {}
        if fm:
            rows = [["Metric", "Value"]]
            for k, v in fm.items():
                rows.append([str(k).replace("_", " ").title(), str(v)])
            t = Table(rows, colWidths=[200, usable_width - 200])
            t.setStyle(TableStyle([
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ("BACKGROUND", (0, 0), (-1, 0), HEADER_BG),
                ("TEXTCOLOR", (0, 0), (-1, 0), DARK_TEXT),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ]))
            out.append(t)
            out.append(Spacer(1, 10))
        png_path = _resolve_static_path(context.get("floorplan_png"), project_root)
        if png_path and os.path.exists(png_path):
            out.append(png_file_to_flowable(png_path, usable_width, styles))
        return out
    add_section("Floorplanning", _floorplan)

    # 9. SCHEMATIC
    def _schematic():
        svg_path = _resolve_static_path(context.get("schematic_svg"), project_root)
        if svg_path and os.path.exists(svg_path):
            return [svg_file_to_flowable(svg_path, usable_width, styles)]
        return []
    add_section(" Schematic", _schematic)

    # 10-13. CHARTS (placement / routing / power / congestion)
    def _chart(fig):
        img = fig_to_image_flowable(fig, usable_width, styles)
        return [img] if img is not None else []

    add_section(" Placement", lambda: _chart(context.get("placement_fig")))
    add_section(" Routing", lambda: _chart(context.get("routing_fig")))
    add_section(" Power Analysis", lambda: _chart(context.get("power_fig")))
    add_section(" Congestion Analysis", lambda: _chart(context.get("congestion_fig")))

    # 14. VERIFICATION
    add_section(" Verification Summary",
                 lambda: html_fragment_to_flowables(context.get("verification_html", ""), styles, usable_width))

    # 15. SIMULATION LOG
    def _sim():
        sim_text = str(context.get("sim_result", "") or "")
        if not sim_text.strip():
            return []
        return [Preformatted(sim_text[:MAX_LOG_CHARS], styles["Code"])]
    add_section(" Simulation Log", _sim)

    # 16-17. FPGA / ASIC
    add_section(" FPGA Summary",
                 lambda: html_fragment_to_flowables(context.get("fpga_html", ""), styles, usable_width))
    add_section(" ASIC Summary",
                 lambda: html_fragment_to_flowables(context.get("asic_html", ""), styles, usable_width))

    def _on_first_page(canvas, doc_):
        _draw_cover_page(canvas, doc_, context)

    def _on_later_pages(canvas, doc_):
        _draw_page_border(canvas, doc_)

    doc.build(story, onFirstPage=_on_first_page, onLaterPages=_on_later_pages)
    return output_path
