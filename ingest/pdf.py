from __future__ import annotations

import os
from typing import Optional

from ingest.utils import normalize_text as _norm


SKIP_TITLES = {"目录", "Contents", "Table of Contents"}


class TocNode:
    __slots__ = ("title", "href", "paragraphs", "images", "children", "page")

    def __init__(self, title: str, page: int = 0):
        self.title = title
        self.href = f"page-{page}" if page else ""
        self.paragraphs: list[str] = []
        self.images: list[dict[str, str]] = []
        self.children: dict[str, TocNode] = {}
        self.page = page

    def child(self, title: str) -> TocNode:
        return self.children.setdefault(title, TocNode(title))


def _toc_to_tree(toc: list[tuple[int, str, int]]) -> TocNode:
    root = TocNode("ROOT")
    stack: list[tuple[int, TocNode]] = []

    for level, title, page in toc:
        title = _norm(title)
        if not title or title in SKIP_TITLES:
            continue
        node = TocNode(title, page)
        while stack and stack[-1][0] >= level:
            stack.pop()
        parent = stack[-1][1] if stack else root
        parent.children[title] = node
        stack.append((level, node))

    return root


def _flatten_leaves(node: TocNode) -> list[TocNode]:
    if not node.children:
        return [node]
    result = []
    for child in node.children.values():
        result.extend(_flatten_leaves(child))
    return result


def _walk_all(node: TocNode):
    for child in node.children.values():
        yield child
        yield from _walk_all(child)


def _extract_pdf_text(
    doc, page_start: int, page_end: int
) -> tuple[list[str], list[dict[str, str]]]:
    paragraphs: list[str] = []
    images: list[dict[str, str]] = []
    for i in range(page_start, page_end):
        page = doc[i]
        text = page.get_text("text")
        for block in text.split("\n\n"):
            cleaned = _norm(block)
            if cleaned:
                paragraphs.append(cleaned)
    return paragraphs, images


def _attach_pdf_content(root: TocNode, doc) -> None:
    leaves = _flatten_leaves(root)
    total_pages = doc.page_count

    for idx, leaf in enumerate(leaves):
        start = max(0, leaf.page - 1)  # PyMuPDF 0-indexed
        raw_end = leaves[idx + 1].page - 1 if idx + 1 < len(leaves) else total_pages
        end = max(start + 1, raw_end)  # 至少取一页，避免同页多标题漏内容
        leaf.paragraphs, leaf.images = _extract_pdf_text(doc, start, end)


def _node_to_dict(node: TocNode) -> dict:
    return {
        child.title: {
            "href": child.href,
            "paragraphs": child.paragraphs,
            "images": child.images,
            "children": _node_to_dict(child),
        }
        for child in node.children.values()
    }


def _search_guide(root: TocNode) -> dict:
    return {
        "toc_tree": {
            chapter.title: {
                section.title: list(section.children)
                for section in chapter.children.values()
            }
            for chapter in root.children.values()
        }
    }


def _pymupdf_convert(pdf_path: str) -> dict:
    import fitz

    doc = fitz.open(pdf_path)
    try:
        toc = doc.get_toc()
        if not toc:
            raise RuntimeError("PDF 中未找到目录结构（bookmarks）")
        root = _toc_to_tree(toc)
        _attach_pdf_content(root, doc)
        return {
            "book_tree": _node_to_dict(root),
            "search_guide": _search_guide(root),
        }
    finally:
        doc.close()


SUPPORTED_STRATEGIES = {"pymupdf"}


def convert_pdf(pdf_path: str, strategy: str = "pymupdf") -> dict:
    if strategy not in SUPPORTED_STRATEGIES:
        raise ValueError(f"不支持策略: {strategy}，可选: {SUPPORTED_STRATEGIES}")
    if not os.path.isfile(pdf_path):
        raise FileNotFoundError(f"PDF 文件不存在: {pdf_path}")
    return _pymupdf_convert(pdf_path)
