from pathlib import Path
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer

ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / "docs" / "procurement_pack"


def _read_markdown(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _convert_md_to_story(md_text: str, one_page: bool = False):
    styles = getSampleStyleSheet()
    if one_page:
        normal = ParagraphStyle("NormalCompact", parent=styles["Normal"], fontSize=8, leading=9, spaceAfter=1)
        heading = ParagraphStyle("HeadingCompact", parent=styles["Heading2"], fontSize=10, leading=11, spaceBefore=3, spaceAfter=2)
        heading1 = ParagraphStyle("Heading1Compact", parent=styles["Heading1"], fontSize=12, leading=13, spaceAfter=3)
        bullet = ParagraphStyle("BulletCompact", parent=normal, leftIndent=10, bulletIndent=4, spaceAfter=1)
    else:
        normal = styles["Normal"]
        heading = styles["Heading2"]
        heading1 = styles["Heading1"]
        bullet = ParagraphStyle("Bullet", parent=normal, leftIndent=16, bulletIndent=8, spaceAfter=4)

    story = []
    spacer_h = 3 if one_page else 8

    for raw in md_text.splitlines():
        line = raw.strip()
        if not line:
            story.append(Spacer(1, spacer_h))
            continue

        if line.startswith("# "):
            story.append(Paragraph(line[2:].strip(), heading1))
            story.append(Spacer(1, spacer_h))
        elif line.startswith("## "):
            story.append(Paragraph(line[3:].strip(), heading))
        elif line.startswith("### "):
            story.append(Paragraph(f"<b>{line[4:].strip()}</b>", normal))
        elif line.startswith("- "):
            story.append(Paragraph(f"• {line[2:].strip()}", bullet))
        else:
            cleaned = line.replace("**", "")
            story.append(Paragraph(cleaned, normal))

    return story


def build_pdf(md_filename: str, pdf_filename: str, one_page: bool = False):
    md_path = DOCS / md_filename
    pdf_path = DOCS / pdf_filename
    text = _read_markdown(md_path)
    margins = dict(leftMargin=28, rightMargin=28, topMargin=28, bottomMargin=28) if one_page else dict(leftMargin=40, rightMargin=40, topMargin=40, bottomMargin=40)
    doc = SimpleDocTemplate(str(pdf_path), pagesize=LETTER, **margins)
    story = _convert_md_to_story(text, one_page=one_page)
    doc.build(story)


if __name__ == "__main__":
    build_pdf("Lex_Aureon_Security_Whitepaper.md", "Lex_Aureon_Security_Whitepaper.pdf")
    build_pdf("Lex_Aureon_Architecture_One_Pager.md", "Lex_Aureon_Architecture_One_Pager.pdf", one_page=True)
    print("Generated PDFs in docs/procurement_pack")
