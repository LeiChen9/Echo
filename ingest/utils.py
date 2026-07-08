import os
import re
import warnings
from pathlib import PurePosixPath
from typing import Optional
from urllib.parse import unquote, urldefrag

from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning

warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)


def make_soup(markup: str) -> BeautifulSoup:
    soup = BeautifulSoup(markup, "xml")
    return soup if soup.find() else BeautifulSoup(markup, "html.parser")


def resolve_href(base_dir: str, href: str) -> tuple[str, Optional[str]]:
    file_part, fragment = urldefrag(href or "")
    if not file_part:
        return "", fragment or None
    path = str(PurePosixPath(base_dir.replace("\\", "/"), unquote(file_part)))
    return path, fragment or None


def normalize_text(text: str) -> str:
    text = text.replace("\u200b", "")
    return " ".join(text.split())
