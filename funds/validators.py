from __future__ import annotations

from pathlib import Path

from django.core.files.uploadedfile import UploadedFile
from django.template.defaultfilters import filesizeformat
from rest_framework.exceptions import ValidationError

MAX_UPLOAD_BYTES = 5 * 1024 * 1024

COVER_EXTENSIONS: frozenset[str] = frozenset({".jpg", ".jpeg", ".png"})
DOCUMENT_EXTENSIONS: frozenset[str] = frozenset({".pdf", ".doc", ".docx", ".jpg", ".jpeg", ".png"})


def _extension(filename: str) -> str:
    return Path(filename.lower()).suffix


def validate_upload_size(value: UploadedFile) -> None:
    if value.size > MAX_UPLOAD_BYTES:
        raise ValidationError(
            f"File too large. Maximum size is {filesizeformat(MAX_UPLOAD_BYTES)}.",
        )


def validate_cover_image_file(value: UploadedFile) -> UploadedFile:
    validate_upload_size(value)
    ext = _extension(value.name)
    if ext not in COVER_EXTENSIONS:
        raise ValidationError(
            "Cover image must be one of: JPG, JPEG, PNG.",
        )
    return value


def validate_supporting_document_file(value: UploadedFile) -> UploadedFile:
    validate_upload_size(value)
    ext = _extension(value.name)
    if ext not in DOCUMENT_EXTENSIONS:
        raise ValidationError(
            "Supporting document must be one of: PDF, DOC, DOCX, JPG, JPEG, PNG.",
        )
    return value
