#!/usr/bin/env python3
"""
PDF to EPUB converter using pdfminer.six for text extraction and ebooklib for EPUB creation.

Usage:
    python3 pdf_to_epub.py <input.pdf> [output.epub]

Example:
    python3 pdf_to_epub.py polanyi-personal-knowledge.pdf polanyi-personal-knowledge.epub
"""

import sys
import re
import uuid
import argparse
from pathlib import Path

from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer, LTChar, LTAnon, LTTextLine
from ebooklib import epub


# ── Text extraction ────────────────────────────────────────────────────────────

def get_font_size(element):
    """Return the most common font size in a text container."""
    sizes = []
    for line in element:
        if isinstance(line, LTTextLine):
            for char in line:
                if isinstance(char, LTChar):
                    sizes.append(round(char.size, 1))
    if not sizes:
        return 10.0
    return max(set(sizes), key=sizes.count)


def is_bold(element):
    """Rough heuristic: font name contains Bold."""
    for line in element:
        if isinstance(line, LTTextLine):
            for char in line:
                if isinstance(char, LTChar) and "Bold" in char.fontname:
                    return True
    return False


def extract_blocks(pdf_path: str):
    """
    Extract text blocks from the PDF, tagging each with approximate role
    (heading, subheading, paragraph) based on font size.
    Returns list of dicts: {text, font_size, bold}.
    """
    blocks = []
    for page_layout in extract_pages(pdf_path):
        for element in page_layout:
            if not isinstance(element, LTTextContainer):
                continue
            text = element.get_text().strip()
            if not text:
                continue
            size = get_font_size(element)
            bold = is_bold(element)
            blocks.append({"text": text, "size": size, "bold": bold})
    return blocks


# ── Block classification ───────────────────────────────────────────────────────

def classify_blocks(blocks):
    """
    Assign a role to each block: 'h1', 'h2', 'h3', or 'p'.
    Uses font-size distribution to determine thresholds.
    """
    if not blocks:
        return blocks

    sizes = [b["size"] for b in blocks]
    sizes_sorted = sorted(set(sizes), reverse=True)

    # Determine heading thresholds from the size distribution
    body_size = max(set(sizes), key=sizes.count)
    large_threshold = body_size * 1.5
    medium_threshold = body_size * 1.2

    for b in blocks:
        s = b["size"]
        if s >= large_threshold:
            b["role"] = "h1"
        elif s >= medium_threshold or (b["bold"] and s > body_size):
            b["role"] = "h2"
        elif b["bold"] and s == body_size:
            b["role"] = "h3"
        else:
            b["role"] = "p"
    return blocks


# ── Chapter splitting ─────────────────────────────────────────────────────────

def split_into_chapters(blocks):
    """
    Group blocks into chapters. A new chapter starts at each h1.
    Returns list of {title, blocks}.
    """
    chapters = []
    current = {"title": "Introduction", "blocks": []}

    for b in blocks:
        if b["role"] == "h1":
            if current["blocks"]:
                chapters.append(current)
            current = {"title": b["text"].replace("\n", " ").strip(), "blocks": []}
        else:
            current["blocks"].append(b)

    if current["blocks"] or not chapters:
        chapters.append(current)

    return chapters


# ── HTML rendering ─────────────────────────────────────────────────────────────

def block_to_html(b):
    text = b["text"].replace("\n", " ").strip()
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    role = b["role"]
    if role == "h1":
        return f"<h1>{text}</h1>\n"
    if role == "h2":
        return f"<h2>{text}</h2>\n"
    if role == "h3":
        return f"<h3>{text}</h3>\n"
    return f"<p>{text}</p>\n"


def chapter_to_html(chapter):
    title = chapter["title"].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    body = "".join(block_to_html(b) for b in chapter["blocks"])
    return f"<h1>{title}</h1>\n{body}"


# ── EPUB assembly ─────────────────────────────────────────────────────────────

CSS = """
body { font-family: Georgia, serif; margin: 5% 8%; line-height: 1.6; }
h1 { font-size: 1.6em; margin-top: 2em; border-bottom: 1px solid #ccc; padding-bottom: .3em; }
h2 { font-size: 1.3em; margin-top: 1.6em; }
h3 { font-size: 1.1em; margin-top: 1.2em; }
p  { margin: .6em 0; text-align: justify; }
"""


def build_epub(chapters, output_path: str, title: str, author: str):
    book = epub.EpubBook()
    book.set_identifier(str(uuid.uuid4()))
    book.set_title(title)
    book.set_language("en")
    book.add_author(author)

    # Stylesheet
    style = epub.EpubItem(
        uid="style",
        file_name="style/main.css",
        media_type="text/css",
        content=CSS,
    )
    book.add_item(style)

    epub_chapters = []
    for i, ch in enumerate(chapters):
        ch_title = ch["title"][:80]  # truncate for file name safety
        safe_name = re.sub(r"[^a-z0-9]+", "-", ch_title.lower()).strip("-") or f"chap{i}"
        item = epub.EpubHtml(
            title=ch_title,
            file_name=f"chap/{safe_name}.xhtml",
            lang="en",
        )
        item.content = chapter_to_html(ch)
        item.add_item(style)
        book.add_item(item)
        epub_chapters.append(item)

    # Navigation
    book.toc = tuple(epub.Link(c.file_name, c.title, c.file_name) for c in epub_chapters)
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    book.spine = ["nav"] + epub_chapters

    epub.write_epub(output_path, book)
    print(f"EPUB written to: {output_path}")


# ── CLI entry point ───────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Convert a PDF to EPUB.")
    parser.add_argument("pdf", help="Path to source PDF file")
    parser.add_argument("epub_out", nargs="?", help="Output EPUB path (default: same name as PDF)")
    parser.add_argument("--title", default="Personal Knowledge: Towards a Post-Critical Philosophy",
                        help="Book title")
    parser.add_argument("--author", default="Michael Polanyi", help="Author name")
    args = parser.parse_args()

    pdf_path = args.pdf
    epub_out = args.epub_out or Path(pdf_path).with_suffix(".epub").name

    print(f"Extracting text from {pdf_path} …")
    blocks = extract_blocks(pdf_path)
    print(f"  {len(blocks)} text blocks extracted.")

    blocks = classify_blocks(blocks)
    chapters = split_into_chapters(blocks)
    print(f"  {len(chapters)} chapters identified.")

    build_epub(chapters, epub_out, title=args.title, author=args.author)


if __name__ == "__main__":
    main()
