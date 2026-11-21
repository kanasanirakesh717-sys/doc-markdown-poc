from pathlib import Path
from markitdown import MarkItDown


def _get_converter() -> MarkItDown:
    try:
        return MarkItDown()
    except Exception:
        return MarkItDown(enable_builtins=False)


def _run_markitdown(file_path: str) -> str:
    converter = _get_converter()
    result = converter.convert(file_path)
    markdown_text = getattr(result, "markdown", None) or getattr(result, "text_content", "")
    if markdown_text and markdown_text.strip():
        return markdown_text

    ext = Path(file_path).suffix.lower()
    if ext in {".txt", ".md", ".csv", ".log", ".json", ".xml", ".html"}:
        return Path(file_path).read_text(encoding="utf-8", errors="replace")

    return markdown_text or ""


def _run_anydoc(file_path: str) -> str:
    """
    AnyDoc mode: converts documents to Markdown via MarkItDown with a
    plain-text fallback for text-based formats.
    """
    text = _run_markitdown(file_path)
    if text.strip():
        return text

    return Path(file_path).read_text(encoding="utf-8", errors="replace")


def extract_to_markdown(file_path: str, parser_name: str | None) -> tuple[str, str]:
    normalized = (parser_name or "markitdown").strip().lower()

    if normalized == "anydoc":
        return "anydoc", _run_anydoc(file_path)

    return "markitdown", _run_markitdown(file_path)