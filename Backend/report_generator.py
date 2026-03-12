"""
report_generator.py
-------------------
Generates a professional PDF interview assessment report.
Call: generate_report(session: dict) -> bytes
"""

from io import BytesIO
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus import (
    BaseDocTemplate, PageTemplate, Frame,
    Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether
)

# ─── PALETTE ─────────────────────────────────────────────────────────────────
BLACK       = colors.HexColor("#000000")
WHITE       = colors.white
HEADER_BG   = colors.HexColor("#1C2B4A")
HEADER_FG   = colors.white
ROW_ALT     = colors.HexColor("#F5F7FA")
BORDER      = colors.HexColor("#B0B8C8")
LABEL_BG    = colors.HexColor("#F0F2F6")
TEXT_DARK   = colors.HexColor("#1A1A1A")
C_GREEN     = colors.HexColor("#1A6B3A")
C_AMBER     = colors.HexColor("#7A4500")
C_RED       = colors.HexColor("#8B0000")

PAGE_W      = 174 * mm
COL_LABEL   = 42 * mm
COL_VALUE   = PAGE_W - COL_LABEL


def make_styles():
    return {
        "info_label": ParagraphStyle("info_label",
            fontName="Helvetica-Bold", fontSize=10, leading=14, textColor=TEXT_DARK),
        "info_value": ParagraphStyle("info_value",
            fontName="Helvetica", fontSize=10, leading=14, textColor=TEXT_DARK),
        "info_value_large": ParagraphStyle("info_value_large",
            fontName="Helvetica-Bold", fontSize=13, leading=18, textColor=TEXT_DARK),
        "section_bar": ParagraphStyle("section_bar",
            fontName="Helvetica-Bold", fontSize=11, leading=15, textColor=HEADER_FG),
        "col_header": ParagraphStyle("col_header",
            fontName="Helvetica-Bold", fontSize=10, leading=14, textColor=HEADER_FG),
        "q_label": ParagraphStyle("q_label",
            fontName="Helvetica-Bold", fontSize=10, leading=14, textColor=TEXT_DARK),
        "q_question": ParagraphStyle("q_question",
            fontName="Helvetica-Bold", fontSize=10, leading=15, textColor=TEXT_DARK),
        "q_answer": ParagraphStyle("q_answer",
            fontName="Helvetica", fontSize=10, leading=15, textColor=TEXT_DARK),
        "q_feedback": ParagraphStyle("q_feedback",
            fontName="Helvetica", fontSize=10, leading=15, textColor=TEXT_DARK),
        "q_code": ParagraphStyle("q_code",
            fontName="Courier", fontSize=9, leading=13, textColor=TEXT_DARK),
        "score_good": ParagraphStyle("score_good",
            fontName="Helvetica-Bold", fontSize=11, leading=15,
            textColor=C_GREEN, alignment=TA_CENTER),
        "score_mid": ParagraphStyle("score_mid",
            fontName="Helvetica-Bold", fontSize=11, leading=15,
            textColor=C_AMBER, alignment=TA_CENTER),
        "score_bad": ParagraphStyle("score_bad",
            fontName="Helvetica-Bold", fontSize=11, leading=15,
            textColor=C_RED, alignment=TA_CENTER),
        "score_lbl_good": ParagraphStyle("score_lbl_good",
            fontName="Helvetica", fontSize=8, leading=11,
            textColor=C_GREEN, alignment=TA_CENTER),
        "score_lbl_mid": ParagraphStyle("score_lbl_mid",
            fontName="Helvetica", fontSize=8, leading=11,
            textColor=C_AMBER, alignment=TA_CENTER),
        "score_lbl_bad": ParagraphStyle("score_lbl_bad",
            fontName="Helvetica", fontSize=8, leading=11,
            textColor=C_RED, alignment=TA_CENTER),
        "sum_cell": ParagraphStyle("sum_cell",
            fontName="Helvetica", fontSize=10, leading=14, textColor=TEXT_DARK),
        "sum_good": ParagraphStyle("sum_good",
            fontName="Helvetica-Bold", fontSize=10, leading=14, textColor=C_GREEN),
        "sum_mid": ParagraphStyle("sum_mid",
            fontName="Helvetica-Bold", fontSize=10, leading=14, textColor=C_AMBER),
        "sum_bad": ParagraphStyle("sum_bad",
            fontName="Helvetica-Bold", fontSize=10, leading=14, textColor=C_RED),
        "footer": ParagraphStyle("footer",
            fontName="Helvetica", fontSize=8.5, leading=12,
            textColor=colors.HexColor("#666666"), alignment=TA_CENTER),
    }


def xml_safe(text):
    return (str(text)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;"))

def code_safe(text):
    return (xml_safe(text)
            .replace("\n", "<br/>")
            .replace("\t", "&nbsp;&nbsp;&nbsp;&nbsp;")
            .replace("  ", "&nbsp;&nbsp;"))

def score_rating(score, out_of):
    p = float(score) / out_of
    if p >= 0.8: return "Excellent"
    if p >= 0.6: return "Good"
    if p >= 0.4: return "Fair"
    return "Needs Improvement"

def pick_score_styles(score, out_of, styles):
    p = float(score) / out_of
    if p >= 0.8: return styles["score_good"], styles["score_lbl_good"]
    if p >= 0.5: return styles["score_mid"],  styles["score_lbl_mid"]
    return         styles["score_bad"],        styles["score_lbl_bad"]

def pick_sum_style(score, out_of, styles):
    p = float(score) / out_of
    if p >= 0.8: return styles["sum_good"]
    if p >= 0.5: return styles["sum_mid"]
    return styles["sum_bad"]

def section_bar(title, styles):
    t = Table([[Paragraph(title.upper(), styles["section_bar"])]], colWidths=[PAGE_W])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0,0),(-1,-1), HEADER_BG),
        ("ROWPADDING", (0,0),(-1,-1), (10, 8, 10, 8)),
        ("VALIGN",     (0,0),(-1,-1), "MIDDLE"),
    ]))
    return t

def build_doc(buf, name, role, date_str):
    doc = BaseDocTemplate(
        buf, pagesize=A4,
        leftMargin=18*mm, rightMargin=18*mm,
        topMargin=20*mm, bottomMargin=20*mm,
        title="Interview Assessment Report",
    )

    def draw_page(canvas, doc):
        canvas.saveState()
        W, H = A4
        canvas.setFillColor(HEADER_BG)
        canvas.rect(0, H - 15*mm, W, 15*mm, fill=1, stroke=0)
        canvas.setFont("Helvetica-Bold", 10)
        canvas.setFillColor(WHITE)
        canvas.drawString(18*mm, H - 9.5*mm, "INTERVIEW ASSESSMENT REPORT")
        canvas.setFont("Helvetica", 9)
        canvas.setFillColor(colors.HexColor("#B8C8E8"))
        canvas.drawRightString(W - 18*mm, H - 9.5*mm,
            f"{xml_safe(name)}  |  {xml_safe(role)}")
        canvas.setStrokeColor(BORDER)
        canvas.setLineWidth(0.5)
        canvas.line(18*mm, 13*mm, W - 18*mm, 13*mm)
        canvas.setFont("Helvetica", 8.5)
        canvas.setFillColor(colors.HexColor("#666666"))
        canvas.drawString(18*mm, 8*mm, f"Date: {date_str}  |  Confidential")
        canvas.drawRightString(W - 18*mm, 8*mm, f"Page {doc.page}")
        canvas.restoreState()

    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height,
                  leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=10, id="main")
    doc.addPageTemplates([PageTemplate(id="main", frames=[frame], onPage=draw_page)])
    return doc

def candidate_table(name, role, date_str, duration, total_q, styles):
    col_lbl = 50*mm
    col_val = PAGE_W - col_lbl
    rows = [
        [Paragraph("Candidate Name",   styles["info_label"]), Paragraph(xml_safe(name),          styles["info_value_large"])],
        [Paragraph("Position Applied", styles["info_label"]), Paragraph(xml_safe(role),           styles["info_value"])],
        [Paragraph("Interview Date",   styles["info_label"]), Paragraph(date_str,                 styles["info_value"])],
        [Paragraph("Duration",         styles["info_label"]), Paragraph(xml_safe(str(duration)),  styles["info_value"])],
        [Paragraph("Total Questions",  styles["info_label"]), Paragraph(str(total_q),             styles["info_value"])],
    ]
    t = Table(rows, colWidths=[col_lbl, col_val])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (0, -1),  LABEL_BG),
        ("ROWBACKGROUNDS",(1, 0), (1, -1),  [WHITE, ROW_ALT]),
        ("GRID",          (0, 0), (-1, -1), 0.5, BORDER),
        ("ROWPADDING",    (0, 0), (-1, -1), 9),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("LINEABOVE",     (0, 0), (-1,  0), 2.0, HEADER_BG),
        ("LINEBELOW",     (0,-1), (-1, -1), 1.5, HEADER_BG),
    ]))
    return t

def score_summary_table(history, styles):
    scores_by_round = {}
    for h in history:
        qt = h.get("question_type", "")
        ev = h.get("evaluation") or {}
        sc = ev.get("score") if isinstance(ev, dict) else None
        if sc is not None:
            scores_by_round.setdefault(qt, []).append(sc)

    col_w = [70*mm, 26*mm, 26*mm, 26*mm, 26*mm]
    header = [
        Paragraph("Round",     styles["col_header"]),
        Paragraph("Questions", styles["col_header"]),
        Paragraph("Avg Score", styles["col_header"]),
        Paragraph("Out Of",    styles["col_header"]),
        Paragraph("Rating",    styles["col_header"]),
    ]
    rows = [header]

    for lbl, keys, out_of in [
        ("Behavioral Round",         ["behavioral","fresher"], 5),
        ("Domain / Role Round",      ["role"],                 5),
        ("Technical / Coding Round", ["technical"],           10),
    ]:
        sc_list = []
        for k in keys:
            sc_list.extend(scores_by_round.get(k, []))
        if not sc_list:
            continue
        avg = round(sum(sc_list)/len(sc_list), 1)
        sty = pick_sum_style(avg, out_of, styles)
        rows.append([
            Paragraph(lbl,                      styles["sum_cell"]),
            Paragraph(str(len(sc_list)),         styles["sum_cell"]),
            Paragraph(str(avg),                  sty),
            Paragraph(str(out_of),               styles["sum_cell"]),
            Paragraph(score_rating(avg, out_of), sty),
        ])

    if len(rows) == 1:
        return None

    t = Table(rows, colWidths=col_w)
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1,  0), HEADER_BG),
        ("ROWBACKGROUNDS",(0, 1), (-1, -1), [WHITE, ROW_ALT]),
        ("GRID",          (0, 0), (-1, -1), 0.5, BORDER),
        ("ROWPADDING",    (0, 0), (-1, -1), 9),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN",         (1, 0), (-1, -1), "CENTER"),
        ("LINEABOVE",     (0, 0), (-1,  0), 2.0, HEADER_BG),
        ("LINEBELOW",     (0,-1), (-1, -1), 1.5, HEADER_BG),
    ]))
    return t

def qa_block(index, item, styles):
    qt         = item.get("question_type", "general")
    question   = item.get("question", "")
    answer     = item.get("answer", "")
    evaluation = item.get("evaluation") or {}
    score      = evaluation.get("score") if isinstance(evaluation, dict) else None
    feedback   = evaluation.get("feedback", "") if isinstance(evaluation, dict) else ""
    out_of     = 10 if qt == "technical" else 5

    rows       = []
    fb_row_idx = None

    # Question row
    q_para = Paragraph(xml_safe(question), styles["q_question"])
    if score is not None:
        sc_sty, lbl_sty = pick_score_styles(score, out_of, styles)
        SCORE_COL = 36*mm
        score_inner = Table(
            [[Paragraph(f"{score}/{out_of}", sc_sty)],
             [Paragraph(score_rating(score, out_of), lbl_sty)]],
            colWidths=[SCORE_COL]
        )
        score_inner.setStyle(TableStyle([
            ("ROWPADDING", (0,0),(-1,-1), 1),
            ("ALIGN",      (0,0),(-1,-1), "CENTER"),
        ]))
        inner = Table([[q_para, score_inner]],
                      colWidths=[COL_VALUE - SCORE_COL, SCORE_COL])
        inner.setStyle(TableStyle([
            ("VALIGN",    (0,0),(-1,-1), "TOP"),
            ("ROWPADDING",(0,0),(-1,-1), 0),
            ("LINEAFTER", (0,0),(0,-1),  0.5, BORDER),
        ]))
        rows.append([Paragraph(f"Q{index}", styles["q_label"]), inner])
    else:
        rows.append([Paragraph(f"Q{index}", styles["q_label"]), q_para])

    # Answer row
    if answer:
        if qt == "technical":
            ans_para = Paragraph(code_safe(answer), styles["q_code"])
        else:
            ans_para = Paragraph(xml_safe(answer), styles["q_answer"])
        rows.append([Paragraph("Candidate Answer", styles["q_label"]), ans_para])

    # AI Feedback row
    if feedback:
        fb_row_idx = len(rows)
        rows.append([
            Paragraph("AI Feedback", styles["q_label"]),
            Paragraph(xml_safe(feedback), styles["q_feedback"]),
        ])

    # Technical extras
    if qt == "technical" and isinstance(evaluation, dict):
        for field, label in [
            ("bugs",           "Bugs Identified"),
            ("optimizations",  "Optimisations"),
            ("best_practices", "Best Practices"),
        ]:
            val = evaluation.get(field)
            if val:
                rows.append([Paragraph(label, styles["q_label"]),
                              Paragraph(xml_safe(val), styles["q_answer"])])
        improved = evaluation.get("improved_code")
        if improved:
            rows.append([Paragraph("Suggested Code", styles["q_label"]),
                         Paragraph(code_safe(improved), styles["q_code"])])

    t = Table(rows, colWidths=[COL_LABEL, COL_VALUE])
    cmds = [
        ("BACKGROUND", (0, 0), (0, -1),  LABEL_BG),
        ("BACKGROUND", (1, 0), (1, -1),  WHITE),
        ("ROWBACKGROUNDS", (1, 0), (1, -1), [WHITE, ROW_ALT]),
        ("GRID",       (0, 0), (-1, -1), 0.5, BORDER),
        ("ROWPADDING", (0, 0), (-1, -1), 8),
        ("VALIGN",     (0, 0), (-1, -1), "TOP"),
        ("LINEABOVE",  (0, 0), (-1,  0), 1.5, HEADER_BG),
        ("LINEBELOW",  (0,-1), (-1, -1), 1.0, BORDER),
    ]
    if fb_row_idx is not None:
        cmds.append(("BACKGROUND", (0, fb_row_idx), (1, fb_row_idx),
                     colors.HexColor("#EDF2FB")))
    t.setStyle(TableStyle(cmds))
    return [t, Spacer(1, 10)]


def generate_report(session: dict) -> bytes:
    buf      = BytesIO()
    styles   = make_styles()
    history  = session.get("history", [])
    name     = session.get("name", "Candidate")
    role     = session.get("role", "")
    q_count  = session.get("q_count", len(history))
    date_str = datetime.now().strftime("%d %B %Y")
    duration = session.get("duration", "")

    doc   = build_doc(buf, name, role, date_str)
    story = []

    story.append(section_bar("Candidate Information", styles))
    story.append(Spacer(1, 1))
    story.append(candidate_table(name, role, date_str, duration, q_count, styles))
    story.append(Spacer(1, 16))

    summary = score_summary_table(history, styles)
    if summary:
        story.append(section_bar("Score Summary", styles))
        story.append(Spacer(1, 1))
        story.append(summary)
        story.append(Spacer(1, 16))

    beh = [h for h in history if h.get("question_type") in ("behavioral","fresher")]
    if beh:
        story.append(section_bar("Behavioral Round", styles))
        story.append(Spacer(1, 8))
        for i, item in enumerate(beh, 1):
            story.extend(qa_block(i, item, styles))
        story.append(Spacer(1, 6))

    domain = [h for h in history if h.get("question_type") == "role"]
    if domain:
        story.append(section_bar("Domain / Role Round", styles))
        story.append(Spacer(1, 8))
        off = len(beh)
        for i, item in enumerate(domain, off+1):
            story.extend(qa_block(i, item, styles))
        story.append(Spacer(1, 6))

    tech = [h for h in history if h.get("question_type") == "technical"]
    if tech:
        story.append(section_bar("Technical / Coding Round", styles))
        story.append(Spacer(1, 8))
        off = len(beh) + len(domain)
        for i, item in enumerate(tech, off+1):
            story.extend(qa_block(i, item, styles))
        story.append(Spacer(1, 6))

    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", thickness=0.5, color=BORDER))
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        "This report has been generated by the AI Interviewer platform. Scores and feedback "
        "reflect automated AI evaluation and should be considered alongside human judgment. "
        "This document is confidential and intended solely for authorised personnel.",
        styles["footer"]))

    doc.build(story)
    return buf.getvalue()
