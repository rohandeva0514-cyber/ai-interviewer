"""
report_generator.py
-------------------
Generates a polished PDF interview report using ReportLab.
Call: generate_report(session: dict) -> bytes

Fix: No KeepTogether or single-cell Table wrappers around long content.
     Long Q&A cards flow naturally across page breaks.
"""

from io import BytesIO
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.platypus import (
    BaseDocTemplate, PageTemplate, Frame,
    Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether
)
from reportlab.graphics.shapes import Drawing, String, Circle
from reportlab.graphics import renderPDF


# ─── COLOUR PALETTE ──────────────────────────────────────────────────────────
DARK_BG   = colors.HexColor("#0A0F2C")
ACCENT    = colors.HexColor("#100396")
ACCENT2   = colors.HexColor("#8fc9ff")
WHITE     = colors.white
GREY_TEXT = colors.HexColor("#6b7fa3")
GREEN     = colors.HexColor("#22c55e")
AMBER     = colors.HexColor("#f59e0b")
RED       = colors.HexColor("#ef4444")
SOFT_BG   = colors.HexColor("#f0f4ff")
BORDER    = colors.HexColor("#c7d8f8")
CARD_BG   = colors.HexColor("#fafbff")

PAGE_W    = 170 * mm   # usable width inside margins


# ─── STYLES ──────────────────────────────────────────────────────────────────
def make_styles():
    return {
        "h_name": ParagraphStyle("h_name",
            fontName="Helvetica-Bold", fontSize=22, leading=28,
            textColor=WHITE, spaceAfter=2),
        "h_role": ParagraphStyle("h_role",
            fontName="Helvetica", fontSize=11, leading=16,
            textColor=ACCENT2, spaceAfter=0),
        "section_title": ParagraphStyle("section_title",
            fontName="Helvetica-Bold", fontSize=12, leading=16,
            textColor=ACCENT, spaceBefore=10, spaceAfter=4),
        "q_text": ParagraphStyle("q_text",
            fontName="Helvetica-Bold", fontSize=10, leading=14,
            textColor=colors.HexColor("#1a1a2e"), spaceAfter=3,
            leftIndent=4),
        "answer_text": ParagraphStyle("answer_text",
            fontName="Helvetica", fontSize=9.5, leading=14,
            textColor=colors.HexColor("#2d3748"), spaceAfter=3,
            leftIndent=4),
        "feedback_text": ParagraphStyle("feedback_text",
            fontName="Helvetica-Oblique", fontSize=9, leading=13,
            textColor=colors.HexColor("#4a5568"), spaceAfter=2,
            leftIndent=4),
        "code_text": ParagraphStyle("code_text",
            fontName="Courier", fontSize=7.5, leading=10.5,
            textColor=colors.HexColor("#1a202c"),
            backColor=colors.HexColor("#f0f4f8"),
            spaceAfter=3, leftIndent=8, rightIndent=4),
        "meta": ParagraphStyle("meta",
            fontName="Helvetica", fontSize=8, leading=11,
            textColor=GREY_TEXT, leftIndent=4),
        "footer": ParagraphStyle("footer",
            fontName="Helvetica", fontSize=8, leading=11,
            textColor=colors.HexColor("#9aa5b1"), alignment=TA_CENTER),
        "body": ParagraphStyle("body",
            fontName="Helvetica", fontSize=10, leading=14,
            textColor=colors.HexColor("#1a1a2e")),
    }


# ─── HELPERS ─────────────────────────────────────────────────────────────────
def xml_safe(text: str) -> str:
    return (str(text)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;"))


def code_safe(text: str) -> str:
    return (xml_safe(text)
            .replace("\n", "<br/>")
            .replace("\t", "&nbsp;&nbsp;&nbsp;&nbsp;")
            .replace("  ", "&nbsp;&nbsp;"))


def score_color(score, out_of=5):
    pct = float(score) / out_of
    if pct >= 0.8: return GREEN
    if pct >= 0.5: return AMBER
    return RED


def score_label(score, out_of=5):
    pct = float(score) / out_of
    if pct >= 0.8: return "Excellent"
    if pct >= 0.6: return "Good"
    if pct >= 0.4: return "Fair"
    return "Needs Work"


def score_badge(score, out_of=5, size=36):
    d = Drawing(size, size)
    col = score_color(score, out_of)
    # shadow
    d.add(Circle(size/2+1, size/2-1, size/2-3,
                 fillColor=colors.HexColor("#00000018"), strokeColor=None))
    # circle
    d.add(Circle(size/2, size/2, size/2-2,
                 fillColor=col, strokeColor=WHITE, strokeWidth=1.5))
    # score
    d.add(String(size/2, size/2-3.5, str(score),
                 textAnchor="middle", fontName="Helvetica-Bold",
                 fontSize=12, fillColor=WHITE))
    d.add(String(size/2, 3.5, f"/{out_of}",
                 textAnchor="middle", fontName="Helvetica",
                 fontSize=5.5, fillColor=colors.HexColor("#ffffff99")))
    return d


# ─── HEADER BANNER ───────────────────────────────────────────────────────────
def header_banner(name, role, date_str, duration, total_q, styles):
    name_p = Paragraph(name, styles["h_name"])
    role_p = Paragraph(f"Applied for: <b>{xml_safe(role)}</b>", styles["h_role"])
    meta_p = Paragraph(
        f"Date: {date_str}  |  Duration: {duration}  |  Questions: {total_q}",
        ParagraphStyle("hm", fontName="Helvetica", fontSize=8.5, leading=12,
                       textColor=colors.HexColor("#a0aec0")))

    badge = Drawing(56, 56)
    badge.add(Circle(28, 28, 26,
                     fillColor=colors.HexColor("#1a3a8f"),
                     strokeColor=ACCENT2, strokeWidth=1.5))
    badge.add(String(28, 20, "AI", textAnchor="middle",
                     fontName="Helvetica-Bold", fontSize=20, fillColor=WHITE))
    badge.add(String(28, 10, "INTERVIEW", textAnchor="middle",
                     fontName="Helvetica", fontSize=5, fillColor=ACCENT2))

    left = [name_p, Spacer(1, 3), role_p, Spacer(1, 5), meta_p]
    t = Table([[left, badge]], colWidths=[PAGE_W - 62*mm, 56*mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0,0),(-1,-1), DARK_BG),
        ("ROWPADDING", (0,0),(-1,-1), 14),
        ("VALIGN",     (0,0),(-1,-1), "MIDDLE"),
        ("LINEBELOW",  (0,0),(-1,0),  2, ACCENT),
    ]))
    return t


# ─── SUMMARY STATS ───────────────────────────────────────────────────────────
def summary_row(history, styles):
    scores = [h.get("evaluation", {}).get("score")
              for h in history
              if isinstance(h.get("evaluation"), dict)
              and h.get("evaluation", {}).get("score") is not None]
    avg = round(sum(scores)/len(scores), 1) if scores else 0

    rounds = {"behavioral":[], "fresher":[], "role":[], "technical":[]}
    for h in history:
        qt = h.get("question_type","")
        sc = h.get("evaluation",{}).get("score") if isinstance(h.get("evaluation"), dict) else None
        if qt in rounds and sc is not None:
            rounds[qt].append(sc)

    best_round, best_score = "—", -1
    labels = {"behavioral":"Behavioral","fresher":"Behavioral","role":"Domain","technical":"Technical"}
    for rt, sc_list in rounds.items():
        if sc_list:
            a = sum(sc_list)/len(sc_list)
            if a > best_score:
                best_score = a
                best_round = labels.get(rt, rt.title())

    col_w = PAGE_W / 3
    sl = ParagraphStyle("sl", fontName="Helvetica", fontSize=7.5,
                         textColor=GREY_TEXT, leading=10)

    def cell(value_html, lbl):
        return [Paragraph(value_html, styles["body"]), Spacer(1,2), Paragraph(lbl, sl)]

    cells = [
        cell(f'<font color="#100396" size="20"><b>{avg}/5</b></font>', "Average Score"),
        cell(f'<font color="#22c55e" size="13"><b>{best_round}</b></font>', "Strongest Round"),
        cell(f'<font color="#f59e0b" size="16"><b>{len(scores)}/15</b></font>', "Questions Scored"),
    ]

    t = Table([cells], colWidths=[col_w, col_w, col_w])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0,0),(-1,-1), SOFT_BG),
        ("ROWPADDING", (0,0),(-1,-1), 10),
        ("VALIGN",     (0,0),(-1,-1), "TOP"),
        ("LINEAFTER",  (0,0),(1,-1),  0.5, BORDER),
        ("BOX",        (0,0),(-1,-1), 0.5, BORDER),
    ]))
    return t


# ─── Q&A BLOCK ───────────────────────────────────────────────────────────────
def qa_block(index, item, styles):
    """
    Returns a LIST of flowables for one Q&A.
    Critically: NO KeepTogether around the whole thing, and NO single-cell
    Table wrapping all content — both cause LayoutError on long code answers.
    
    Visual card effect is achieved via:
      - A KeepTogether on just the short header row (always fits on one page)
      - A left-border stripe table for each content paragraph
      - A closing border line
    """
    qt         = item.get("question_type", "general")
    question   = item.get("question", "")
    answer     = item.get("answer", "")
    evaluation = item.get("evaluation") or {}
    score      = evaluation.get("score") if isinstance(evaluation, dict) else None
    feedback   = evaluation.get("feedback", "") if isinstance(evaluation, dict) else ""

    tag_map = {
        "behavioral": ("#dbeafe", "#1e40af", "Behavioral"),
        "fresher":    ("#dbeafe", "#1e40af", "Behavioral"),
        "role":       ("#ede9fe", "#5b21b6", "Domain"),
        "technical":  ("#d1fae5", "#065f46", "Technical"),
    }
    tag_bg, tag_fg, tag_label = tag_map.get(qt, ("#f3f4f6", "#374151", qt.title()))

    out_of = 10 if qt == "technical" else 5

    # ── Header: always KeepTogether (it's tiny: ~40pt) ──
    q_num_p = Paragraph(f"<b>Q{index}</b>",
                        ParagraphStyle("qn", fontName="Helvetica-Bold",
                                       fontSize=11, textColor=ACCENT))
    tag_p   = Paragraph(
        f"<b>{tag_label}</b>",
        ParagraphStyle("tag", fontName="Helvetica-Bold", fontSize=7.5,
                       textColor=colors.HexColor(tag_fg),
                       backColor=colors.HexColor(tag_bg),
                       borderPadding=(2,6,2,6)))

    hdr_left = Table([[q_num_p, tag_p]], colWidths=[22*mm, 28*mm])
    hdr_left.setStyle(TableStyle([
        ("VALIGN",     (0,0),(-1,-1), "MIDDLE"),
        ("ROWPADDING", (0,0),(-1,-1), 0),
    ]))

    if score is not None:
        badge   = score_badge(score, out_of)
        hdr_row = Table([[hdr_left, badge]], colWidths=[PAGE_W - 40*mm, 36*mm])
    else:
        hdr_row = Table([[hdr_left, ""]], colWidths=[PAGE_W - 40*mm, 36*mm])

    hdr_row.setStyle(TableStyle([
        ("BACKGROUND", (0,0),(-1,-1), CARD_BG),
        ("ROWPADDING", (0,0),(-1,-1), 8),
        ("VALIGN",     (0,0),(-1,-1), "MIDDLE"),
        ("LINEABOVE",  (0,0),(-1,0),  0.75, BORDER),
        ("LINEBEFORE", (0,0),(0,-1),  3,    ACCENT),
        ("LINEAFTER",  (0,0),(-1,-1), 0.75, BORDER),
    ]))

    flowables = [KeepTogether([hdr_row])]   # header always fits

    # ── Helper: wrap a paragraph in a left-bordered cell ──
    def card_row(content_flowable, bg=WHITE):
        t = Table([[content_flowable]], colWidths=[PAGE_W])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0,0),(-1,-1), bg),
            ("ROWPADDING", (0,0),(-1,-1), (4, 8, 4, 4)),
            ("LINEBEFORE", (0,0),(0,-1),  3,    ACCENT),
            ("LINEAFTER",  (0,0),(-1,-1), 0.75, BORDER),
            ("VALIGN",     (0,0),(-1,-1), "TOP"),
        ]))
        return t

    # ── Question text ──
    flowables.append(card_row(Paragraph(xml_safe(question), styles["q_text"])))

    # ── Answer ──
    if answer:
        if qt == "technical":
            flowables.append(card_row(
                Paragraph('<font color="#6b7fa3" size="8">YOUR CODE:</font>',
                          styles["meta"])))
            # Split code into chunks of 60 lines so no single flowable is > page height
            lines = answer.split("\n")
            chunk_size = 55
            for i in range(0, len(lines), chunk_size):
                chunk = "\n".join(lines[i:i+chunk_size])
                flowables.append(card_row(
                    Paragraph(code_safe(chunk), styles["code_text"]),
                    bg=colors.HexColor("#f7f9fc")))
        else:
            flowables.append(card_row(
                Paragraph('<font color="#6b7fa3" size="8">YOUR ANSWER:</font>',
                          styles["meta"])))
            flowables.append(card_row(
                Paragraph(xml_safe(answer), styles["answer_text"])))

    # ── Feedback ──
    if feedback:
        fb_col = score_color(score, out_of) if score is not None else GREY_TEXT
        fb_hex = ("#22c55e" if fb_col==GREEN else
                  "#f59e0b" if fb_col==AMBER else "#ef4444")
        flowables.append(card_row(
            Paragraph(
                f'<font color="{fb_hex}">&#9679;</font> <i>{xml_safe(feedback)}</i>',
                styles["feedback_text"])))

    # ── Technical extras ──
    if qt == "technical" and isinstance(evaluation, dict):
        for field, lbl in [("bugs","BUGS & MISTAKES"),
                            ("optimizations","OPTIMIZATIONS"),
                            ("best_practices","BEST PRACTICES")]:
            val = evaluation.get(field)
            if val:
                flowables.append(card_row(
                    Paragraph(
                        f'<font color="#6b7fa3" size="8">{lbl}:</font> {xml_safe(val)}',
                        styles["feedback_text"])))

        improved = evaluation.get("improved_code")
        if improved:
            flowables.append(card_row(
                Paragraph('<font color="#6b7fa3" size="8">SUGGESTED IMPROVEMENT:</font>',
                          styles["meta"])))
            lines = improved.split("\n")
            chunk_size = 55
            for i in range(0, len(lines), chunk_size):
                chunk = "\n".join(lines[i:i+chunk_size])
                flowables.append(card_row(
                    Paragraph(code_safe(chunk), styles["code_text"]),
                    bg=colors.HexColor("#f0f7f0")))

    # Closing border line
    flowables.append(Table([[""]], colWidths=[PAGE_W], rowHeights=[1]))
    flowables[-1].setStyle(TableStyle([
        ("LINEBELOW",  (0,0),(-1,-1), 0.75, BORDER),
        ("LINEBEFORE", (0,0),(0,-1),  3,    ACCENT),
        ("LINEAFTER",  (0,0),(-1,-1), 0.75, BORDER),
        ("ROWPADDING", (0,0),(-1,-1), 0),
    ]))

    flowables.append(Spacer(1, 10))
    return flowables


# ─── PAGE TEMPLATE ───────────────────────────────────────────────────────────
def build_doc(buf):
    doc = BaseDocTemplate(
        buf, pagesize=A4,
        leftMargin=20*mm, rightMargin=20*mm,
        topMargin=18*mm, bottomMargin=22*mm,
        title="AI Interview Report",
    )

    def page_bg(canvas, doc):
        canvas.saveState()
        W, H = A4
        canvas.setFillColor(DARK_BG)
        canvas.rect(0, H-8*mm, W, 8*mm, fill=1, stroke=0)
        canvas.setFillColor(ACCENT)
        canvas.rect(0, H-10*mm, W, 2*mm, fill=1, stroke=0)
        canvas.setStrokeColor(BORDER)
        canvas.setLineWidth(0.5)
        canvas.line(20*mm, 16*mm, W-20*mm, 16*mm)
        canvas.setFont("Helvetica", 7.5)
        canvas.setFillColor(GREY_TEXT)
        canvas.drawCentredString(
            W/2, 10*mm,
            f"AI Interview Report  \u2022  Confidential  \u2022  Page {doc.page}")
        canvas.restoreState()

    frame = Frame(
        doc.leftMargin, doc.bottomMargin,
        doc.width, doc.height,
        leftPadding=0, rightPadding=0,
        topPadding=0, bottomPadding=24,
        id="main"
    )
    doc.addPageTemplates([PageTemplate(id="main", frames=[frame], onPage=page_bg)])
    return doc


# ─── MAIN ENTRY POINT ────────────────────────────────────────────────────────
def generate_report(session: dict) -> bytes:
    buf      = BytesIO()
    styles   = make_styles()
    history  = session.get("history", [])
    name     = session.get("name", "Candidate")
    role     = session.get("role", "—")
    q_count  = session.get("q_count", len(history))
    date_str = datetime.now().strftime("%d %B %Y")
    duration = session.get("duration", "—")

    story = []

    # 1. Header
    story.append(header_banner(name, role, date_str, duration, q_count, styles))
    story.append(Spacer(1, 10))

    # 2. Summary stats
    story.append(summary_row(history, styles))
    story.append(Spacer(1, 14))

    # 3. Behavioral
    beh = [h for h in history if h.get("question_type") in ("behavioral","fresher")]
    if beh:
        story.append(HRFlowable(width="100%", thickness=1, color=BORDER, spaceAfter=4))
        story.append(Paragraph("Behavioral Round", styles["section_title"]))
        for i, item in enumerate(beh, 1):
            story.extend(qa_block(i, item, styles))

    # 4. Domain
    domain = [h for h in history if h.get("question_type") == "role"]
    if domain:
        story.append(HRFlowable(width="100%", thickness=1, color=BORDER, spaceAfter=4))
        story.append(Paragraph("Domain / Role Round", styles["section_title"]))
        off = len(beh)
        for i, item in enumerate(domain, off+1):
            story.extend(qa_block(i, item, styles))

    # 5. Technical
    tech = [h for h in history if h.get("question_type") == "technical"]
    if tech:
        story.append(HRFlowable(width="100%", thickness=1, color=BORDER, spaceAfter=4))
        story.append(Paragraph("Technical / Coding Round", styles["section_title"]))
        off = len(beh) + len(domain)
        for i, item in enumerate(tech, off+1):
            story.extend(qa_block(i, item, styles))

    # 6. Score summary table
    scores_by_round = {}
    for h in history:
        qt = h.get("question_type","")
        ev = h.get("evaluation") or {}
        sc = ev.get("score") if isinstance(ev, dict) else None
        if sc is not None:
            scores_by_round.setdefault(qt, []).append(sc)

    score_rows = [[
        Paragraph("<b>Round</b>",     styles["meta"]),
        Paragraph("<b>Avg Score</b>", styles["meta"]),
        Paragraph("<b>Rating</b>",    styles["meta"]),
    ]]
    for lbl, key, out in [("Behavioral", ["behavioral","fresher"], 5),
                           ("Domain",    ["role"],                  5),
                           ("Technical", ["technical"],            10)]:
        sc_list = []
        for k in key:
            sc_list.extend(scores_by_round.get(k, []))
        if sc_list:
            avg  = round(sum(sc_list)/len(sc_list), 1)
            col  = score_color(avg, out)
            chex = ("#22c55e" if col==GREEN else
                    "#f59e0b" if col==AMBER else "#ef4444")
            score_rows.append([
                Paragraph(lbl, styles["body"]),
                Paragraph(f'<font color="{chex}"><b>{avg}/{out}</b></font>', styles["body"]),
                Paragraph(score_label(avg, out), styles["body"]),
            ])

    if len(score_rows) > 1:
        story.append(HRFlowable(width="100%", thickness=1, color=BORDER, spaceAfter=4))
        story.append(Paragraph("Score Summary", styles["section_title"]))
        st = Table(score_rows, colWidths=[60*mm, 55*mm, 55*mm])
        st.setStyle(TableStyle([
            ("BACKGROUND",    (0,0),(-1,0),  DARK_BG),
            ("TEXTCOLOR",     (0,0),(-1,0),  WHITE),
            ("FONTNAME",      (0,0),(-1,0),  "Helvetica-Bold"),
            ("FONTSIZE",      (0,0),(-1,0),  9),
            ("ROWPADDING",    (0,0),(-1,-1), 8),
            ("ROWBACKGROUNDS",(0,1),(-1,-1), [WHITE, SOFT_BG]),
            ("GRID",          (0,0),(-1,-1), 0.4, BORDER),
            ("VALIGN",        (0,0),(-1,-1), "MIDDLE"),
        ]))
        story.append(st)
        story.append(Spacer(1, 10))

    # 7. Footer note
    story.append(Spacer(1, 8))
    story.append(HRFlowable(width="100%", thickness=0.5, color=BORDER))
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        "This report was generated automatically by the AI Interviewer platform. "
        "Scores reflect AI evaluation and should be reviewed alongside human judgment.",
        styles["footer"]))

    doc = build_doc(buf)
    doc.build(story)
    return buf.getvalue()
