"""epub → json: 提取并保存到 asset/book/{project}/"""

from core.config import get_project_config
from ingest.epub import parse_epub
from core.utils import write_json

PROJECT = "division_of_labor"  # ← 改这里切换项目


def main():
    cfg = get_project_config(PROJECT)
    epub_path = cfg.book_epub_path()
    output_path = cfg.book_json_path()

    print(f"Parsing {epub_path} ...")
    result = parse_epub(str(epub_path))
    write_json(str(output_path), result)
    print(f"Done -> {output_path}")


if __name__ == "__main__":
    main()
