import os
import re
import warnings
from typing import Optional
from urllib.parse import unquote, urldefrag

from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning

warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)


def normalize_text(text: str) -> str:
    return " ".join(text.split())


def make_soup(markup: str) -> BeautifulSoup:
    soup = BeautifulSoup(markup, "xml")
    return soup if soup.find() else BeautifulSoup(markup, "html.parser")


def resolve_href(base_dir: str, href: str) -> tuple[str, Optional[str]]:
    file_part, fragment = urldefrag(href or "")
    path = os.path.normpath(os.path.join(base_dir, unquote(file_part))) if file_part else ""
    return path, fragment or None


def remove_citations(text: str) -> str:
    text = re.sub(r"\s*\[\s*[\d,\s]+\s*\]\s*", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def remove_references(paragraphs: list[str]) -> list[str]:
    return [text for text in paragraphs if not text.startswith("[ ")]


def extract_chapters(book_data: dict) -> dict[str, dict[str, str]]:
    chapters = {}
    for chapter_key, chapter in book_data["book_tree"].items():
        if chapter_key == "版权信息":
            continue

        chapter_id, title = chapter_key.split(maxsplit=1)
        body = "".join(remove_references(chapter["paragraphs"]))
        chapters[chapter_id] = {
            "title": title,
            "body": remove_citations(body),
        }
    return chapters

def split_chunks(text: str, max_chars: int = 4500) -> list[str]:
    paragraphs = [p.strip() for p in re.split(r"\n+", text) if p.strip()]

    if len(paragraphs) <= 1:
        sentences = [s.strip() for s in re.split(r"(?<=[。！？!?；;])\s*", text) if s.strip()]
        paragraphs = sentences or [text.strip()]

    chunks: list[str] = []
    current: list[str] = []
    current_len = 0

    for paragraph in paragraphs:
        if current and current_len + len(paragraph) > max_chars:
            chunks.append("\n\n".join(current))
            current = []
            current_len = 0
        current.append(paragraph)
        current_len += len(paragraph)

    if current:
        chunks.append("\n\n".join(current))
    return chunks