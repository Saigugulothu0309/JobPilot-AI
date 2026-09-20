"""Authenticated candidate profile endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import get_db_session
from app.modules.auth.models import User
from app.modules.profile.schemas import (
    CareerPreferencesResponse,
    CareerPreferencesUpdateRequest,
    EducationCreateRequest,
    EducationResponse,
    EducationUpdateRequest,
    ExperienceCreateRequest,
    ExperienceResponse,
    ExperienceUpdateRequest,
    ProfileResponse,
    ProfileUpdateRequest,
    ProjectCreateRequest,
    ProjectResponse,
    ProjectUpdateRequest,
    SkillCreateRequest,
    SkillResponse,
    SkillUpdateRequest,
)
from app.modules.profile.service import (
    DuplicateProfessionalRecordError,
    ProfessionalRecordNotFoundError,
    ProfileNotFoundError,
    ProfileService,
)
from app.security.auth import get_current_user

router = APIRouter(prefix="/profile", tags=["profile"])


def _ensure_profile(session: Session, current_user: User) -> None:
    try:
        ProfileService(session).require_profile(current_user.id)
    except ProfileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("", response_model=ProfileResponse)
def get_profile(
    current_user: User = Depends(get_current_user), session: Session = Depends(get_db_session)
) -> ProfileResponse:
    profile = ProfileService(session).get(current_user.id)
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
    return ProfileResponse.model_validate(profile)


@router.put("", response_model=ProfileResponse)
def update_profile(
    payload: ProfileUpdateRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> ProfileResponse:
    profile = ProfileService(session).upsert(
        current_user.id, payload.model_dump(exclude_unset=True)
    )
    return ProfileResponse.model_validate(profile)


@router.get("/preferences", response_model=CareerPreferencesResponse)
def get_preferences(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> CareerPreferencesResponse:
    try:
        preferences = ProfileService(session).get_preferences(current_user.id)
    except ProfileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Preferences not found",
        ) from exc
    if preferences is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Preferences not found")
    return CareerPreferencesResponse.model_validate(preferences)


@router.put("/preferences", response_model=CareerPreferencesResponse)
def update_preferences(
    payload: CareerPreferencesUpdateRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> CareerPreferencesResponse:
    preferences = ProfileService(session).upsert_preferences(
        current_user.id, payload.model_dump()
    )
    return CareerPreferencesResponse.model_validate(preferences)


@router.get("/skills", response_model=list[SkillResponse])
def list_skills(
    current_user: User = Depends(get_current_user), session: Session = Depends(get_db_session)
) -> list[SkillResponse]:
    profile_service = ProfileService(session)
    try:
        skills = profile_service.list_skills(current_user.id)
    except ProfileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return [SkillResponse.model_validate(skill) for skill in skills]


@router.post("/skills", response_model=SkillResponse, status_code=status.HTTP_201_CREATED)
def create_skill(
    payload: SkillCreateRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> SkillResponse:
    profile_service = ProfileService(session)
    try:
        skill = profile_service.create_skill(current_user.id, payload.model_dump())
    except ProfileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except DuplicateProfessionalRecordError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return SkillResponse.model_validate(skill)


@router.put("/skills/{skill_id}", response_model=SkillResponse)
def update_skill(
    skill_id: UUID,
    payload: SkillUpdateRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> SkillResponse:
    profile_service = ProfileService(session)
    try:
        skill = profile_service.update_skill(
            current_user.id, skill_id, payload.model_dump(exclude_unset=True)
        )
    except ProfileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ProfessionalRecordNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except DuplicateProfessionalRecordError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return SkillResponse.model_validate(skill)


@router.delete("/skills/{skill_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_skill(
    skill_id: UUID,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> None:
    profile_service = ProfileService(session)
    try:
        profile_service.delete_skill(current_user.id, skill_id)
    except ProfileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ProfessionalRecordNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return None


@router.get("/education", response_model=list[EducationResponse])
def list_education(
    current_user: User = Depends(get_current_user), session: Session = Depends(get_db_session)
) -> list[EducationResponse]:
    profile_service = ProfileService(session)
    try:
        education = profile_service.list_education(current_user.id)
    except ProfileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return [EducationResponse.model_validate(item) for item in education]


@router.post("/education", response_model=EducationResponse, status_code=status.HTTP_201_CREATED)
def create_education(
    payload: EducationCreateRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> EducationResponse:
    profile_service = ProfileService(session)
    try:
        item = profile_service.create_education(current_user.id, payload.model_dump())
    except ProfileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return EducationResponse.model_validate(item)


@router.put("/education/{education_id}", response_model=EducationResponse)
def update_education(
    education_id: UUID,
    payload: EducationUpdateRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> EducationResponse:
    profile_service = ProfileService(session)
    try:
        item = profile_service.update_education(
            current_user.id, education_id, payload.model_dump(exclude_unset=True)
        )
    except ProfileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ProfessionalRecordNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return EducationResponse.model_validate(item)


@router.delete("/education/{education_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_education(
    education_id: UUID,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> None:
    profile_service = ProfileService(session)
    try:
        profile_service.delete_education(current_user.id, education_id)
    except ProfileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ProfessionalRecordNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return None


@router.get("/experience", response_model=list[ExperienceResponse])
def list_experience(
    current_user: User = Depends(get_current_user), session: Session = Depends(get_db_session)
) -> list[ExperienceResponse]:
    profile_service = ProfileService(session)
    try:
        experience = profile_service.list_experience(current_user.id)
    except ProfileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return [ExperienceResponse.model_validate(item) for item in experience]


@router.post("/experience", response_model=ExperienceResponse, status_code=status.HTTP_201_CREATED)
def create_experience(
    payload: ExperienceCreateRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> ExperienceResponse:
    profile_service = ProfileService(session)
    try:
        item = profile_service.create_experience(current_user.id, payload.model_dump())
    except ProfileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return ExperienceResponse.model_validate(item)


@router.put("/experience/{experience_id}", response_model=ExperienceResponse)
def update_experience(
    experience_id: UUID,
    payload: ExperienceUpdateRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> ExperienceResponse:
    profile_service = ProfileService(session)
    try:
        item = profile_service.update_experience(
            current_user.id, experience_id, payload.model_dump(exclude_unset=True)
        )
    except ProfileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ProfessionalRecordNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return ExperienceResponse.model_validate(item)


@router.delete("/experience/{experience_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_experience(
    experience_id: UUID,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> None:
    profile_service = ProfileService(session)
    try:
        profile_service.delete_experience(current_user.id, experience_id)
    except ProfileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ProfessionalRecordNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return None


@router.get("/projects", response_model=list[ProjectResponse])
def list_projects(
    current_user: User = Depends(get_current_user), session: Session = Depends(get_db_session)
) -> list[ProjectResponse]:
    profile_service = ProfileService(session)
    try:
        projects = profile_service.list_projects(current_user.id)
    except ProfileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return [ProjectResponse.model_validate(item) for item in projects]


@router.post("/projects", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(
    payload: ProjectCreateRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> ProjectResponse:
    profile_service = ProfileService(session)
    try:
        item = profile_service.create_project(current_user.id, payload.model_dump())
    except ProfileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return ProjectResponse.model_validate(item)


@router.put("/projects/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: UUID,
    payload: ProjectUpdateRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> ProjectResponse:
    profile_service = ProfileService(session)
    try:
        item = profile_service.update_project(
            current_user.id, project_id, payload.model_dump(exclude_unset=True)
        )
    except ProfileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ProfessionalRecordNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return ProjectResponse.model_validate(item)


@router.delete("/projects/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    project_id: UUID,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> None:
    profile_service = ProfileService(session)
    try:
        profile_service.delete_project(current_user.id, project_id)
    except ProfileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ProfessionalRecordNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return None
