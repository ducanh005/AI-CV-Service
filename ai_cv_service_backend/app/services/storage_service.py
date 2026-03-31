import os
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from app.core.config import settings
from app.core.exceptions import AppException


class StorageService:
    allowed_avatar_types = {"image/png", "image/jpeg", "image/webp"}
    allowed_cv_types = {
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/msword",
    }

    extension_by_mime = {
        "application/pdf": {".pdf"},
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": {".docx"},
        "application/msword": {".doc"},
        "image/png": {".png"},
        "image/jpeg": {".jpg", ".jpeg"},
        "image/webp": {".webp"},
    }

    @classmethod
    def _infer_allowed_extensions(cls, allowed_types: set[str]) -> set[str]:
        allowed_extensions: set[str] = set()
        for mime in allowed_types:
            allowed_extensions.update(cls.extension_by_mime.get(mime, set()))
        return allowed_extensions

    @staticmethod
    async def save_upload(file: UploadFile, target_dir: str, allowed_types: set[str]) -> str:
        suffix = Path(file.filename or "").suffix.lower()
        allowed_extensions = StorageService._infer_allowed_extensions(allowed_types)
        type_allowed = file.content_type in allowed_types
        extension_allowed = suffix in allowed_extensions

        # Some clients send generic MIME types for uploads; accept known extensions as fallback.
        if not type_allowed and not extension_allowed:
            raise AppException("Unsupported file type", status_code=400)

        content = await file.read()
        max_size = settings.MAX_FILE_SIZE_MB * 1024 * 1024
        if len(content) > max_size:
            raise AppException("File exceeds max size", status_code=400)

        unique_name = f"{uuid4().hex}{suffix}"
        os.makedirs(target_dir, exist_ok=True)
        file_path = Path(target_dir) / unique_name

        with open(file_path, "wb") as out:
            out.write(content)

        return str(file_path).replace("\\", "/")
