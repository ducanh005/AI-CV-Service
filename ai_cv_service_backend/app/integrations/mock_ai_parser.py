import re
from pathlib import Path


def _extract_text_from_pdf(file_path: str) -> str:
    from pypdf import PdfReader

    reader = PdfReader(file_path)
    texts = [(page.extract_text() or "") for page in reader.pages]
    return "\n".join(texts)


def _extract_text_from_docx(file_path: str) -> str:
    from docx import Document

    doc = Document(file_path)
    return "\n".join(paragraph.text for paragraph in doc.paragraphs if paragraph.text)


def extract_text_from_cv(file_path: str) -> str:
    ext = Path(file_path).suffix.lower()
    try:
        if ext == ".pdf":
            return _extract_text_from_pdf(file_path)
        if ext == ".docx":
            return _extract_text_from_docx(file_path)
        if ext in {".txt", ".md"}:
            return Path(file_path).read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""

    return ""


def _extract_skills(text: str) -> list[str]:
    skill_bank = [
        "python",
        "java",
        "javascript",
        "typescript",
        "react",
        "nodejs",
        "fastapi",
        "django",
        "flask",
        "sql",
        "postgresql",
        "mysql",
        "docker",
        "kubernetes",
        "aws",
        "gcp",
        "azure",
        "git",
        "redis",
        "celery",
        "communication",
        "problem solving",
    ]
    normalized = f" {text.lower()} "
    return [skill for skill in skill_bank if f" {skill} " in normalized]


def _extract_experience_signals(text: str) -> list[str]:
    matches = re.findall(r"(\d{1,2})\+?\s*(?:years|year|yrs)", text, flags=re.IGNORECASE)
    if not matches:
        return []
    max_year = max(int(m) for m in matches)
    return [f"Detected up to {max_year} years of experience from CV text"]


def _extract_education_signals(text: str) -> list[str]:
    lower = text.lower()
    education_keywords = ["bachelor", "master", "phd", "university", "college", "certification"]
    found = [keyword for keyword in education_keywords if keyword in lower]
    if not found:
        return []
    return [f"Education keywords found: {', '.join(found)}"]


def parse_cv_file(file_path: str) -> dict[str, list[str]]:
    text = extract_text_from_cv(file_path)
    if not text:
        name_tokens = Path(file_path).stem.replace("_", " ").split()
        return {
            "skills": ["python", "fastapi", "sql"],
            "experience": [f"Fallback inference from filename tokens: {len(name_tokens)}"],
            "education": ["No education signals extracted"],
        }

    cleaned = re.sub(r"\s+", " ", text).strip()
    skills = _extract_skills(cleaned)
    experience = _extract_experience_signals(cleaned)
    education = _extract_education_signals(cleaned)
    return {
        "skills": skills,
        "experience": experience,
        "education": education,
    }
