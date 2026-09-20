"""Top-level HTTP routing registration."""

from fastapi import APIRouter

from app.modules.activity.api import router as activity_router
from app.modules.application.api import router as application_router
from app.modules.auth.api import router as auth_router
from app.modules.feedback.api import router as feedback_router
from app.modules.job.api import router as job_router
from app.modules.notification.api import router as notification_router
from app.modules.profile.api import router as profile_router
from app.modules.resume.api import router as resume_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(activity_router)
api_router.include_router(application_router)
api_router.include_router(auth_router)
api_router.include_router(feedback_router)
api_router.include_router(job_router)
api_router.include_router(notification_router)
api_router.include_router(profile_router)
api_router.include_router(resume_router)
