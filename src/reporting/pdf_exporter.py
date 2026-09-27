"""
PDF Exporter for Module 7 — Reporting Layer.
Generates clean, human-readable, professional clinical decision-support reports in PDF format.
Strictly adheres to:
- Exact 7-section clinical report structure
- No raw markdown syntax (**, |, ---, \\()
- Professional typography (Helvetica / Helvetica-Bold)
- Academic Blue + Black theme (#1F4E79, #2F75B5, #000000)
- Clean page wrapping and table layouts
"""

import io
import re
from typing import Union, Optional
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfgen import canvas


class NumberedCanvas(canvas.Canvas):
    """Canvas that computes total pages dynamically for clean page numbering."""
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
            self.draw_page_number(num_pages)
            super().showPage()
        super().save()

    def draw_page_number(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748B"))
        # Top Header
        self.drawString(40, 762, "CLINICAL DECISION-SUPPORT SYSTEM - AUDIT REPORT")
        self.setStrokeColor(colors.HexColor("#CBD5E1"))
        self.setLineWidth(0.5)
        self.line(40, 756, 572, 756)
        
        # Bottom Footer
        self.line(40, 42, 572, 42)
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(572, 30, page_str)
        self.drawString(40, 30, "CONFIDENTIAL & MACHINE-ASSISTED CLINICAL SUPPORT")
        self.restoreState()


def build_clinical_report_pdf(report_text: str, output_target: Optional[Union[str, io.BytesIO]] = None) -> io.BytesIO:
    """
    Renders standardized clinical report text into a professional PDF document.
    Can write to a file path or return an in-memory BytesIO buffer.
    """
    if output_target is None:
        buf = io.BytesIO()
        target = buf
    elif isinstance(output_target, str):
        target = output_target
    else:
        target = output_target

    doc = SimpleDocTemplate(
        target,
        pagesize=letter,
        leftMargin=40,
        rightMargin=40,
        topMargin=50,
        bottomMargin=50
    )

    styles = getSampleStyleSheet()

    # Palette
    c_dark_blue = colors.HexColor("#1F4E79")
    c_blue = colors.HexColor("#2F75B5")
    c_light_blue = colors.HexColor("#F0F4F8")
    c_gray = colors.HexColor("#64748B")
    c_border = colors.HexColor("#D0D7DE")

    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=17,
        leading=21,
        textColor=c_dark_blue,
        alignment=TA_CENTER,
        spaceAfter=12
    )

    h1_style = ParagraphStyle(
        'SectionH1',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11.5,
        leading=15.5,
        textColor=c_dark_blue,
        spaceBefore=10,
        spaceAfter=4,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        'SectionH2',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=13.5,
        textColor=c_blue,
        spaceBefore=7,
        spaceAfter=3,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'ReportBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=colors.black
    )

    body_bold_style = ParagraphStyle(
        'ReportBodyBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=13,
        textColor=colors.black
    )

    decision_style = ParagraphStyle(
        'DecisionHero',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=17,
        alignment=TA_CENTER,
        spaceBefore=4,
        spaceAfter=4
    )

    disclaimer_style = ParagraphStyle(
        'Disclaimer',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=8,
        leading=11,
        textColor=c_gray,
        spaceBefore=10
    )

    story = []
    lines = report_text.strip().split('\n')

    i = 0
    while i < len(lines):
        line = lines[i].strip()
        line = line.replace('’', "'").replace('‘', "'").replace('“', '"').replace('”', '"')
        i += 1

        if not line:
            story.append(Spacer(1, 3))
            continue

        # Document Title
        if "Patient Clinical Decision-Support Report" in line:
            clean_title = re.sub(r'[^\x00-\x7F]+', '', line).replace('#', '').strip()
            if not clean_title:
                clean_title = "Patient Clinical Decision-Support Report"
            story.append(Paragraph(clean_title, title_style))
            story.append(HRFlowable(width="100%", thickness=1.5, color=c_dark_blue, spaceBefore=2, spaceAfter=8))
            continue

        # Major Section Headings (1. PATIENT INFORMATION, 2. DISEASE PREDICTION, etc.)
        m_sec = re.match(r'^(?:#+\s*)?([1-7]\.\s*(?:[^\w\s]*\s*)?[A-Za-z\s&]+)$', line)
        if m_sec:
            sec_title = re.sub(r'[^\x00-\x7F]+', '', m_sec.group(1)).strip()
            story.append(Spacer(1, 4))
            story.append(Paragraph(sec_title, h1_style))
            story.append(HRFlowable(width="100%", thickness=0.75, color=c_blue, spaceBefore=1, spaceAfter=5))
            continue

        # Sub-headings in Section 6 (A. Contradiction Analysis, B. Consensus Analysis, C. Trust Score)
        m_subsec = re.match(r'^(?:#+\s*)?([A-C]\.\s*(?:[^\w\s]*\s*)?[A-Za-z\s]+)$', line)
        if m_subsec:
            subsec_title = re.sub(r'[^\x00-\x7F]+', '', m_subsec.group(1)).strip()
            story.append(Paragraph(subsec_title, h2_style))
            continue

        if "CLINICAL INTERPRETATION" in line.upper():
            subsec_title = re.sub(r'[^\x00-\x7F]+', '', line).replace('#', '').strip()
            if not subsec_title:
                subsec_title = "CLINICAL INTERPRETATION"
            story.append(Spacer(1, 4))
            story.append(Paragraph(subsec_title, h2_style))
            continue

        if line.strip().upper() == "FINAL SYSTEM DECISION":
            continue

        # SHAP Table Header & Rows
        if line.startswith("Feature | Impact | SHAP Value | Raw Value"):
            shap_rows = [["Feature", "Impact", "SHAP Value", "Raw Value"]]
            while i < len(lines) and lines[i].strip() and "|" in lines[i]:
                parts = [p.strip() for p in lines[i].split("|")]
                if len(parts) == 4:
                    if len(shap_rows) <= 5:  # Header is index 0, so exactly at most 5 feature data rows
                        shap_rows.append(parts)
                i += 1

            tbl_data = []
            for r_idx, r in enumerate(shap_rows):
                if r_idx == 0:
                    tbl_data.append([
                        Paragraph(cell, ParagraphStyle('TH', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=8.5, textColor=colors.white))
                        for cell in r
                    ])
                else:
                    imp_lower = r[1].lower()
                    imp_color = colors.HexColor("#DC2626") if "increase" in imp_lower else (colors.HexColor("#16A34A") if "decrease" in imp_lower else colors.black)
                    cell_0 = Paragraph(r[0], body_bold_style)
                    cell_1 = Paragraph(r[1], ParagraphStyle('Imp', parent=body_style, fontName='Helvetica-Bold', textColor=imp_color))
                    cell_2 = Paragraph(r[2], body_style)
                    cell_3 = Paragraph(r[3], body_style)
                    tbl_data.append([cell_0, cell_1, cell_2, cell_3])

            shap_table = Table(tbl_data, colWidths=[170, 125, 115, 122])
            shap_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), c_dark_blue),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3.5),
                ('TOPPADDING', (0, 0), (-1, -1), 3.5),
                ('GRID', (0, 0), (-1, -1), 0.5, c_border),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, c_light_blue])
            ]))
            story.append(shap_table)
            story.append(Spacer(1, 6))
            continue

        # Final System Decision Card
        if "— DETECTED" in line or "— NOT DETECTED" in line or "- DETECTED" in line or "- NOT DETECTED" in line:
            clean_line = re.sub(r'[^\x00-\x7F—–-]+', '', line).replace('—', ' &mdash; ').replace('–', ' &mdash; ').strip()
            is_det = "NOT DETECTED" not in clean_line and "DETECTED" in clean_line
            det_color = colors.HexColor("#DC2626") if is_det else colors.HexColor("#16A34A")

            p_box = Paragraph(clean_line, ParagraphStyle('DecHero', parent=decision_style, textColor=det_color))
            box_data = [[p_box]]
            box_table = Table(box_data, colWidths=[532])
            box_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#FEF2F2") if is_det else colors.HexColor("#F0FDF4")),
                ('BORDER', (0, 0), (-1, -1), 1.5, det_color),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]))
            story.append(box_table)
            story.append(Spacer(1, 5))
            continue

        # Disclaimer - completely omitted from patient report downloads
        if line.startswith("NOTICE:") or line.startswith("NOTE:") or "machine-assisted clinical decision support" in line:
            continue

        # Key-Value Lines
        if ":" in line and not line.startswith("http"):
            parts = line.split(":", 1)
            key = re.sub(r'[^\x00-\x7F]+', '', parts[0]).strip()
            val = re.sub(r'[^\x00-\x7F—–-]+', '', parts[1]).replace('—', ' &mdash; ').replace('–', ' &mdash; ').strip()
            p_text = f"<b>{key}:</b> {val}"
            story.append(Paragraph(p_text, body_style))
            continue

        # Standard Paragraph Line
        clean_line = re.sub(r'[^\x00-\x7F—–-]+', '', line).replace('—', ' &mdash; ').replace('–', ' &mdash; ').strip()
        if clean_line:
            story.append(Paragraph(clean_line, body_style))

    doc.build(story, canvasmaker=NumberedCanvas)

    if isinstance(target, io.BytesIO):
        target.seek(0)
        return target
    return target
