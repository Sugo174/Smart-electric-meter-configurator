"""Форматирование и печать сохранённых параметров прибора."""

from html import escape
from io import BytesIO
import os
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import LongTable, Paragraph, SimpleDocTemplate


def snapshot_children(value):
    if isinstance(value, dict):
        return value.items()
    if isinstance(value, list) and any(isinstance(item, dict) for item in value):
        return ((str(index), item) for index, item in enumerate(value, 1))
    return None


def snapshot_value(value):
    if value is None:
        return "—"
    if isinstance(value, bool):
        return "Да" if value else "Нет"
    if isinstance(value, list):
        return ", ".join(map(str, value)) or "—"
    return str(value)


def create_snapshot_pdf(snapshot):
    fonts = Path(os.environ.get("WINDIR", r"C:\Windows")) / "Fonts"
    for name, path in (("EmisReport", "arial.ttf"), ("EmisReportBold", "arialbd.ttf")):
        pdfmetrics.registerFont(TTFont(name, str(fonts / path)))

    green = colors.HexColor("#00664D")
    muted = colors.HexColor("#437467")
    dark = colors.HexColor("#24332F")
    light = colors.HexColor("#DDF3EB")
    line = colors.HexColor("#9EC8BB")
    normal = ParagraphStyle("Value", fontName="EmisReport", fontSize=10, leading=14, textColor=dark)
    heading = ParagraphStyle("Heading", parent=normal, fontName="EmisReportBold", textColor=green)
    title = ParagraphStyle("Title", parent=heading, fontSize=19, leading=24, spaceAfter=16)

    def paragraph(text, style):
        return Paragraph(escape(text).replace("\n", "<br/>"), style)

    rows = [(paragraph("Параметр", heading), paragraph("Значение", heading))]
    table_style = [
        ("BACKGROUND", (0, 0), (-1, 0), light),
        ("LINEAFTER", (0, 0), (0, -1), 0.6, line),
        ("LINEBELOW", (0, 0), (-1, 0), 0.6, line),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 9),
        ("RIGHTPADDING", (0, 0), (-1, -1), 9),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]

    def add_rows(items, depth=0):
        for name, value in items:
            children = snapshot_children(value)
            if children is None:
                caption = ParagraphStyle("Caption", parent=normal, textColor=muted, leftIndent=depth * 10)
                rows.append((paragraph(name, caption), paragraph(snapshot_value(value), normal)))
                continue

            row = len(rows)
            group = ParagraphStyle("Group", parent=heading, leftIndent=depth * 10)
            rows.append((paragraph(name, group), ""))
            table_style.append(("BACKGROUND", (0, row), (-1, row), colors.HexColor("#F1F7F4")))
            children = list(children)
            if children:
                table_style.append(("NOSPLIT", (0, row), (-1, row + 1)))
                add_rows(children, depth + 1)

    add_rows(snapshot.items())
    stream = BytesIO()
    document = SimpleDocTemplate(
        stream, pagesize=A4, leftMargin=32, rightMargin=32, topMargin=34, bottomMargin=34,
        title="Выгрузка EMIS",
    )
    table = LongTable(rows, colWidths=(document.width * 0.53, document.width * 0.47),
                      repeatRows=1, splitInRow=1, style=table_style)
    document.build([paragraph("Выгрузка EMIS", title), table])
    return stream.getvalue()
