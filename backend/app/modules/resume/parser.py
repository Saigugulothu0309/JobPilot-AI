"""Structured parsing for normalized resume text."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Iterable

from app.modules.resume.processing import normalize_text


SECTION_ALIASES = {
    "summary": {"summary", "objective"},
    "skills": {"skills", "technical skills", "core skills", "programming languages"},
    "education": {"education", "academic background", "academics", "education history"},
    "experience": {"experience", "work experience", "professional experience", "employment"},
    "projects": {"projects", "academic projects", "personal projects", "portfolio projects"},
}


@dataclass(slots=True)
class BasicInformation:
    full_name: str | None = None
    email: str | None = None
    phone: str | None = None
    location: str | None = None
    linkedin_url: str | None = None
    github_url: str | None = None
    portfolio_url: str | None = None
    source: str | None = None


@dataclass(slots=True)
class SkillEntry:
    name: str
    category: str | None = None
    source: str | None = None


@dataclass(slots=True)
class EducationEntry:
    institution: str | None = None
    degree: str | None = None
    field_of_study: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    description: str | None = None
    source: str | None = None


@dataclass(slots=True)
class ExperienceEntry:
    company: str | None = None
    job_title: str | None = None
    location: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    description: str | None = None
    source: str | None = None


@dataclass(slots=True)
class ProjectEntry:
    name: str | None = None
    description: str | None = None
    technologies: list[str] = field(default_factory=list)
    url: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    source: str | None = None


@dataclass(slots=True)
class StructuredResumeResult:
    basic_information: BasicInformation | None = None
    skills: list[SkillEntry] = field(default_factory=list)
    education: list[EducationEntry] = field(default_factory=list)
    experience: list[ExperienceEntry] = field(default_factory=list)
    projects: list[ProjectEntry] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return {
            "basic_information": None
            if self.basic_information is None
            else {
                "full_name": self.basic_information.full_name,
                "email": self.basic_information.email,
                "phone": self.basic_information.phone,
                "location": self.basic_information.location,
                "linkedin_url": self.basic_information.linkedin_url,
                "github_url": self.basic_information.github_url,
                "portfolio_url": self.basic_information.portfolio_url,
                "source": self.basic_information.source,
            },
            "skills": [
                {
                    "name": skill.name,
                    "category": skill.category,
                    "source": skill.source,
                }
                for skill in self.skills
            ],
            "education": [
                {
                    "institution": item.institution,
                    "degree": item.degree,
                    "field_of_study": item.field_of_study,
                    "start_date": item.start_date,
                    "end_date": item.end_date,
                    "description": item.description,
                    "source": item.source,
                }
                for item in self.education
            ],
            "experience": [
                {
                    "company": item.company,
                    "job_title": item.job_title,
                    "location": item.location,
                    "start_date": item.start_date,
                    "end_date": item.end_date,
                    "description": item.description,
                    "source": item.source,
                }
                for item in self.experience
            ],
            "projects": [
                {
                    "name": item.name,
                    "description": item.description,
                    "technologies": item.technologies,
                    "url": item.url,
                    "start_date": item.start_date,
                    "end_date": item.end_date,
                    "source": item.source,
                }
                for item in self.projects
            ],
            "warnings": self.warnings,
        }


class ResumeParser:
    """Parse resume text into a reviewable structured result without persistence."""

    def parse(self, text: str) -> StructuredResumeResult:
        clean_text = normalize_text(text)
        if not clean_text.strip():
            return StructuredResumeResult(
                basic_information=None,
                warnings=["Resume text is empty or missing."],
            )

        lines = [line.strip() for line in clean_text.splitlines() if line.strip()]
        section_lines: dict[str, list[str]] = {
            "summary": [],
            "skills": [],
            "education": [],
            "experience": [],
            "projects": [],
        }
        current_section: str | None = None

        for line in lines:
            heading = self._detect_heading(line)
            if heading is not None:
                current_section = heading
                continue
            if current_section is not None:
                section_lines[current_section].append(line)

        basic_information = self._parse_basic_information(lines, clean_text)
        skills = self._parse_skills_by_heading(lines)
        education = self._parse_education(section_lines.get("education", []))
        experience = self._parse_experience(section_lines.get("experience", []))
        projects = self._parse_projects(section_lines.get("projects", []))

        warnings: list[str] = []
        if basic_information is None:
            warnings.append("Basic contact information could not be confidently parsed.")
        if not skills:
            warnings.append("Skills section could not be confidently parsed.")
        if not education:
            warnings.append("Education section could not be confidently parsed.")
        if not experience:
            warnings.append("Experience section could not be confidently parsed.")
        if not projects:
            warnings.append("Projects section could not be confidently parsed.")

        return StructuredResumeResult(
            basic_information=basic_information,
            skills=skills,
            education=education,
            experience=experience,
            projects=projects,
            warnings=warnings,
        )

    def _detect_heading(self, line: str) -> str | None:
        key = line.casefold().strip(" :;-|")
        for section_name, aliases in SECTION_ALIASES.items():
            if key in aliases or any(alias in key for alias in aliases):
                return section_name
        return None

    def _section_name_for(self, lines: Iterable[str]) -> str | None:
        for line in lines:
            heading = self._detect_heading(line)
            if heading is not None:
                return heading
        return None

    def _parse_basic_information(self, lines: list[str], text: str) -> BasicInformation | None:
        email = self._first_match(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text)
        phone = self._first_match(
            r"(?:\+?\d[\d\s().-]{7,}\d)",
            text,
        )
        linkedin = self._first_match(
            r"(?:https?://)?(?:www\.)?linkedin\.com/in/[A-Za-z0-9._%+-]+",
            text,
        )
        github = self._first_match(
            r"(?:https?://)?(?:www\.)?github\.com/[A-Za-z0-9._-]+",
            text,
        )
        portfolio = self._first_match(
            r"(?:https?://)?(?:www\.)?(?:[A-Za-z0-9.-]+\.)+[A-Za-z]{2,}(?:/[A-Za-z0-9._~:/?#[\]@!$&'()*+,;=%-]*)?",
            text,
        )

        name = self._extract_name(lines, text, email)
        if name and (email or phone or linkedin or github):
            return BasicInformation(
                full_name=name,
                email=email,
                phone=phone,
                location=self._infer_location(text),
                linkedin_url=self._normalize_url(linkedin, "linkedin"),
                github_url=self._normalize_url(github, "github"),
                portfolio_url=self._normalize_url(portfolio, "portfolio"),
                source="header",
            )

        if not email and not phone and not linkedin and not github:
            return None

        return BasicInformation(
            full_name=self._extract_name_from_email(text, email),
            email=email,
            phone=phone,
            location=self._infer_location(text),
            linkedin_url=self._normalize_url(linkedin, "linkedin"),
            github_url=self._normalize_url(github, "github"),
            portfolio_url=self._normalize_url(portfolio, "portfolio"),
            source="contact",
        )

    def _infer_location(self, text: str) -> str | None:
        patterns = [
            r"\b[A-Z][A-Za-z.-]+(?:\s+[A-Z][A-Za-z.-]+)*,\s*[A-Z]{2}\b",
            r"\b[A-Z][A-Za-z.-]+(?:\s+[A-Z][A-Za-z.-]+)*,\s*[A-Z][A-Za-z.-]+(?:\s+[A-Z][A-Za-z.-]+)*\b",
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                candidate = match.group(0)
                if candidate.lower() not in {"skills", "education", "experience", "projects"}:
                    return candidate
        return None

    def _extract_name(self, lines: list[str], text: str, email: str | None) -> str | None:
        for line in lines:
            lowered = line.lower()
            if lowered.startswith(("skills", "education", "experience", "projects", "summary", "objective")):
                continue
            if re.search(r"https?://", line):
                continue
            if "@" in line or "(" in line or ")" in line or "/" in line:
                continue
            candidate = re.sub(r"^[\-•|\s]+|[\-•|\s]+$", "", line)
            if not candidate:
                continue
            tokens = candidate.split()
            if len(tokens) < 2 or len(tokens) > 4:
                continue
            if not all(self._looks_like_name_token(token) for token in tokens):
                continue
            if email and candidate.lower() in text.lower():
                return candidate
            if not email and any(token.isupper() for token in tokens):
                return candidate
        return None

    def _looks_like_name_token(self, token: str) -> bool:
        cleaned = token.strip(".,;:()[]{}|\"")
        if not cleaned:
            return False
        if cleaned.lower() in {"skills", "education", "experience", "projects", "summary", "objective"}:
            return False
        if cleaned.startswith("http"):
            return False
        if any(char.isdigit() for char in cleaned):
            return False
        if not re.fullmatch(r"[A-Za-z][A-Za-z'-]*", cleaned):
            return False
        return True

    def _extract_name_from_email(self, text: str, email: str | None) -> str | None:
        if email is None:
            return None
        prefix = text.split(email)[0].strip()
        lines = [line.strip() for line in prefix.splitlines() if line.strip()]
        if lines:
            return lines[-1]
        return None

    def _parse_skills(self, lines: list[str], section_name: str | None) -> list[SkillEntry]:
        items: list[SkillEntry] = []
        if not lines:
            return items
        category = section_name
        for line in lines:
            for split_line in re.split(r"(?:\n|,|\||;)", line):
                candidate = split_line.strip()
                if not candidate:
                    continue
                if re.fullmatch(r"(?:skills|technical skills|programming languages)", candidate, re.I):
                    continue
                if len(candidate) < 2:
                    continue
                items.append(SkillEntry(name=candidate, category=category, source="skills section"))
        return items

    def _parse_skills_by_heading(self, lines: list[str]) -> list[SkillEntry]:
        items: list[SkillEntry] = []
        current_category: str | None = None
        for line in lines:
            heading = self._detect_heading(line)
            if heading == "skills":
                current_category = line.strip()
                continue
            if heading is not None:
                current_category = None
                continue
            if current_category is None:
                continue

            for split_line in re.split(r"(?:\n|,|\||;)", line):
                candidate = split_line.strip()
                if not candidate:
                    continue
                if re.fullmatch(r"(?:skills|technical skills|programming languages)", candidate, re.I):
                    continue
                if len(candidate) < 2:
                    continue
                items.append(
                    SkillEntry(
                        name=candidate,
                        category=current_category,
                        source="skills section",
                    )
                )
        return items

    def _parse_education(self, lines: list[str]) -> list[EducationEntry]:
        entries: list[EducationEntry] = []
        if not lines:
            return entries
        for line in lines:
            if not line:
                continue
            if "|" in line:
                parts = [part.strip() for part in line.split("|")]
            else:
                parts = [part.strip() for part in line.split(",")]
            degree = None
            institution = None
            field = None
            start = None
            end = None
            if parts:
                first = parts[0]
                degree_match = re.match(r"(?P<degree>[A-Za-z.]+(?:\s+[A-Za-z.]+)*)\s+in\s+(?P<field>.+)", first, re.IGNORECASE)
                if degree_match:
                    degree = degree_match.group("degree").strip()
                    field = degree_match.group("field").strip()
                    institution = parts[1].strip() if len(parts) > 1 else None
                else:
                    match = re.match(r"(?P<field>.+?)(?:,\s*(?P<institution>.+?))(?:,\s*(?P<dates>.+))?$", line, re.IGNORECASE)
                    if match:
                        field = match.group("field").strip()
                        institution = match.group("institution").strip() if match.group("institution") else None
                        if match.group("dates"):
                            start, end = self._parse_date_range(match.group("dates"))
                    else:
                        institution = first
                if line and not institution and len(parts) > 1:
                    institution = parts[1].strip()
                if len(parts) >= 3:
                    dates = parts[-1].strip()
                    start, end = self._parse_date_range(dates)
                elif " - " in line:
                    dates = line.rsplit(" - ", 1)[-1]
                    if re.search(r"\d{4}", dates):
                        start, end = self._parse_date_range(dates)
            entries.append(
                EducationEntry(
                    institution=institution,
                    degree=degree,
                    field_of_study=field,
                    start_date=start,
                    end_date=end,
                    description=line,
                    source="education section",
                )
            )
        return entries

    def _parse_experience(self, lines: list[str]) -> list[ExperienceEntry]:
        entries: list[ExperienceEntry] = []
        current: dict[str, str | None] = {"company": None, "job_title": None, "location": None, "start_date": None, "end_date": None, "description": None}
        for line in lines:
            if "|" in line:
                parts = [part.strip() for part in line.split("|")]
                if len(parts) >= 2:
                    current["job_title"] = parts[0].strip()
                    current["company"] = parts[1].strip() if len(parts) > 1 else None
                    current["location"] = parts[2].strip() if len(parts) > 2 else None
                    current["start_date"], current["end_date"] = self._parse_date_range(parts[3].strip()) if len(parts) > 3 else (None, None)
                    entries.append(
                        ExperienceEntry(
                            company=current["company"],
                            job_title=current["job_title"],
                            location=current["location"],
                            start_date=current["start_date"],
                            end_date=current["end_date"],
                            description=current["description"],
                            source="experience section",
                        )
                    )
                    current = {"company": None, "job_title": None, "location": None, "start_date": None, "end_date": None, "description": None}
                    continue
            if line and not re.match(r"^(?:[A-Z][a-z]+\s+){1,4}$", line):
                if not current["job_title"]:
                    current["job_title"] = line
                else:
                    current["description"] = (current["description"] or "") + (" " + line if current["description"] else line)
        if current["job_title"] or current["company"]:
            entries.append(
                ExperienceEntry(
                    company=current["company"],
                    job_title=current["job_title"],
                    location=current["location"],
                    start_date=current["start_date"],
                    end_date=current["end_date"],
                    description=current["description"],
                    source="experience section",
                )
            )
        return entries

    def _parse_projects(self, lines: list[str]) -> list[ProjectEntry]:
        entries: list[ProjectEntry] = []
        if not lines:
            return entries
        for line in lines:
            if not line:
                continue
            if "|" in line:
                parts = [part.strip() for part in line.split("|")]
                name = parts[0].strip()
                technologies = [item.strip() for item in parts[1].split(",")] if len(parts) > 1 else []
                url = None
                if len(parts) > 2:
                    url = parts[2].strip() if re.match(r"https?://", parts[2].strip()) else None
                entries.append(
                    ProjectEntry(
                        name=name,
                        description="",
                        technologies=[tech for tech in technologies if tech],
                        url=url,
                        start_date=None,
                        end_date=None,
                        source="projects section",
                    )
                )
            elif re.search(r"https?://", line):
                continue
            else:
                if entries:
                    entries[-1].description = (entries[-1].description or "") + (" " + line if entries[-1].description else line)
        return entries

    def _first_match(self, pattern: str, text: str) -> str | None:
        match = re.search(pattern, text, re.IGNORECASE)
        if match is None:
            return None
        return match.group(0)

    def _normalize_url(self, url: str | None, kind: str) -> str | None:
        if url is None:
            return None
        if kind == "linkedin" and not url.startswith("https://"):
            return f"https://{url}"
        if kind == "github" and not url.startswith("https://"):
            return f"https://{url}"
        if kind == "portfolio" and not url.startswith("https://"):
            return f"https://{url}"
        return url

    def _parse_date_range(self, raw: str) -> tuple[str | None, str | None]:
        value = raw.strip()
        if not value:
            return None, None
        if value.lower() in {"present", "current", "ongoing"}:
            return None, None
        if "-" in value:
            parts = [part.strip() for part in value.split("-")]
            if len(parts) == 2:
                return parts[0], None
        match = re.search(r"(\d{4})\s*(?:-|–|to)?\s*(\d{4}|Present|Current|Ongoing)?", value, re.IGNORECASE)
        if match:
            start = match.group(1)
            end = match.group(2)
            if end and end.lower() not in {"present", "current", "ongoing"}:
                return start, end
            return start, None
        return value, None
