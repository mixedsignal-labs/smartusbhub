#!/usr/bin/env python3
"""Build separate themed SmartUSBHub PDFs from Markdown sources."""

from __future__ import annotations

import argparse
import html
import io
import re
import sys
from pathlib import Path
from typing import Iterable
from urllib.parse import quote, unquote

try:
    from reportlab import rl_config
    from PIL import Image as PILImage
    from pypdf import PdfReader
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.platypus import (
        BaseDocTemplate,
        Flowable,
        Frame,
        HRFlowable,
        Image,
        ListFlowable,
        ListItem,
        PageBreak,
        PageTemplate,
        Paragraph,
        Preformatted,
        Spacer,
        Table,
        TableStyle,
    )
    from reportlab.platypus.tableofcontents import TableOfContents
    from reportlab.platypus.tables import CellStyle
    from svglib.svglib import svg2rlg
    from fontTools.ttLib import TTFont as VariableTTFont
    from fontTools.varLib.instancer import instantiateVariableFont
except ModuleNotFoundError as exc:
    print(
        "Missing PDF dependency. Install with:\n"
        "  python3 -m pip install -r scripts/requirements-pdf.txt\n"
        f"Original error: {exc}",
        file=sys.stderr,
    )
    raise SystemExit(2) from exc


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "output" / "pdf"
TMP_DIR = ROOT / "tmp" / "pdfs"
CALLOUT_ASSET_DIR = ROOT / "scripts" / "assets" / "manual-icons"
WEBSITE_LABEL = "www.mixedsignallab.com"
WEBSITE_URL = "https://www.mixedsignallab.com"
GITHUB_BASE = "https://github.com/mixedsignal-labs/smartusbhub/blob/main/"
THEME_PRIMARY = "#1473E6"
THEME_DARK = "#17365D"
THEME_BODY = "#111111"
THEME_MUTED = "#5F6B7A"
THEME_PALE = "#EAF2FC"
THEME_LINE = "#D9E2F3"
THEME_WARNING = "#B42318"
THEME_WARNING_PALE = "#FDECEA"
THEME_CAUTION = "#F4C542"
THEME_CAUTION_PALE = "#FFF7D6"
THEME_SUCCESS = "#237A3B"
THEME_SUCCESS_PALE = "#F2FAF4"

DOCUMENTS = {
    "usb2_4p_guide": {
        "product": "usb2_4p",
        "language": "zh",
        "title": "SmartUSBHub Pro 4CH USB2.0",
        "document_type": "使用指南",
        "model": "HBP_USB2_4CH / HBP_USB2_4CH_PSU",
        "source": "docs/products/usb2_4p/user_guide_cn.md",
        "output": "HBP_USB2_4CH_使用指南.pdf",
    },
    "usb2_4p_spec": {
        "product": "usb2_4p",
        "language": "zh",
        "title": "SmartUSBHub Pro 4CH USB2.0",
        "document_type": "技术规格书",
        "model": "HBP_USB2_4CH / HBP_USB2_4CH_PSU",
        "source": "docs/products/usb2_4p/datasheet_cn.md",
        "output": "HBP_USB2_4CH_技术规格书.pdf",
    },
    "usb2_4p_spec_en": {
        "product": "usb2_4p",
        "language": "en",
        "title": "SmartUSBHub Pro 4CH USB2.0",
        "document_type": "Technical Specifications",
        "model": "HBP_USB2_4CH / HBP_USB2_4CH_PSU",
        "source": "docs/products/usb2_4p/datasheet.md",
        "output": "SmartUSBHub_Pro_4CH_USB2.0_Technical_Specifications_v1.0_EN.pdf",
    },
    "usb2_7p_guide": {
        "product": "usb2_7p",
        "language": "zh",
        "title": "SmartUSBHub Pro 7CH USB2.0",
        "document_type": "使用指南",
        "model": "HBP_USB2_7CH / HBP_USB2_7CH_ADV",
        "source": "docs/products/usb2_7p/user_guide_cn.md",
        "output": "HBP_USB2_7CH_使用指南.pdf",
    },
    "usb2_7p_spec": {
        "product": "usb2_7p",
        "language": "zh",
        "title": "SmartUSBHub Pro 7CH USB2.0",
        "document_type": "技术规格书",
        "model": "HBP_USB2_7CH / HBP_USB2_7CH_ADV",
        "source": "docs/products/usb2_7p/datasheet_cn.md",
        "output": "HBP_USB2_7CH_技术规格书.pdf",
    },
    "usb2_7p_spec_en": {
        "product": "usb2_7p",
        "language": "en",
        "title": "SmartUSBHub Pro 7CH USB2.0",
        "document_type": "Technical Specifications",
        "model": "HBP_USB2_7CH / HBP_USB2_7CH_ADV",
        "source": "docs/products/usb2_7p/datasheet.md",
        "output": "SmartUSBHub_Pro_7CH_USB2.0_Technical_Specifications_v1.0_EN.pdf",
    },
    "protocol": {
        "product": "shared",
        "language": "zh",
        "title": "SmartUSBHub",
        "document_type": "通信协议",
        "model": "SmartUSBHub 产品系列",
        "source": "docs/protocol_cn.md",
        "output": "SmartUSBHub_通信协议.pdf",
    },
    "protocol_en": {
        "product": "shared",
        "language": "en",
        "title": "SmartUSBHub",
        "document_type": "Communication Protocol",
        "model": "SmartUSBHub Product Family",
        "source": "docs/protocol.md",
        "output": "SmartUSBHub_Communication_Protocol_v1.0_EN.pdf",
    },
}

LOCAL_ANCHORS: dict[tuple[str, str], str] = {}


def find_font(candidates: Iterable[str]) -> Path:
    for candidate in candidates:
        path = Path(candidate)
        if path.exists():
            return path
    raise RuntimeError(
        "Source Han Sans SC was not found. Install the Adobe open-source "
        "SourceHanSansSC-VF.ttf font before building PDFs."
    )


def register_fonts() -> None:
    variable = find_font(
        [
            str(ROOT.parent.parent / "fonts/adobe/install/source-han-sans-sc/SourceHanSansSC-VF.ttf"),
            str(Path.home() / "Library/Fonts/SourceHanSansSC-VF.ttf"),
            "/Library/Fonts/SourceHanSansSC-VF.ttf",
        ]
    )
    font_dir = TMP_DIR / "fonts"
    font_dir.mkdir(parents=True, exist_ok=True)

    def static_instance(weight: int, style: str) -> Path:
        output = font_dir / f"SourceHanSansSC-{style}.ttf"
        if output.exists() and output.stat().st_mtime >= variable.stat().st_mtime:
            return output
        font = VariableTTFont(str(variable))
        instance = instantiateVariableFont(font, {"wght": weight}, inplace=False)
        names = instance["name"]
        family = "Source Han Sans SC"
        full_name = f"{family} {style}"
        postscript_name = f"SourceHanSansSC-{style}"
        for name_id, value in (
            (1, family),
            (2, style),
            (4, full_name),
            (6, postscript_name),
        ):
            names.removeNames(nameID=name_id)
            names.setName(value, name_id, 3, 1, 0x409)
            names.setName(value, name_id, 1, 0, 0)
        instance.save(output)
        return output

    regular = static_instance(400, "Regular")
    bold = static_instance(700, "Bold")
    pdfmetrics.registerFont(TTFont("DocCJK", str(regular), subfontIndex=0))
    pdfmetrics.registerFont(TTFont("DocCJKBold", str(bold), subfontIndex=0))
    pdfmetrics.registerFontFamily(
        "DocCJK",
        normal="DocCJK",
        bold="DocCJKBold",
        italic="DocCJK",
        boldItalic="DocCJKBold",
    )
    rl_config.canvas_basefontname = "DocCJK"
    CellStyle.fontname = "DocCJK"


def make_styles() -> dict[str, ParagraphStyle]:
    sample = getSampleStyleSheet()
    return {
        "body": ParagraphStyle(
            "Body",
            parent=sample["BodyText"],
            fontName="DocCJK",
            fontSize=9.5,
            leading=15,
            textColor=colors.HexColor(THEME_BODY),
            spaceAfter=5,
            wordWrap="CJK",
        ),
        "cover_product": ParagraphStyle(
            "CoverProduct",
            fontName="DocCJKBold",
            fontSize=25,
            leading=34,
            alignment=TA_CENTER,
            textColor=colors.HexColor(THEME_DARK),
            wordWrap="CJK",
        ),
        "cover_type": ParagraphStyle(
            "CoverType",
            fontName="DocCJK",
            fontSize=17,
            leading=24,
            alignment=TA_CENTER,
            textColor=colors.HexColor(THEME_MUTED),
        ),
        "cover_model": ParagraphStyle(
            "CoverModel",
            fontName="DocCJKBold",
            fontSize=10.5,
            leading=18,
            alignment=TA_CENTER,
            textColor=colors.HexColor(THEME_PRIMARY),
        ),
        "cover_meta": ParagraphStyle(
            "CoverMeta",
            fontName="DocCJK",
            fontSize=10.5,
            leading=18,
            alignment=TA_CENTER,
            textColor=colors.HexColor(THEME_MUTED),
        ),
        "toc_title": ParagraphStyle(
            "TOCTitle",
            fontName="DocCJKBold",
            fontSize=22,
            leading=28,
            textColor=colors.HexColor(THEME_DARK),
            spaceAfter=14,
        ),
        "part": ParagraphStyle(
            "PartHeading",
            fontName="DocCJKBold",
            fontSize=20,
            leading=28,
            textColor=colors.HexColor(THEME_PRIMARY),
            spaceBefore=4,
            spaceAfter=16,
            keepWithNext=True,
            wordWrap="CJK",
        ),
        "h2": ParagraphStyle(
            "Heading2",
            fontName="DocCJKBold",
            fontSize=15,
            leading=21,
            textColor=colors.HexColor(THEME_PRIMARY),
            spaceBefore=12,
            spaceAfter=7,
            keepWithNext=True,
            wordWrap="CJK",
        ),
        "h3": ParagraphStyle(
            "Heading3",
            fontName="DocCJKBold",
            fontSize=11.5,
            leading=17,
            textColor=colors.HexColor(THEME_PRIMARY),
            spaceBefore=9,
            spaceAfter=5,
            keepWithNext=True,
            wordWrap="CJK",
        ),
        "h4": ParagraphStyle(
            "Heading4",
            fontName="DocCJKBold",
            fontSize=10,
            leading=15,
            textColor=colors.HexColor(THEME_DARK),
            spaceBefore=7,
            spaceAfter=4,
            keepWithNext=True,
            wordWrap="CJK",
        ),
        "h5": ParagraphStyle(
            "Heading5",
            fontName="DocCJKBold",
            fontSize=9,
            leading=14,
            textColor=colors.HexColor(THEME_MUTED),
            spaceBefore=6,
            spaceAfter=3,
            keepWithNext=True,
            wordWrap="CJK",
        ),
        "table": ParagraphStyle(
            "TableText",
            fontName="DocCJK",
            fontSize=7.4,
            leading=10.2,
            textColor=colors.HexColor(THEME_BODY),
            wordWrap="CJK",
        ),
        "table_header": ParagraphStyle(
            "TableHeader",
            fontName="DocCJKBold",
            fontSize=7.4,
            leading=10.2,
            textColor=colors.white,
            wordWrap="CJK",
        ),
        "note": ParagraphStyle(
            "Note",
            fontName="DocCJK",
            fontSize=8.6,
            leading=13.5,
            textColor=colors.HexColor("#334155"),
            wordWrap="CJK",
        ),
        "code": ParagraphStyle(
            "Code",
            fontName="DocCJK",
            fontSize=7.8,
            leading=11.5,
            leftIndent=6,
            rightIndent=6,
            textColor=colors.HexColor("#334155"),
        ),
        "caption": ParagraphStyle(
            "Caption",
            fontName="DocCJK",
            fontSize=8,
            leading=11,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#64748B"),
            spaceBefore=3,
            spaceAfter=8,
        ),
    }


class HeadingParagraph(Paragraph):
    def __init__(
        self,
        text: str,
        style: ParagraphStyle,
        toc_level: int | None,
        bookmark: str,
    ) -> None:
        super().__init__(f'<a name="{bookmark}"/>{html.escape(text)}', style)
        self.heading_text = text
        self.toc_level = toc_level
        self.bookmark = bookmark


class ClickableTableOfContents(TableOfContents):
    """Table of contents whose full entry rows are clickable."""

    def wrap(self, availWidth: float, availHeight: float) -> tuple[float, float]:
        size = super().wrap(availWidth, availHeight)
        entry_keys = iter(key for _, _, _, key in self._lastEntries)
        for row in self._table._cellvalues:
            cell = row[0]
            flowables = cell if isinstance(cell, (list, tuple)) else (cell,)
            for flowable in flowables:
                if isinstance(flowable, Paragraph):
                    flowable.__class__ = ClickableTOCParagraph
                    flowable.toc_bookmark = next(entry_keys, None)
        return size


class ClickableTOCParagraph(Paragraph):
    """Add one internal link annotation over the complete TOC row."""

    toc_bookmark: str | None = None

    def drawOn(self, canvas, x, y, _sW=0) -> None:
        super().drawOn(canvas, x, y, _sW)
        if self.toc_bookmark:
            canvas.linkRect(
                "",
                self.toc_bookmark,
                (x, y, x + self.width, y + self.height),
                relative=1,
                thickness=0,
            )


class ThemedPDFDocTemplate(BaseDocTemplate):
    def __init__(self, filename: str, title: str) -> None:
        super().__init__(
            filename,
            pagesize=A4,
            rightMargin=21 * mm,
            leftMargin=21 * mm,
            topMargin=20 * mm,
            bottomMargin=18 * mm,
            title=title,
            author="Mixed Signal Lab",
            subject="SmartUSBHub Product Documentation",
        )
        frame = Frame(
            self.leftMargin,
            self.bottomMargin,
            self.width,
            self.height,
            id="content",
        )
        self.addPageTemplates(
            [PageTemplate(id="manual", frames=[frame], onPage=self._draw_header_footer)]
        )

    def _draw_header_footer(self, canvas, _doc) -> None:
        page = canvas.getPageNumber()
        if page == 1:
            return
        canvas.saveState()
        canvas.setStrokeColor(colors.HexColor(THEME_LINE))
        canvas.setLineWidth(0.5)
        canvas.line(self.leftMargin, A4[1] - 14 * mm, A4[0] - self.rightMargin, A4[1] - 14 * mm)
        canvas.setFont("DocCJK", 8)
        canvas.setFillColor(colors.HexColor(THEME_MUTED))
        canvas.drawString(self.leftMargin, A4[1] - 10.5 * mm, WEBSITE_LABEL)
        label_width = pdfmetrics.stringWidth(WEBSITE_LABEL, "DocCJK", 8)
        canvas.linkURL(
            WEBSITE_URL,
            (
                self.leftMargin,
                A4[1] - 12 * mm,
                self.leftMargin + label_width,
                A4[1] - 8.5 * mm,
            ),
            relative=0,
        )
        canvas.line(self.leftMargin, 12 * mm, A4[0] - self.rightMargin, 12 * mm)
        canvas.drawRightString(A4[0] - self.rightMargin, 7.5 * mm, str(page - 1))
        canvas.restoreState()

    def afterFlowable(self, flowable: Flowable) -> None:
        if not isinstance(flowable, HeadingParagraph):
            return
        key = flowable.bookmark
        self.canv.bookmarkPage(key)
        if flowable.toc_level is None:
            return
        self.canv.addOutlineEntry(
            flowable.heading_text,
            key,
            level=flowable.toc_level,
            closed=flowable.toc_level == 0,
        )
        self.notify(
            "TOCEntry",
            (
                flowable.toc_level,
                flowable.heading_text,
                self.page - 1,
                key,
            ),
        )


def slugify(text: str, prefix: str, index: int) -> str:
    ascii_slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return f"{prefix}-{ascii_slug or 'section'}-{index}"


def resolve_link(raw_url: str, source: Path) -> str:
    url = raw_url.strip()
    if url.startswith("#"):
        anchor = url[1:]
        return "#" + LOCAL_ANCHORS.get((str(source.resolve()), anchor), anchor)
    if url.startswith(("http://", "https://", "mailto:")):
        return url
    clean = url.split("#", 1)[0]
    try:
        target = (source.parent / clean).resolve().relative_to(ROOT)
        return GITHUB_BASE + quote(target.as_posix(), safe="/")
    except ValueError:
        return GITHUB_BASE


def inline_markup(text: str, source: Path) -> str:
    placeholders: dict[str, str] = {}

    def keep(fragment: str) -> str:
        token = f"@@INLINE{len(placeholders)}@@"
        placeholders[token] = fragment
        return token

    def image_alt(match: re.Match[str]) -> str:
        return keep(html.escape(match.group(1)))

    text = re.sub(r"!\[([^]]*)\]\([^)]+\)", image_alt, text)

    def link(match: re.Match[str]) -> str:
        label = html.escape(match.group(1))
        href = html.escape(resolve_link(match.group(2), source), quote=True)
        return keep(f'<link href="{href}" color="#1769AA"><u>{label}</u></link>')

    text = re.sub(r"\[([^]]+)\]\(([^)]+)\)", link, text)
    text = html.escape(text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"(?<!\*)\*(.+?)\*(?!\*)", r"<i>\1</i>", text)
    text = re.sub(
        r"`([^`]+)`",
        r'<font name="DocCJK" color="#7C3AED">\1</font>',
        text,
    )
    text = text.replace("&lt;u&gt;", "<u>").replace("&lt;/u&gt;", "</u>")
    for token, fragment in placeholders.items():
        text = text.replace(token, fragment)
    return text


def display_units(value: str) -> int:
    return sum(2 if ord(char) > 127 else 1 for char in re.sub(r"<[^>]+>", "", value))


class MarkdownRenderer:
    def __init__(
        self,
        styles: dict[str, ParagraphStyle],
        max_width: float,
        language: str = "zh",
    ) -> None:
        self.styles = styles
        self.max_width = max_width
        self.language = language
        self.heading_index = 0

    def render(self, source: Path, prefix: str) -> list[Flowable]:
        lines = source.read_text(encoding="utf-8").splitlines()
        upcoming_index = self.heading_index
        for candidate in lines:
            heading_match = re.match(r"^(#{2,5})\s+(.+?)\s*$", candidate.strip())
            if not heading_match:
                continue
            upcoming_index += 1
            heading_title = re.sub(r"\*\*", "", heading_match.group(2)).rstrip("：:")
            markdown_anchor = re.sub(r"[\s]+", "-", heading_title.strip().lower())
            markdown_anchor = re.sub(r"[^\w\-\u4e00-\u9fff]", "", markdown_anchor)
            LOCAL_ANCHORS[(str(source.resolve()), markdown_anchor)] = slugify(
                heading_title, prefix, upcoming_index
            )
        flowables: list[Flowable] = []
        i = 0
        skipped_h1 = False
        seen_section = False
        while i < len(lines):
            raw = lines[i]
            stripped = raw.strip()
            if not stripped:
                i += 1
                continue
            if stripped.startswith("# ") and not skipped_h1:
                skipped_h1 = True
                i += 1
                continue
            if not seen_section and re.fullmatch(
                r"\[[^]]+\]\([^)]*\.(?:md|pdf)\)",
                stripped,
                flags=re.IGNORECASE,
            ):
                i += 1
                continue
            heading = re.match(r"^(#{2,5})\s+(.+?)\s*$", stripped)
            if heading:
                seen_section = True
                markdown_level = len(heading.group(1))
                toc_level = markdown_level - 2 if markdown_level <= 3 else None
                title = re.sub(r"\*\*", "", heading.group(2)).rstrip("：:")
                self.heading_index += 1
                style_name = {2: "h2", 3: "h3", 4: "h4", 5: "h5"}[markdown_level]
                flowables.append(
                    HeadingParagraph(
                        title,
                        self.styles[style_name],
                        toc_level,
                        slugify(title, prefix, self.heading_index),
                    )
                )
                i += 1
                continue
            if re.match(r"^[-_]{5,}$", stripped):
                flowables.extend(
                    [Spacer(1, 3), HRFlowable(width="100%", color=colors.HexColor(THEME_LINE)), Spacer(1, 4)]
                )
                i += 1
                continue
            if stripped.startswith("```"):
                language = stripped[3:].strip().lower()
                code: list[str] = []
                i += 1
                while i < len(lines) and not lines[i].strip().startswith("```"):
                    code.append(lines[i])
                    i += 1
                i += 1
                if language == "mermaid":
                    flowables.extend(self._render_mermaid(code, source))
                    continue
                box = Table(
                    [[Preformatted("\n".join(code), self.styles["code"])]],
                    colWidths=[self.max_width],
                )
                box.setStyle(
                    TableStyle(
                        [
                            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F3F6FA")),
                            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor(THEME_LINE)),
                            ("LEFTPADDING", (0, 0), (-1, -1), 7),
                            ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                            ("TOPPADDING", (0, 0), (-1, -1), 6),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                        ]
                    )
                )
                flowables.extend([box, Spacer(1, 5)])
                continue
            if self._is_image(stripped):
                image_flowables = self._render_image(stripped, source)
                flowables.extend(image_flowables)
                i += 1
                continue
            if self._is_table_start(lines, i):
                table_lines: list[str] = []
                while i < len(lines) and lines[i].strip().startswith("|"):
                    table_lines.append(lines[i].strip())
                    i += 1
                flowables.extend(self._render_table(table_lines, source))
                continue
            if stripped.startswith(":::{admonition}"):
                title = stripped.removeprefix(":::{admonition}").strip()
                directive_class = ""
                directive_lines: list[str] = []
                i += 1
                while i < len(lines) and lines[i].strip() != ":::":
                    value = lines[i].strip()
                    if value.startswith(":class:"):
                        directive_class = value.removeprefix(":class:").strip().lower()
                    else:
                        directive_lines.append(value)
                    i += 1
                if i < len(lines):
                    i += 1
                admonition = {
                    "warning": "WARNING" if self.language == "en" else "警告",
                    "important": "CAUTION" if self.language == "en" else "小心",
                    "caution": "CAUTION" if self.language == "en" else "小心",
                    "tip": "EXPECTED RESULT" if self.language == "en" else "正常结果",
                    "success": "EXPECTED RESULT" if self.language == "en" else "正常结果",
                }.get(
                    directive_class,
                    "NOTE" if self.language == "en" else "提示",
                )
                if title:
                    directive_lines.insert(0, title + ".")
                flowables.extend(
                    self._render_admonition_box(
                        directive_lines, source, admonition
                    )
                )
                continue
            if stripped.startswith(">"):
                quote_lines: list[str] = []
                admonition = ""
                while i < len(lines) and (lines[i].strip().startswith(">") or not lines[i].strip()):
                    value = lines[i].strip()
                    if value.startswith(">"):
                        value = value[1:].strip()
                    if value == "[!WARNING]":
                        admonition = "WARNING" if self.language == "en" else "警告"
                    elif value == "[!IMPORTANT]":
                        admonition = "CAUTION" if self.language == "en" else "小心"
                    elif value == "[!NOTE]":
                        admonition = "NOTE" if self.language == "en" else "提示"
                    elif value == "[!TIP]":
                        admonition = "EXPECTED RESULT" if self.language == "en" else "正常结果"
                    else:
                        quote_lines.append(value)
                    i += 1
                if quote_lines:
                    flowables.extend(
                        self._render_admonition_box(
                            quote_lines, source, admonition
                        )
                    )
                continue
            if re.match(r"^\s*[-*]\s+", raw) or re.match(r"^\s*\d+\.\s+", raw):
                items: list[ListItem] = []
                ordered = bool(re.match(r"^\s*\d+\.\s+", raw))
                pattern = r"^\s*\d+\.\s+" if ordered else r"^\s*[-*]\s+"
                while i < len(lines) and re.match(pattern, lines[i]):
                    item_text = re.sub(pattern, "", lines[i]).strip()
                    items.append(
                        ListItem(
                            Paragraph(inline_markup(item_text, source), self.styles["body"]),
                            leftIndent=11,
                        )
                    )
                    i += 1
                flowables.append(
                    ListFlowable(
                        items,
                        bulletType="1" if ordered else "bullet",
                        start="1" if ordered else "•",
                        leftIndent=16,
                        bulletFontName="DocCJK",
                        bulletFontSize=8,
                        spaceAfter=4,
                    )
                )
                continue

            paragraph_lines = [stripped]
            i += 1
            while i < len(lines) and lines[i].strip() and not self._starts_block(lines, i):
                paragraph_lines.append(lines[i].strip())
                i += 1
            paragraph = " ".join(paragraph_lines)
            flowables.append(Paragraph(inline_markup(paragraph, source), self.styles["body"]))
        return flowables

    @staticmethod
    def _is_table_start(lines: list[str], index: int) -> bool:
        if index + 1 >= len(lines) or not lines[index].strip().startswith("|"):
            return False
        return bool(re.match(r"^\|?\s*:?-{3,}", lines[index + 1].strip())) or "---" in lines[index + 1]

    @staticmethod
    def _is_image(text: str) -> bool:
        return bool(re.match(r"^!\[[^]]*\]\([^)]+\)$", text)) or text.startswith("<img ")

    def _starts_block(self, lines: list[str], index: int) -> bool:
        value = lines[index].strip()
        return bool(
            re.match(r"^#{1,5}\s+", value)
            or re.match(r"^\s*[-*]\s+", lines[index])
            or re.match(r"^\s*\d+\.\s+", lines[index])
            or value.startswith((">", "```", "|", ":::"))
            or self._is_image(value)
            or re.match(r"^[-_]{5,}$", value)
        )

    def _render_admonition_box(
        self,
        lines: list[str],
        source: Path,
        admonition: str,
    ) -> list[Flowable]:
        if admonition in ("警告", "WARNING"):
            background = THEME_WARNING_PALE
            accent = THEME_WARNING
            title_color = THEME_WARNING
            icon_name = "icon-warning-white.png"
        elif admonition in ("小心", "CAUTION"):
            background = THEME_CAUTION_PALE
            accent = THEME_CAUTION
            title_color = THEME_DARK
            icon_name = "icon-warning-dark.png"
        elif admonition in ("正常结果", "EXPECTED RESULT"):
            background = THEME_SUCCESS_PALE
            accent = THEME_SUCCESS
            title_color = THEME_SUCCESS
            icon_name = "icon-check-white.png"
        else:
            background = THEME_PALE
            accent = THEME_PRIMARY
            title_color = THEME_DARK
            icon_name = "icon-info-white.png"
            admonition = admonition or ("NOTE" if self.language == "en" else "提示")
        note_content = self._render_quote_content(
            lines, source, admonition, title_color
        )
        icon = Image(
            str(CALLOUT_ASSET_DIR / icon_name),
            width=7 * mm,
            height=7 * mm,
        )
        band_width = 15.5 * mm
        box = Table(
            [[icon, note_content]],
            colWidths=[band_width, self.max_width - band_width],
            hAlign="LEFT",
        )
        box.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (0, 0), colors.HexColor(accent)),
                    ("BACKGROUND", (1, 0), (1, 0), colors.HexColor(background)),
                    ("BOX", (0, 0), (-1, -1), 0.55, colors.HexColor("#6B7280")),
                    ("LINEAFTER", (0, 0), (0, 0), 0.55, colors.HexColor("#6B7280")),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("ALIGN", (0, 0), (0, 0), "CENTER"),
                    ("LEFTPADDING", (0, 0), (0, 0), 4),
                    ("RIGHTPADDING", (0, 0), (0, 0), 4),
                    ("TOPPADDING", (0, 0), (0, 0), 10),
                    ("BOTTOMPADDING", (0, 0), (0, 0), 10),
                    ("LEFTPADDING", (1, 0), (1, 0), 9),
                    ("RIGHTPADDING", (1, 0), (1, 0), 9),
                    ("TOPPADDING", (1, 0), (1, 0), 7),
                    ("BOTTOMPADDING", (1, 0), (1, 0), 7),
                ]
            )
        )
        return [box, Spacer(1, 5)]

    def _render_quote_content(
        self,
        lines: list[str],
        source: Path,
        admonition: str,
        title_color: str,
    ) -> list[Flowable]:
        content: list[Flowable] = []
        lines = list(lines)
        if admonition:
            title = ""
            for index, value in enumerate(lines):
                value = value.strip()
                if not value or value.startswith(("```", "-", "*")):
                    continue
                # Do not treat decimal points (for example, "2.1 A") as
                # sentence boundaries when deriving the callout title.
                match = re.match(
                    r"^(.+?)(?:[。！？!?]|(?<!\d)\.(?!\d))(?:\s*(.*))?$",
                    value,
                )
                if match:
                    title = match.group(1).strip()
                    remainder = (match.group(2) or "").strip()
                    lines[index] = remainder
                break
            heading = html.escape(admonition)
            if title:
                heading += "：" + inline_markup(title, source)
            content.append(
                Paragraph(
                    f'<b><font color="{title_color}">{heading}</font></b>',
                    self.styles["note"],
                )
            )
        i = 0
        while i < len(lines):
            value = lines[i].strip()
            if not value:
                content.append(Spacer(1, 3))
                i += 1
                continue
            if value.startswith("```"):
                code: list[str] = []
                i += 1
                while i < len(lines) and not lines[i].strip().startswith("```"):
                    code.append(lines[i])
                    i += 1
                i += 1
                content.append(Preformatted("\n".join(code), self.styles["code"]))
                continue
            list_match = re.match(r"^([-*]|\d+\.)\s+(.+)$", value)
            if list_match:
                ordered = list_match.group(1)[0].isdigit()
                items: list[ListItem] = []
                while i < len(lines):
                    item_match = re.match(r"^([-*]|\d+\.)\s+(.+)$", lines[i].strip())
                    if not item_match or item_match.group(1)[0].isdigit() != ordered:
                        break
                    items.append(
                        ListItem(
                            Paragraph(
                                inline_markup(item_match.group(2), source),
                                self.styles["note"],
                            ),
                            leftIndent=6 if ordered else 0,
                        )
                    )
                    i += 1
                content.append(
                    ListFlowable(
                        items,
                        bulletType="1" if ordered else "bullet",
                        start="1" if ordered else "•",
                        leftIndent=12,
                        bulletColor=colors.HexColor(THEME_PRIMARY),
                        bulletFontName="DocCJK",
                        bulletFontSize=8 if ordered else 7,
                        bulletOffsetY=0 if ordered else 1.5,
                        bulletDedent=4,
                        bulletFormat="%s." if ordered else None,
                        spaceAfter=2,
                    )
                )
                continue
            paragraph_lines = [value]
            i += 1
            while i < len(lines):
                next_value = lines[i].strip()
                if (
                    not next_value
                    or next_value.startswith("```")
                    or re.match(r"^([-*]|\d+\.)\s+", next_value)
                ):
                    break
                paragraph_lines.append(next_value)
                i += 1
            content.append(
                Paragraph(
                    inline_markup(" ".join(paragraph_lines), source),
                    self.styles["note"],
                )
            )
        return content

    def _render_mermaid(self, lines: list[str], source: Path) -> list[Flowable]:
        meaningful = [line.strip() for line in lines if line.strip()]
        if not meaningful or meaningful[0] != "packet-beta":
            fallback = Preformatted("\n".join(lines), self.styles["code"])
            return [fallback, Spacer(1, 5)]
        fields: list[tuple[int, int, str]] = []
        for line in meaningful[1:]:
            match = re.match(r'(\d+)-(\d+):\s*"(.*)"$', line)
            if match:
                fields.append((int(match.group(1)), int(match.group(2)), match.group(3)))
        if not fields:
            return []
        weights = [
            max(end - start + 1, min(22, max(8, display_units(label))))
            for start, end, label in fields
        ]
        total = sum(weights)
        widths = [self.max_width * weight / total for weight in weights]
        labels = [
            Paragraph(inline_markup(label, source), self.styles["table_header"])
            for _, _, label in fields
        ]
        ranges = [
            Paragraph(
                f"bit {start}" if start == end else f"bit {start}-{end}",
                self.styles["table"],
            )
            for start, end, _ in fields
        ]
        diagram = Table([labels, ranges], colWidths=widths, hAlign="LEFT")
        diagram.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(THEME_PRIMARY)),
                    ("BACKGROUND", (0, 1), (-1, 1), colors.HexColor(THEME_PALE)),
                    ("GRID", (0, 0), (-1, -1), 0.7, colors.HexColor(THEME_PRIMARY)),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 3),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                    ("TOPPADDING", (0, 0), (-1, -1), 7),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                ]
            )
        )
        return [
            Spacer(1, 4),
            diagram,
            Paragraph(
                "Protocol frame bit layout"
                if self.language == "en"
                else "协议帧位布局",
                self.styles["caption"],
            ),
        ]

    def _render_image(self, line: str, source: Path) -> list[Flowable]:
        markdown_match = re.match(r"^!\[([^]]*)\]\(([^)]+)\)$", line)
        if markdown_match:
            alt, raw_path = markdown_match.groups()
        else:
            src_match = re.search(r'src=["\']([^"\']+)["\']', line)
            alt_match = re.search(r'alt=["\']([^"\']*)["\']', line)
            if not src_match:
                return []
            raw_path = src_match.group(1)
            alt = alt_match.group(1) if alt_match else ""
        if re.fullmatch(
            r"(?i)(?:image[-_].*|sc\d+|device[-_]overview(?:[-_]en)?|connection[-_]guide(?:[-_]cn)?)",
            alt.strip(),
        ):
            alt = ""
        if raw_path.startswith(("http://", "https://")):
            label = "Image" if self.language == "en" else "图片"
            return [Paragraph(f"{label}: {html.escape(alt)}", self.styles["caption"])]
        image_path = (source.parent / unquote(raw_path)).resolve()
        if not image_path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")
        raster_fallback = image_path.with_suffix(".png")
        if image_path.suffix.lower() == ".svg" and raster_fallback.exists():
            image_path = raster_fallback
        max_height = 115 * mm
        if image_path.suffix.lower() == ".svg":
            svg_text = image_path.read_text(encoding="utf-8")
            svg_text = re.sub(
                r"font-family\s*:\s*[^;}]+",
                "font-family:DocCJK",
                svg_text,
            )
            drawing = svg2rlg(io.BytesIO(svg_text.encode("utf-8")))
            if drawing is None:
                raise RuntimeError(f"Unable to render SVG: {image_path}")
            scale = min(self.max_width / drawing.width, max_height / drawing.height, 1.0)
            drawing.width *= scale
            drawing.height *= scale
            drawing.scale(scale, scale)
            visual: Flowable = drawing
        else:
            with PILImage.open(image_path) as raster:
                width, height = raster.size
            scale = min(self.max_width / width, max_height / height, 1.0)
            visual = Image(str(image_path), width=width * scale, height=height * scale)
        result: list[Flowable] = [Spacer(1, 4), visual]
        if alt:
            result.append(Paragraph(html.escape(alt), self.styles["caption"]))
        else:
            result.append(Spacer(1, 6))
        return result

    def _render_table(self, lines: list[str], source: Path) -> list[Flowable]:
        raw_rows = [[cell.strip() for cell in line.strip("|").split("|")] for line in lines]
        if len(raw_rows) > 1 and all(re.match(r"^:?-{3,}:?$", cell) for cell in raw_rows[1]):
            del raw_rows[1]
        column_count = max(len(row) for row in raw_rows)
        for row in raw_rows:
            row.extend([""] * (column_count - len(row)))
        maxima = [
            max(6, min(34, max(display_units(row[col]) for row in raw_rows)))
            for col in range(column_count)
        ]
        total = sum(maxima)
        widths = [self.max_width * value / total for value in maxima]
        rows: list[list[Paragraph]] = []
        for row_index, row in enumerate(raw_rows):
            style = self.styles["table_header" if row_index == 0 else "table"]
            rows.append([Paragraph(inline_markup(cell, source), style) for cell in row])
        table = Table(rows, colWidths=widths, repeatRows=1, hAlign="LEFT")
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(THEME_DARK)),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F3F5F7")]),
                    ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor(THEME_LINE)),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 4),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]
            )
        )
        return [table, Spacer(1, 7)]


def make_toc(styles: dict[str, ParagraphStyle]) -> TableOfContents:
    toc = ClickableTableOfContents()
    toc.dotsMinLevel = 0
    toc.levelStyles = [
        ParagraphStyle(
            "TOCPart",
            fontName="DocCJKBold",
            fontSize=11,
            leading=17,
            leftIndent=0,
            firstLineIndent=0,
            textColor=colors.HexColor(THEME_DARK),
            spaceBefore=5,
        ),
        ParagraphStyle(
            "TOCSection",
            fontName="DocCJK",
            fontSize=9.3,
            leading=14,
            leftIndent=12,
            firstLineIndent=0,
            textColor=colors.HexColor("#334155"),
        ),
        ParagraphStyle(
            "TOCSubsection",
            fontName="DocCJK",
            fontSize=8.3,
            leading=12,
            leftIndent=25,
            firstLineIndent=0,
            textColor=colors.HexColor("#64748B"),
        ),
    ]
    return toc


def count_outline_entries(items: list) -> int:
    return sum(
        count_outline_entries(item) if isinstance(item, list) else 1
        for item in items
    )


def validate_toc_links(reader: PdfReader, output: Path) -> None:
    expected = count_outline_entries(reader.outline)
    full_row_links = 0
    for page in reader.pages:
        for annotation_ref in page.get("/Annots", []):
            annotation = annotation_ref.get_object()
            if not annotation.get("/Dest"):
                continue
            rect = annotation.get("/Rect")
            if rect and float(rect[2]) - float(rect[0]) >= 0.75 * A4[0]:
                full_row_links += 1
    if full_row_links < expected:
        raise RuntimeError(
            f"TOC links are incomplete in {output}: "
            f"expected {expected} full-row links, found {full_row_links}"
        )


def build_document(document_key: str) -> Path:
    config = DOCUMENTS[document_key]
    output = OUTPUT_DIR / config["output"]
    styles = make_styles()
    doc = ThemedPDFDocTemplate(
        str(output), f'{config["title"]} {config["document_type"]}'
    )
    language = config.get("language", "zh")
    renderer = MarkdownRenderer(styles, doc.width, language)
    applies_to = "Applies to" if language == "en" else "适用于"
    release_label = "Released v1.0" if language == "en" else "正式版 v1.0"
    contents_label = "Contents" if language == "en" else "目录"

    story: list[Flowable] = [
        Spacer(1, 38 * mm),
        Paragraph(config["title"], styles["cover_product"]),
        Spacer(1, 8 * mm),
        HRFlowable(width="38%", thickness=1.2, color=colors.HexColor(THEME_PRIMARY)),
        Spacer(1, 8 * mm),
        Paragraph(config["document_type"], styles["cover_type"]),
        Spacer(1, 10 * mm),
        Paragraph(f'{applies_to}: {config["model"]}', styles["cover_model"]),
        Paragraph(release_label, styles["cover_meta"]),
        Spacer(1, 32 * mm),
        Paragraph(
            f'<link href="{WEBSITE_URL}" color="{THEME_PRIMARY}"><u>{WEBSITE_LABEL}</u></link>',
            styles["cover_meta"],
        ),
        PageBreak(),
        Paragraph(contents_label, styles["toc_title"]),
        make_toc(styles),
        PageBreak(),
    ]
    story.extend(renderer.render(ROOT / config["source"], document_key))
    doc.multiBuild(story)

    reader = PdfReader(str(output))
    if len(reader.pages) < 3:
        raise RuntimeError(f"Generated PDF is unexpectedly short: {output}")
    if not reader.outline:
        raise RuntimeError(f"Generated PDF has no bookmarks: {output}")
    validate_toc_links(reader, output)
    return output


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build separate themed SmartUSBHub PDFs from Markdown."
    )
    parser.add_argument(
        "--product",
        choices=["all", "usb2_4p", "usb2_7p", "protocol", *DOCUMENTS.keys()],
        default="all",
        help="Product or document to build (default: all).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    register_fonts()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    if args.product == "all":
        document_keys = list(DOCUMENTS)
    elif args.product in ("usb2_4p", "usb2_7p"):
        document_keys = [
            key
            for key, config in DOCUMENTS.items()
            if config["product"] == args.product
        ] + ["protocol"]
    elif args.product == "protocol":
        document_keys = ["protocol", "protocol_en"]
    else:
        document_keys = [args.product]
    outputs = [build_document(document_key) for document_key in document_keys]
    for output in outputs:
        print(output.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
