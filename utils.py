import json
from pathlib import Path
from typing import Any
import re


def load_json(path: str | Path) -> Any:
    with Path(path).open(encoding="utf-8") as f:
        return json.load(f)


def write_json(path: str | Path, data: Any, *, indent: int = 2) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=indent)

def json_eval(response: str) -> dict:
    # 去除 ```json ... ``` 包裹（如果有）
    text = re.sub(r'^```(?:json)?\s*|\s*```$', '', response.strip())
    
    return json.loads(text)

def read_text(path: str | Path) -> str:
    return Path(path).read_text(encoding="utf-8")


def write_text(path: str | Path, text: str) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")

def load_text(path: str | Path) -> str:
    return Path(path).read_text(encoding="utf-8")