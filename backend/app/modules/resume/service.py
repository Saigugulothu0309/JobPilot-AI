"""Resume ownership, validation, and text-processing business logic."""

from __future__ import annotations

from datetime import date
from pathlib import Path
from uuid import UUID

import fitz  # type: ignore[import-untyped]
from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.profile.models import Education, Experience, Profile, Project, Skill
from app.modules.profile.service import ProfileService
from app.modules.resume.models import Resume
from app.modules.resume.processing import (
    ExtractionError,
    PDFExtractor,
    ProcessingResult,
    get_document_extractor,
    normalize_text,
)
from app.modules.resume.storage import LocalStorageService

MAX_RESUME_BYTES = 10 * 1024 * 1024
ALLOWED_MIME_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}
ALLOWED_SUFFIXES = {".pdf", ".docx"}


class ResumeNotFoundError(RuntimeError):
    """Raised when a resume is absent or belongs to another profile."""


class ResumeProcessingService:
    def __init__(
        self,
        session: Session,
        storage_service: LocalStorageService | None = None,
    ) -> None:
        self.session = session
        self.storage_service = storage_service or LocalStorageService()

    def process_for_profile(self, user_id: UUID, resume_id: UUID) -> ProcessingResult:
        resume = ResumeService(self.session, self.storage_service).get_for_profile(
            user_id,
            resume_id,
        )
        try:
            file_bytes = self.storage_service.get(resume.storage_key)
        except (ValueError, FileNotFoundError) as exc:
            raise ResumeProcessingError(
                "Resume file is missing from storage.",
                "MISSING_STORED_FILE",
            ) from exc

        if not file_bytes:
            return ProcessingResult(
                success=False,
                extractor="",
                error_code="EMPTY_DOCUMENT",
                error_message="Stored resume is empty.",
            )

        try:
            extractor = get_document_extractor(resume.mime_type, resume.original_filename)
        except ExtractionError as exc:
            return ProcessingResult(
                success=False,
                extractor="",
                error_code=exc.code,
                error_message=exc.message,
            )

        try:
            raw_text = extractor.extract(file_bytes)
        except ExtractionError as exc:
            return ProcessingResult(
                success=False,
                text="",
                character_count=0,
                extractor=extractor.name,
                error_code=exc.code,
                error_message=exc.message,
            )

        text = normalize_text(raw_text)
        if not text:
            return ProcessingResult(
                success=False,
                extractor=extractor.name,
                error_code="EMPTY_DOCUMENT",
                error_message="Document contains no extractable text.",
            )

        result = ProcessingResult(
            success=True,
            text=text,
            character_count=len(text),
            extractor=extractor.name,
        )
        if isinstance(extractor, PDFExtractor):
            result.page_count = self._pdf_page_count(file_bytes)
        return result

    def _pdf_page_count(self, file_bytes: bytes) -> int | None:
        try:
            document = fitz.open(stream=file_bytes, filetype="pdf")
        except (RuntimeError, ValueError, TypeError):
            return None
        try:
            page_count_value = document.page_count
            if page_count_value is None:
                return None
            return int(page_count_value)
        finally:
            document.close()


class ResumeProcessingError(RuntimeError):
    """Raised when the stored document cannot be processed safely."""

    def __init__(self, message: str, code: str) -> None:
        super().__init__(message)
        self.message = message
        self.code = code


class ResumeReviewError(RuntimeError):
    """Raised when a resume review cannot be changed or approved."""


class ResumeReviewService:
    def __init__(
        self,
        session: Session,
        storage_service: LocalStorageService | None = None,
    ) -> None:
        self.session = session
        self.storage_service = storage_service

    def get_review(self, user_id: UUID, resume_id: UUID) -> dict[str, object]:
        resume = ResumeService(self.session, self.storage_service).get_for_profile(
            user_id, resume_id
        )
        if resume.review_data is None:
            processing = ResumeProcessingService(
                self.session, self.storage_service
            ).process_for_profile(user_id, resume_id)
            if not processing.success or not processing.text:
                raise ResumeReviewError(processing.error_message or "Resume could not be parsed")
            from app.modules.resume.parser import ResumeParser

            resume.review_data = ResumeParser().parse(processing.text).to_dict()
            resume.review_status = "PARSED"
            self.session.commit()
            self.session.refresh(resume)
        return self._response(resume)

    def update_review(
        self,
        user_id: UUID,
        resume_id: UUID,
        review_data: dict[str, object],
    ) -> dict[str, object]:
        resume = ResumeService(self.session, self.storage_service).get_for_profile(
            user_id, resume_id
        )
        if resume.review_status == "APPROVED":
            raise ResumeReviewError("Approved resume review cannot be edited")
        resume.review_data = review_data
        resume.review_status = "PARSED"
        self.session.commit()
        self.session.refresh(resume)
        return self._response(resume)

    def approve_review(self, user_id: UUID, resume_id: UUID) -> dict[str, object]:
        resume = ResumeService(self.session, self.storage_service).get_for_profile(
            user_id, resume_id
        )
        if resume.review_data is None:
            self.get_review(user_id, resume_id)
            resume = ResumeService(self.session, self.storage_service).get_for_profile(
                user_id, resume_id
            )
        if resume.review_status == "APPROVED":
            return self._response(resume)

        data = resume.review_data or {}
        profile = self.session.get(Profile, resume.profile_id)
        if profile is None:
            raise ResumeReviewError("Profile not found")
        self._approve_basic_information(profile, data.get("basic_information"))
        self._approve_skills(profile.id, data.get("skills", []))
        self._approve_education(profile.id, data.get("education", []))
        self._approve_experience(profile.id, data.get("experience", []))
        self._approve_projects(profile.id, data.get("projects", []))
        resume.review_status = "APPROVED"
        self.session.commit()
        self.session.refresh(resume)
        return self._response(resume)

    def _response(self, resume: Resume) -> dict[str, object]:
        return {
            "resume_id": resume.id,
            "status": resume.review_status,
            **(resume.review_data or {}),
        }

    def _approve_basic_information(
        self, profile: Profile, values: object
    ) -> None:
        if not isinstance(values, dict):
            return
        for field in ("full_name", "phone", "location"):
            if field in values:
                setattr(profile, field, values[field])

    def _approve_skills(self, profile_id: UUID, values: object) -> None:
        if not isinstance(values, list):
            return
        for value in values:
            if not isinstance(value, dict) or not value.get("name"):
                continue
            name = str(value["name"])
            existing = self.session.scalar(
                select(Skill).where(Skill.profile_id == profile_id, Skill.name == name)
            )
            if existing is None:
                self.session.add(
                    Skill(
                        profile_id=profile_id,
                        name=name,
                        category=value.get("category"),
                        proficiency="INTERMEDIATE",
                    )
                )

    def _approve_education(self, profile_id: UUID, values: object) -> None:
        if not isinstance(values, list):
            return
        for value in values:
            if not isinstance(value, dict) or not value.get("institution"):
                continue
            start_date = self._to_date(value.get("start_date"))
            if start_date is None:
                continue
            filters = (
                Education.profile_id == profile_id,
                Education.institution == value["institution"],
                Education.degree == value.get("degree"),
            )
            if self.session.scalar(select(Education).where(*filters)) is None:
                self.session.add(
                    Education(
                        profile_id=profile_id,
                        institution=value["institution"],
                        degree=value.get("degree"),
                        field_of_study=value.get("field_of_study"),
                        start_date=start_date,
                        end_date=self._to_date(value.get("end_date")),
                        description=value.get("description"),
                    )
                )

    def _approve_experience(self, profile_id: UUID, values: object) -> None:
        if not isinstance(values, list):
            return
        for value in values:
            if (
                not isinstance(value, dict)
                or not value.get("company")
                or not value.get("job_title")
            ):
                continue
            start_date = self._to_date(value.get("start_date"))
            if start_date is None:
                continue
            filters = (
                Experience.profile_id == profile_id,
                Experience.company == value["company"],
                Experience.job_title == value["job_title"],
                Experience.start_date == start_date,
            )
            if self.session.scalar(select(Experience).where(*filters)) is None:
                self.session.add(
                    Experience(
                        profile_id=profile_id,
                        company=value["company"],
                        job_title=value["job_title"],
                        location=value.get("location"),
                        start_date=start_date,
                        end_date=self._to_date(value.get("end_date")),
                        description=value.get("description"),
                    )
                )

    def _approve_projects(self, profile_id: UUID, values: object) -> None:
        if not isinstance(values, list):
            return
        for value in values:
            if not isinstance(value, dict) or not value.get("name"):
                continue
            start_date = self._to_date(value.get("start_date"))
            if start_date is None:
                continue
            filters = (
                Project.profile_id == profile_id,
                Project.name == value["name"],
                Project.start_date == start_date,
            )
            if self.session.scalar(select(Project).where(*filters)) is None:
                self.session.add(
                    Project(
                        profile_id=profile_id,
                        name=value["name"],
                        description=value.get("description"),
                        url=value.get("url"),
                        start_date=start_date,
                        end_date=self._to_date(value.get("end_date")),
                    )
                )

    def _to_date(self, value: object) -> date | None:
        if not isinstance(value, str) or not value.strip():
            return None
        normalized = value.strip()
        if normalized.isdigit() and len(normalized) == 4:
            return date(int(normalized), 1, 1)
        try:
            return date.fromisoformat(normalized)
        except ValueError:
            return None


class ResumeService:
    def __init__(
        self,
        session: Session,
        storage_service: LocalStorageService | None = None,
    ) -> None:
        self.session = session
        self.storage_service = storage_service or LocalStorageService()

    def _resolve_profile(self, user_id: UUID) -> Profile:
        profile = self.session.query(Profile).filter(Profile.user_id == user_id).one_or_none()
        if profile is None:
            return ProfileService(self.session).get_or_create_profile(user_id)
        return profile

    def _safe_filename(self, original_filename: str) -> str:
        candidate = Path(original_filename.replace("\\", "/")).name
        if candidate in {"", ".", ".."}:
            raise ValueError("Invalid filename")
        suffix = Path(candidate).suffix.lower()
        if suffix not in ALLOWED_SUFFIXES:
            raise ValueError("Unsupported resume format")
        return candidate

    def _validate_upload(self, file: UploadFile, file_bytes: bytes) -> tuple[str, str, str]:
        if not file.filename:
            raise ValueError("Resume filename is required")
        safe_filename = self._safe_filename(file.filename)
        mime_type = (file.content_type or "").lower()
        if mime_type not in ALLOWED_MIME_TYPES:
            raise ValueError("Unsupported resume MIME type")
        suffix = Path(safe_filename).suffix.lower()
        if suffix == ".pdf":
            if not file_bytes.startswith(b"%PDF"):
                raise ValueError("Invalid PDF file signature")
        elif suffix == ".docx":
            if not file_bytes.startswith(b"PK"):
                raise ValueError("Invalid DOCX file signature")
        if len(file_bytes) > MAX_RESUME_BYTES:
            raise ValueError("Resume file exceeds the maximum allowed size")
        return safe_filename, mime_type, suffix

    def create_for_profile(self, user_id: UUID, file: UploadFile) -> Resume:
        file_bytes = file.file.read()
        original_name, mime_type, suffix = self._validate_upload(file, file_bytes)
        profile = self._resolve_profile(user_id)
        storage_key, stored_filename = self.storage_service.save(
            file_bytes,
            original_name,
            mime_type,
        )
        resume = Resume(
            profile_id=profile.id,
            original_filename=original_name,
            stored_filename=stored_filename,
            storage_key=storage_key,
            mime_type=mime_type,
            file_size=len(file_bytes),
        )
        self.session.add(resume)
        self.session.commit()
        self.session.refresh(resume)
        return resume

    def list_for_profile(self, user_id: UUID) -> list[Resume]:
        profile = self._resolve_profile(user_id)
        return list(
            self.session.query(Resume)
            .filter(Resume.profile_id == profile.id)
            .order_by(Resume.created_at.asc())
            .all()
        )

    def get_for_profile(self, user_id: UUID, resume_id: UUID) -> Resume:
        profile = self._resolve_profile(user_id)
        resume = self.session.get(Resume, resume_id)
        if resume is None or resume.profile_id != profile.id:
            raise ResumeNotFoundError("Resume not found")
        return resume

    def delete_for_profile(self, user_id: UUID, resume_id: UUID) -> None:
        resume = self.get_for_profile(user_id, resume_id)
        try:
            self.storage_service.delete(resume.storage_key)
        except ValueError:
            pass
        self.session.delete(resume)
        self.session.commit()
