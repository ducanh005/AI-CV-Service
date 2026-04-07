from pathlib import Path

from app.config import settings


class CVParsingError(RuntimeError):
    pass


def _is_subpath(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def resolve_cv_path(raw_path: str) -> Path:
    incoming_path = Path(raw_path)
    candidates: list[Path] = []

    if incoming_path.is_absolute():
        candidates.append(incoming_path)
    else:
        candidates.append(Path(settings.CV_BASE_DIR) / incoming_path)
        candidates.append(incoming_path)

    for candidate in candidates:
        resolved = candidate.resolve()
        if not resolved.exists():
            continue
        if any(_is_subpath(resolved, root) for root in settings.allowed_cv_roots):
            return resolved

    raise CVParsingError("CV file does not exist or is outside allowed roots")


def _extract_text_from_pdf(path: Path) -> str:
    from pypdf import PdfReader

    reader = PdfReader(str(path))
    pages = [(page.extract_text() or "") for page in reader.pages]
    return "\n".join(pages)


def _extract_text_from_docx(path: Path) -> str:
    from docx import Document

    doc = Document(str(path))
    return "\n".join(paragraph.text for paragraph in doc.paragraphs if paragraph.text)


def extract_cv_text(raw_path: str) -> str:
    cv_path = resolve_cv_path(raw_path)
    suffix = cv_path.suffix.lower()

    if suffix == ".pdf":
        text = _extract_text_from_pdf(cv_path)
    elif suffix in {".docx", ".doc"}:
        text = _extract_text_from_docx(cv_path)
    elif suffix in {".txt", ".md"}:
        text = cv_path.read_text(encoding="utf-8", errors="ignore")
    else:
        raise CVParsingError(f"Unsupported CV extension: {suffix}")

    if not text.strip():
        raise CVParsingError("No text extracted from CV")

    return text
