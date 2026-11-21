from pathlib import Path
from markitdown import MarkItDown


def _run_markitdown(file_path: str) -> str:
    converter = MarkItDown()
    result = converter.convert(file_path)
    markdown_text = getattr(result, "markdown", None) or getattr(result, "text_content", "")
    return markdown_text or ""


def _run_anydoc(file_path: str) -> str:
    """
    AnyDoc mode (without Docling): converts supported documents to Markdown via MarkItDown,
    with a plain-text fallback for .txt/.md files if needed.
    """
    text = _run_markitdown(file_path)
    if text.strip():
        return text

    ext = Path(file_path).suffix.lower()
    if ext in {".txt", ".md", ".csv", ".log"}:
        return Path(file_path).read_text(encoding="utf-8", errors="replace")

    return text


def extract_to_markdown(file_path: str, parser_name: str | None) -> tuple[str, str]:
    normalized = (parser_name or "markitdown").strip().lower()

    if normalized == "anydoc":
        return "anydoc", _run_anydoc(file_path)

    # Default parser for the POC
    return "markitdown", _run_markitdown(file_path)