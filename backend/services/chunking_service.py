"""
chunking_service.py - Cut an ExtractedDocument into small, overlapping chunks.

Rules:
1. Never mix two sections in one chunk (split by section first).
2. Inside a section, build chunks from whole sentences / bullet points
   until CHUNK_SIZE characters would be exceeded.
3. Start the next chunk with the last sentences of the previous one
   (up to CHUNK_OVERLAP characters), so ideas at a border are not lost.
4. Never cut inside a sentence, unless one sentence alone is longer than
   CHUNK_SIZE (then it is cut between words).
5. Every chunk remembers its page number (PDF) and section heading (for citations).
"""

import re
from dataclasses import dataclass
from typing import Optional

# Abbreviations whose dot does NOT end a sentence
_ABBREVIATIONS = ["Pvt.", "Ltd.", "e.g.", "i.e.", "etc.", "No.", "Dr.", "Mr.", "Mrs.", "Ms.",
                  "vs.", "Inc.", "approx.", "Sr.", "Jr.", "Co."]
_SENTENCE_END = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9\"'(\[])")
_DOT_PLACEHOLDER = "\u0000"


@dataclass
class Chunk:
    chunk_index: int
    content: str
    page_number: Optional[int]
    section_reference: Optional[str]

    @property
    def char_count(self):
        return len(self.content)


@dataclass
class _Unit:
    """One sentence or one bullet point - the smallest piece we never cut."""
    text: str
    page: Optional[int]
    new_line: bool  # True = starts a new paragraph/bullet line, False = continues a paragraph


def split_sentences(text: str):
    """'Hello there. How are you?' -> ['Hello there.', 'How are you?']"""
    protected = text
    for abbr in _ABBREVIATIONS:
        protected = protected.replace(abbr, abbr.replace(".", _DOT_PLACEHOLDER))
    parts = _SENTENCE_END.split(protected)
    return [p.replace(_DOT_PLACEHOLDER, ".").strip() for p in parts if p.strip()]


def _section_units(section):
    units = []
    for block in section.blocks:
        if block.kind == "bullet":
            units.append(_Unit(f"- {block.text}", block.page, True))
        else:
            for i, sentence in enumerate(split_sentences(block.text)):
                units.append(_Unit(sentence, block.page, i == 0))
    return units


def _split_long_unit(unit, size, overlap):
    """A single sentence longer than the chunk size is cut between words."""
    words, pieces, current = unit.text.split(), [], []
    for word in words:
        if current and len(" ".join(current + [word])) > size:
            pieces.append(" ".join(current))
            tail = []
            for w in reversed(current):  # word-level overlap
                if len(" ".join([w] + tail)) > overlap:
                    break
                tail.insert(0, w)
            current = tail
        current.append(word)
    if current:
        pieces.append(" ".join(current))
    return [_Unit(p, unit.page, unit.new_line if i == 0 else True) for i, p in enumerate(pieces)]


def _join(units):
    text = ""
    for i, unit in enumerate(units):
        if i == 0:
            text = unit.text
        else:
            text += ("\n" if unit.new_line else " ") + unit.text
    return text


def _pack(units, size, overlap):
    """Greedily fill chunks with whole units, adding overlap between neighbours."""
    chunks, current = [], []
    for unit in units:
        if current and len(_join(current + [unit])) > size:
            chunks.append(current)
            # take trailing units from the finished chunk as overlap
            tail = []
            for prev in reversed(current):
                if len(_join([prev] + tail)) > overlap:
                    break
                tail.insert(0, prev)
            if len(tail) == len(current):  # never repeat a whole chunk
                tail = tail[1:]
            current = tail + [unit]
            while len(current) > 1 and len(_join(current)) > size:
                current.pop(0)  # drop overlap if it does not fit
        else:
            current.append(unit)
    if current:
        chunks.append(current)
    return chunks


def chunk_document(extracted, chunk_size=800, chunk_overlap=150):
    """Return a list of Chunk objects for an ExtractedDocument."""
    if chunk_size < 100:
        raise ValueError("chunk_size must be at least 100 characters")
    if not 0 <= chunk_overlap < chunk_size // 2:
        raise ValueError("chunk_overlap must be between 0 and half of chunk_size")

    chunks = []
    for section in extracted.sections:
        units = []
        for unit in _section_units(section):
            units.extend(_split_long_unit(unit, chunk_size, chunk_overlap)
                         if len(unit.text) > chunk_size else [unit])

        for group in _pack(units, chunk_size, chunk_overlap):
            chunks.append(Chunk(
                chunk_index=len(chunks),
                content=_join(group),
                page_number=group[0].page,
                section_reference=section.heading,
            ))
    return chunks


def embedding_text(title, section, content):
    """
    The text that will be turned into an embedding (Phase 6).
    Adding the title and section as a small label helps the search understand
    short chunks like 'It cannot be carried forward.'
    """
    label = " > ".join(p for p in (title, section) if p)
    return f"{label}\n{content}" if label else content
