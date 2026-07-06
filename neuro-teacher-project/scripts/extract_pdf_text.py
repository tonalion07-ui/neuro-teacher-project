"""
Извлечение текста из PDF в .txt для последующего анализа в чате.

Использование:
    python scripts/extract_pdf_text.py <pdf_path> [output_txt]

По умолчанию .txt кладётся рядом с PDF, с тем же именем + .txt.
"""
import os
import sys

# Фикс эмодзи/Unicode в print на Windows-консоли.
os.environ["PYTHONIOENCODING"] = "utf-8"
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except (AttributeError, OSError):
    pass

from pathlib import Path

from pypdf import PdfReader


def extract(pdf_path: Path, output_path: Path) -> tuple[int, int]:
    """Возвращает (количество_страниц, количество_непустых_страниц)."""
    reader = PdfReader(str(pdf_path))
    pages_text: list[str] = []
    non_empty = 0

    for i, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        if text.strip():
            non_empty += 1
        pages_text.append(f"\n\n===== PAGE {i} =====\n\n{text}")

    output_path.write_text("".join(pages_text), encoding="utf-8")
    return len(reader.pages), non_empty


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Использование: python scripts/extract_pdf_text.py <pdf_path> [output_txt]")
        sys.exit(1)

    pdf_path = Path(sys.argv[1])
    if not pdf_path.exists():
        print(f"[ERR] Файл не найден: {pdf_path}")
        sys.exit(1)

    output_path = (
        Path(sys.argv[2])
        if len(sys.argv) > 2
        else pdf_path.with_suffix(".txt")
    )

    total, non_empty = extract(pdf_path, output_path)
    size_kb = output_path.stat().st_size / 1024
    print(f"[OK] Извлечено: {total} стр., {non_empty} непустых → {output_path} ({size_kb:.1f} КБ)")