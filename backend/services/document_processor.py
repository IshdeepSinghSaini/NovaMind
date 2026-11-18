"""
document_processor.py - Read PDF, DOCX and TXT files into one common structure.

Every format becomes the same thing:

    ExtractedDocument
        title     : "Annual Leave Policy"
        metadata  : {"doc_code": "HR-002", "version": "2.1", ...}   (from the header block)
        sections  : [Section(heading="5. Sick Leave",
                             blocks=[Block(kind="paragraph", text="...", page=1),
                                     Block(kind="bullet",    text="...", page=1)])]

Steps for every format:
1. Read lines/paragraphs with their structure (headings, bullets, page numbers).
2. Pull out the metadata header lines ("Document ID: HR-002", ...) and remove them.
3. Remove boilerplate (repeated footers, disclaimers).
4. Clean the text (spaces, special characters).
5. Group everything into sections by heading.
"""

import re
import unicodedata
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


class ExtractionError(Exception):
    """The file could not be read. The message is safe to show to an admin."""


# ------------------------------------------------------------- data shapes --

@dataclass
class Block:
    kind: str                    # "paragraph" or "bullet"
    text: str
    page: Optional[int] = None   # PDFs only


@dataclass
class Section:
    heading: Optional[str]
    blocks: list = field(default_factory=list)


@dataclass
class ExtractedDocument:
    file_type: str
    title: Optional[str]
    metadata: dict
    sections: list
    page_count: Optional[int] = None

    @property
    def text_length(self):
        return sum(len(b.text) for s in self.sections for b in s.blocks)


# ----------------------------------------------------------------- cleaning --

_CHAR_FIXES = {
    " ": " ", " ": " ", "​": "",            # odd spaces
    "‘": "'", "’": "'", "“": '"', "”": '"',  # curly quotes
    "–": "-", "—": "-", "−": "-",            # dashes
    "…": "...",
}


def clean_text(text: str) -> str:
    """Normalise characters and spaces so the same words always look the same."""
    if not text:
        return ""
    text = unicodedata.normalize("NFKC", text)
    for bad, good in _CHAR_FIXES.items():
        text = text.replace(bad, good)
    # remove invisible control characters (keep normal text only)
    text = "".join(ch for ch in text if ch in "\n\t" or unicodedata.category(ch)[0] != "C")
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


# ------------------------------------------------- metadata and boilerplate --

_META_FIELDS = {
    "document id": "doc_code",
    "company": "company",
    "department": "department",
    "document type": "document_type",
    "version": "version",
    "created": "created",
    "access level": "access_level",
}
_META_RE = re.compile(r"^\s*(" + "|".join(_META_FIELDS) + r")\s*:\s*(.+?)\s*$", re.IGNORECASE)

# Text that appears in documents but never answers a question (disclaimers, page numbers)
_BOILERPLATE_RE = [
    re.compile(r"^synthetic document created for testing\b", re.IGNORECASE),
    re.compile(r"^page \d+( of \d+)?$", re.IGNORECASE),
]

_BULLET_RE = re.compile(r"^\s*(?:[-*•●▪]|\d+[.)])\s+")


def _try_metadata(line, metadata):
    """If the line is a header line like 'Version: 2.1', store it and return True."""
    match = _META_RE.match(line)
    if not match:
        return False
    key = _META_FIELDS[match.group(1).lower()]
    metadata.setdefault(key, match.group(2))
    return True


def _is_boilerplate(text):
    return any(p.match(text) for p in _BOILERPLATE_RE)


def _build_sections(items):
    """
    items: list of ("heading" | "paragraph" | "bullet", text, page)
    Returns a list of Section objects (empty sections are dropped).
    """
    sections = [Section(heading=None)]
    for kind, text, page in items:
        text = clean_text(text)
        if not text or _is_boilerplate(text):
            continue
        if kind == "heading":
            sections.append(Section(heading=text))
        else:
            sections[-1].blocks.append(Block(kind=kind, text=text, page=page))
    return [s for s in sections if s.blocks]


# ---------------------------------------------------------------------- TXT --

def _read_text_file(path):
    raw = Path(path).read_bytes()
    for encoding in ("utf-8-sig", "cp1252"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise ExtractionError("The text file could not be decoded.")


def extract_txt(path):
    lines = _read_text_file(path).splitlines()
    metadata, items, title = {}, [], None
    paragraph, para_kind = [], "paragraph"

    def flush():
        nonlocal paragraph, para_kind
        if paragraph:
            items.append((para_kind, " ".join(paragraph), None))
        paragraph, para_kind = [], "paragraph"

    i = 0
    while i < len(lines):
        line = lines[i].strip()
        nxt = lines[i + 1].strip() if i + 1 < len(lines) else ""

        if not line:
            flush()
        elif re.fullmatch(r"=+", nxt) and title is None:          # Title\n=====
            flush(); title = line; i += 1
        elif re.fullmatch(r"-{3,}", nxt):                          # Heading\n-------
            flush(); items.append(("heading", line, None)); i += 1
        elif line.startswith("#"):                                 # # Markdown heading
            flush(); items.append(("heading", line.lstrip("#").strip(), None))
        elif _try_metadata(line, metadata):
            flush()
        elif _BULLET_RE.match(line):
            flush(); para_kind = "bullet"; paragraph = [_BULLET_RE.sub("", line, count=1)]
        else:
            paragraph.append(line)
        i += 1
    flush()

    if title is None and items and items[0][0] == "paragraph" and len(items[0][1]) < 120:
        title = items.pop(0)[1]
    return ExtractedDocument("txt", clean_text(title) or None, metadata, _build_sections(items))


# --------------------------------------------------------------------- DOCX --

def extract_docx(path):
    from docx import Document as DocxDocument

    try:
        d = DocxDocument(str(path))
    except Exception as error:
        raise ExtractionError(f"The Word document could not be opened ({type(error).__name__}).")

    metadata, items, title = {}, [], None
    for para in d.paragraphs:
        text = para.text.strip()
        if not text:
            continue
        style = (para.style.name or "").lower() if para.style is not None else ""
        if style == "title" and title is None:
            title = text
        elif style.startswith("heading"):
            items.append(("heading", text, None))
        elif _try_metadata(text, metadata):
            continue
        elif "list" in style or _BULLET_RE.match(text):
            items.append(("bullet", _BULLET_RE.sub("", text, count=1), None))
        else:
            items.append(("paragraph", text, None))

    # Text inside tables is read too (row by row), so it is not lost
    for table in d.tables:
        for row in table.rows:
            cells = [c.text.strip() for c in row.cells if c.text.strip()]
            if cells:
                items.append(("paragraph", " | ".join(dict.fromkeys(cells)), None))

    if title is None:
        title = (d.core_properties.title or "").strip() or None
    return ExtractedDocument("docx", clean_text(title) if title else None, metadata, _build_sections(items))


# ---------------------------------------------------------------------- PDF --

_PDF_EDGE_MARGIN = 45  # points; text this close to the top/bottom edge is header/footer


def _pdf_lines(doc):
    """Every text line with its page, font size, position and boldness."""
    lines = []
    for page_no, page in enumerate(doc, start=1):
        height = page.rect.height
        page_lines = []
        for block in page.get_text("dict")["blocks"]:
            if block.get("type") != 0:
                continue
            for line in block["lines"]:
                spans = [s for s in line["spans"] if s["text"].strip()]
                if not spans:
                    continue
                x0, y0, _, y1 = line["bbox"]
                if y0 > height - _PDF_EDGE_MARGIN or y1 < _PDF_EDGE_MARGIN:
                    continue  # running header / footer / page number
                page_lines.append({
                    "page": page_no, "x0": x0, "y0": y0, "y1": y1,
                    "text": "".join(s["text"] for s in line["spans"]).strip(),
                    "size": round(max(s["size"] for s in spans), 1),
                    "bold": any("bold" in s["font"].lower() for s in spans),
                })
        page_lines.sort(key=lambda ln: (round(ln["y0"]), ln["x0"]))  # reading order
        lines.extend(page_lines)
    return lines


def extract_pdf(path):
    import pymupdf

    try:
        doc = pymupdf.open(str(path))
    except Exception as error:
        raise ExtractionError(f"The PDF could not be opened ({type(error).__name__}).")

    with doc:
        if doc.needs_pass:
            raise ExtractionError("The PDF is password-protected.")
        page_count = doc.page_count
        lines = _pdf_lines(doc)
        pdf_title = (doc.metadata or {}).get("title") or None

    if not lines:
        return ExtractedDocument("pdf", pdf_title, {}, [], page_count)

    # The most common font size (weighted by text length) is normal body text
    sizes = Counter()
    for ln in lines:
        sizes[ln["size"]] += len(ln["text"])
    body_size = sizes.most_common(1)[0][0]

    # Title = biggest text on page 1 (if clearly bigger than body text)
    first_page = [ln for ln in lines if ln["page"] == 1]
    biggest = max(first_page, key=lambda ln: ln["size"]) if first_page else None
    title = None
    if biggest and biggest["size"] >= body_size * 1.4:
        title = biggest["text"]
        lines.remove(biggest)

    metadata, items = {}, []
    current = None          # [kind, [texts], page, last_line]
    pending_bullet = False  # a lone bullet symbol was seen; the next line starts a bullet item

    def flush():
        nonlocal current
        if current:
            items.append((current[0], _join_pdf_lines(current[1]), current[2]))
        current = None

    for ln in lines:
        text = ln["text"]
        if _try_metadata(text, metadata):
            flush(); continue
        if text in ("•", "●", "-", "*"):
            flush(); pending_bullet = True; continue

        is_heading = ln["size"] >= body_size * 1.15 and len(text) < 120
        if is_heading:
            flush(); items.append(("heading", text, ln["page"])); continue

        starts_bullet = pending_bullet or bool(_BULLET_RE.match(text))
        pending_bullet = False
        if starts_bullet:
            flush()
            current = ["bullet", [_BULLET_RE.sub("", text, count=1)], ln["page"], ln]
            continue

        if current is not None:
            prev = current[3]
            same_page = prev["page"] == ln["page"]
            gap = ln["y0"] - prev["y1"] if same_page else 0
            new_paragraph = (same_page and gap > ln["size"] * 0.5) or ln["size"] != prev["size"]
            if not new_paragraph:
                current[1].append(text); current[3] = ln; continue
            flush()
        current = ["paragraph", [text], ln["page"], ln]
    flush()

    return ExtractedDocument("pdf", clean_text(title or pdf_title or "") or None, metadata,
                             _build_sections(items), page_count)


def _join_pdf_lines(parts):
    """Join wrapped PDF lines; keep 'well-' + 'known' as 'well-known'."""
    text = ""
    for part in parts:
        if text.endswith("-") and part[:1].islower():
            text += part
        else:
            text = f"{text} {part}" if text else part
    return text


# --------------------------------------------------------------------- main --

_EXTRACTORS = {"pdf": extract_pdf, "docx": extract_docx, "txt": extract_txt}


def extract_document(path, file_type) -> ExtractedDocument:
    """Read a file of the given type. Raises ExtractionError if it has no usable text."""
    if file_type not in _EXTRACTORS:
        raise ExtractionError(f"Unsupported file type: {file_type}")
    extracted = _EXTRACTORS[file_type](path)
    if extracted.text_length == 0:
        hint = " Scanned PDFs need OCR, which is not supported." if file_type == "pdf" else ""
        raise ExtractionError("No readable text was found in the document." + hint)
    return extracted
