import sys
import os
import shutil
import docx
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import parse_xml, OxmlElement
from docx.oxml.ns import nsdecls, qn

sys.stdout.reconfigure(encoding='utf-8')

# ==============================================================================
# PROFESSIONAL ACADEMIC BLUE + BLACK COLOR PALETTE
# ==============================================================================
DARK_BLUE_HEX = "1F4E79"
BLUE_HEX = "2F75B5"
BLACK_HEX = "000000"
WHITE_HEX = "FFFFFF"
BORDER_GRAY_HEX = "D0D7DE"

DARK_BLUE_RGB = RGBColor(0x1F, 0x4E, 0x79)
BLUE_RGB = RGBColor(0x2F, 0x75, 0xB5)
BLACK_RGB = RGBColor(0x00, 0x00, 0x00)
WHITE_RGB = RGBColor(0xFF, 0xFF, 0xFF)

DOC_PATH = r"C:\Users\Dell_PC\Downloads\MultiCDSS.docx"
BACKUP_PATH = r"C:\Users\Dell_PC\Downloads\MultiCDSS.original.backup.docx"
WORKSPACE_PATH = r"D:\MultiAgent_CDSS\MultiCDSS.docx"
WORKSPACE_BACKUP = r"D:\MultiAgent_CDSS\MultiCDSS.original.backup.docx"

# Ensure pristine backup exists before any changes
if not os.path.exists(BACKUP_PATH):
    shutil.copy2(DOC_PATH, BACKUP_PATH)
if not os.path.exists(WORKSPACE_BACKUP):
    shutil.copy2(DOC_PATH, WORKSPACE_BACKUP)

# Always load from pristine backup so formatting is completely reproducible
doc = docx.Document(BACKUP_PATH)

# ==============================================================================
# RECORD ORIGINAL CONTENT FOR STRICT VERIFICATION
# ==============================================================================
original_p_texts = [p.text for p in doc.paragraphs]
original_t_texts = [[[c.text for c in row.cells] for row in t.rows] for t in doc.tables]

def set_cell_shading(cell, color_hex):
    """Sets the background fill color of a table cell."""
    tcPr = cell._tc.get_or_add_tcPr()
    for child in list(tcPr):
        if child.tag.endswith('shd'):
            tcPr.remove(child)
    tcPr.append(parse_xml(f'<w:shd {nsdecls("w")} w:fill="{color_hex}" w:val="clear"/>'))

def set_table_styling(tbl):
    """Applies clean academic table borders (top/bottom dark blue, subtle interior row lines, no vertical lines)."""
    tblPr = tbl._tbl.tblPr
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    for child in list(tblPr):
        if child.tag.endswith('tblBorders'):
            tblPr.remove(child)
    borders_xml = f'''
    <w:tblBorders {nsdecls("w")}>
        <w:top w:val="single" w:sz="8" w:space="0" w:color="{DARK_BLUE_HEX}"/>
        <w:left w:val="none"/>
        <w:bottom w:val="single" w:sz="8" w:space="0" w:color="{DARK_BLUE_HEX}"/>
        <w:right w:val="none"/>
        <w:insideH w:val="single" w:sz="4" w:space="0" w:color="{BORDER_GRAY_HEX}"/>
        <w:insideV w:val="none"/>
    </w:tblBorders>
    '''
    tblPr.append(parse_xml(borders_xml))

# ==============================================================================
# 1. PARAGRAPH FORMATTING (Blue & Black Theme)
# ==============================================================================
MAIN_HEADINGS_INDICES = {11, 18, 22, 36, 108, 111}
SUB_HEADINGS_INDICES = {37, 43, 44, 49, 55, 65, 70}
FIGURE_CAPTIONS_INDICES = {25, 90, 96, 104}
TABLE_CAPTIONS_INDICES = {40, 72, 77, 84}

for i, p in enumerate(doc.paragraphs):
    raw_text = p.text.strip()
    if not raw_text:
        continue

    # 1. Main Document Title (P1)
    if i == 1:
        for r in p.runs:
            r.font.name = "Times New Roman"
            r.font.color.rgb = DARK_BLUE_RGB
            r.bold = True
        continue

    # 2. Main Section Headings (I. INTRODUCTION, II. LITERATURE REVIEW, III. PROPOSED SYSTEM, IV. RESULT, V. CONCLUSION, VI. REFERENCES)
    if i in MAIN_HEADINGS_INDICES:
        for r in p.runs:
            r.font.name = "Times New Roman"
            r.font.color.rgb = DARK_BLUE_RGB
            r.bold = True
        continue

    # 3. Subsection Headings (A. Dataset, B. PERFORMANCE MATRIX, C. EXPERIMENT RESULT, Confusion Matrix:, Accuracy:, Precision & Recall, F1-Score)
    if i in SUB_HEADINGS_INDICES:
        for r in p.runs:
            r.font.name = "Times New Roman"
            r.font.color.rgb = BLUE_RGB
            r.bold = True
        continue

    # 4. Figure Captions
    if i in FIGURE_CAPTIONS_INDICES:
        for r in p.runs:
            r.font.name = "Times New Roman"
            r.font.color.rgb = DARK_BLUE_RGB
            if any(fig_lbl in r.text for fig_lbl in ["Fig. 1.", "Fig. 2.", "Fig. 3."]):
                r.bold = True
        continue

    # 5. Table Captions
    if i in TABLE_CAPTIONS_INDICES:
        for r in p.runs:
            r.font.name = "Times New Roman"
            r.font.color.rgb = DARK_BLUE_RGB
            if any(t_lbl in r.text for t_lbl in ["TABLE I.", "TABLE II.", "Table III.", "TABLE III."]):
                r.bold = True
        continue

    # 6. Abstract (P6): Label in Dark Blue Bold, abstract body in Black
    if i == 6:
        for r in p.runs:
            r.font.name = "Times New Roman"
            if "Abstract" in r.text:
                r.font.color.rgb = DARK_BLUE_RGB
                r.bold = True
            else:
                r.font.color.rgb = BLACK_RGB
        continue

    # 7. Keywords (P7, P10): Label in Dark Blue Bold, keywords in Black
    if i in (7, 10):
        for r in p.runs:
            r.font.name = "Times New Roman"
            if "Keywords" in r.text:
                r.font.color.rgb = DARK_BLUE_RGB
                r.bold = True
            else:
                r.font.color.rgb = BLACK_RGB
        continue

    # 8. Key terms in Proposed System (P28, P29, P32, P33, P34, P35): Agent names in Dark Blue Bold
    if i in (28, 29, 32, 33, 34, 35):
        for r in p.runs:
            r.font.name = "Times New Roman"
            agent_names = [
                "Disease Prediction Agent",
                "Explainability Agent",
                "Biomedical Evidence Agent",
                "Reasoning Agent",
                "Decision Fusion Agent",
                "Clinical Reporting Agent"
            ]
            if any(agent in r.text for agent in agent_names):
                r.font.color.rgb = DARK_BLUE_RGB
                r.bold = True
            else:
                r.font.color.rgb = BLACK_RGB
        continue

    # 9. General Body Text & References (All other paragraphs): Pure Black
    for r in p.runs:
        r.font.name = "Times New Roman"
        r.font.color.rgb = BLACK_RGB

# ==============================================================================
# 2. TABLE FORMATTING
# ==============================================================================
# Tables 0 & 1: Author & Affiliation Blocks (Academic IEEE Header)
for t_idx in [0, 1]:
    tbl = doc.tables[t_idx]
    for row in tbl.rows:
        for c in row.cells:
            set_cell_shading(c, WHITE_HEX)
            for p_idx, p in enumerate(c.paragraphs):
                for r in p.runs:
                    r.font.name = "Times New Roman"
                    # Author names in Dark Blue Bold
                    if p_idx == 0:
                        r.font.color.rgb = DARK_BLUE_RGB
                        r.bold = True
                    else:
                        r.font.color.rgb = BLACK_RGB

# Tables 2 to 6: Data Tables (TABLE I, Confusion Matrix, TABLE II, Table III sequential, TABLE III report)
for t_idx in range(2, len(doc.tables)):
    tbl = doc.tables[t_idx]
    set_table_styling(tbl)
    
    # Header Row (Row 0): Dark Blue background, White bold text
    for c in tbl.rows[0].cells:
        set_cell_shading(c, DARK_BLUE_HEX)
        c.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
        for p in c.paragraphs:
            p.paragraph_format.space_before = Pt(2)
            p.paragraph_format.space_after = Pt(2)
            for r in p.runs:
                r.font.name = "Times New Roman"
                r.font.color.rgb = WHITE_RGB
                r.bold = True

    # Data Rows (Row 1+): White background, Black text
    for row in tbl.rows[1:]:
        for c_idx, c in enumerate(row.cells):
            set_cell_shading(c, WHITE_HEX)
            c.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
            for p in c.paragraphs:
                p.paragraph_format.space_before = Pt(1)
                p.paragraph_format.space_after = Pt(1)
                for r in p.runs:
                    r.font.name = "Times New Roman"
                    r.font.color.rgb = BLACK_RGB

# ==============================================================================
# 3. HEADER & FOOTER (Minimal Academic Page Numbers)
# ==============================================================================
for sec_idx, sec in enumerate(doc.sections):
    footer = sec.footer
    # Clean any empty paragraphs
    p_ft = footer.paragraphs[0] if footer.paragraphs else footer.add_paragraph()
    p_ft.text = ""  # Reset any text
    p_ft.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    
    r_ft = p_ft.add_run("Multi-Agent CDSS  |  Page ")
    r_ft.font.name = "Times New Roman"
    r_ft.font.size = Pt(8.5)
    r_ft.font.color.rgb = DARK_BLUE_RGB
    
    # Native Word PAGE field
    fld_page = parse_xml(f'<w:fldSimple {nsdecls("w")} w:instr="PAGE"/>')
    p_ft._p.append(fld_page)

# ==============================================================================
# 4. STRICT VERIFICATION: 100% CONTENT INTEGRITY ASSERTION
# ==============================================================================
current_p_texts = [p.text for p in doc.paragraphs]
current_t_texts = [[[c.text for c in row.cells] for row in t.rows] for t in doc.tables]

assert len(original_p_texts) == len(current_p_texts), (
    f"Paragraph count changed! Original: {len(original_p_texts)}, Current: {len(current_p_texts)}"
)
for i, (orig, curr) in enumerate(zip(original_p_texts, current_p_texts)):
    assert orig == curr, f"Paragraph {i} content modified!\nORIG: {orig}\nCURR: {curr}"

assert len(original_t_texts) == len(current_t_texts), (
    f"Table count changed! Original: {len(original_t_texts)}, Current: {len(current_t_texts)}"
)
for t_idx, (orig_tbl, curr_tbl) in enumerate(zip(original_t_texts, current_t_texts)):
    assert len(orig_tbl) == len(curr_tbl), f"Table {t_idx} row count changed!"
    for r_idx, (orig_row, curr_row) in enumerate(zip(orig_tbl, curr_tbl)):
        assert len(orig_row) == len(curr_row), f"Table {t_idx} row {r_idx} cell count changed!"
        for c_idx, (orig_c, curr_c) in enumerate(zip(orig_row, curr_row)):
            assert orig_c == curr_c, (
                f"Table {t_idx} cell ({r_idx},{c_idx}) content modified!\nORIG: {orig_c}\nCURR: {curr_c}"
            )

print("=" * 60)
print("CONTENT INTEGRITY CHECK PASSED: ZERO CONTENT WAS CHANGED!")
print("=" * 60)

# ==============================================================================
# 5. SAVE FORMATTED DOCUMENT
# ==============================================================================
doc.save(DOC_PATH)
doc.save(WORKSPACE_PATH)

print(f"Successfully saved formatted document to:\n  1. {DOC_PATH}\n  2. {WORKSPACE_PATH}")
