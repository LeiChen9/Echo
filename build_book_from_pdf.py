"""PDF → book.json: 提取并保存到 asset/book/{project}/

用法:
  python build_book_from_pdf.py                # 默认 pymupdf 策略
  python build_book_from_pdf.py --strategy pymupdf
"""

from core.config import get_project_config
from core.utils import write_json
from ingest.pdf import convert_pdf

PROJECT = "how_to_use_AI_for_analysis"
STRATEGY = "pymupdf"


def main():
    cfg = get_project_config(PROJECT)
    pdf_files = list(cfg.book_dir.glob("*.pdf"))
    if not pdf_files:
        raise FileNotFoundError(f"未在 {cfg.book_dir} 中找到 PDF 文件")
    pdf_path = str(pdf_files[0])
    output_path = cfg.book_json_path()

    print(f"Converting {pdf_path} via {STRATEGY} ...")
    result = convert_pdf(pdf_path, strategy=STRATEGY)
    write_json(str(output_path), result)
    print(f"Done -> {output_path}")


if __name__ == "__main__":
    main()
