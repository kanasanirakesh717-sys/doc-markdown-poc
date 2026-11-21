from pathlib import Path
from docling.document_converter import DocumentConverter
from markitdown import MarkItDown


def _run_markitdown(file_path: str) -> str:
    converter = MarkItDown()
    result = converter.convert(file_path)
    markdown_text = getattr(result, "markdown", None) or getattr(result, "text_content", "")
    return markdown_text or ""


def _run_docling(file_path: str) -> str:
    converter = DocumentConverter()
    result = converter.convert(file_path)
    return result.document.export_to_markdown() or ""


def _run_anydoc(file_path: str) -> str:
    """
    AnyDoc mode: tries Docling for rich layout/PDF parsing first,
    and falls back cleanly to MarkItDown so output is always Markdown text.
    """
    ext = Path(file_path).suffix.lower()
    if ext == ".pdf":
        try:
            text = _run_docling(file_path)
            if text.strip():
                return text
        except Exception:
            pass
    return _run_markitdown(file_path)


def extract_to_markdown(file_path: str, parser_name: str | None) -> tuple[str, str]:
    normalized = (parser_name or "markitdown").strip().lower()

    if normalized == "docling":
        return "docling", _run_docling(file_path)
    if normalized == "anydoc":
        return "anydoc", _run_anydoc(file_path)

    # Default parser for the POC
    return "markitdown", _run_markitdown(file_path)