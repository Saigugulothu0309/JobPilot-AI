from fastapi import FastAPI

from app.api.router import api_router
from app.core.errors import ApplicationError, application_error_handler


def create_application() -> FastAPI:
    """Create the JobPilot AI HTTP application."""
    application = FastAPI(title="JobPilot AI", version="0.1.0")
    application.add_exception_handler(ApplicationError, application_error_handler)
    application.include_router(api_router)

    @application.get("/health")
    def health_check() -> dict[str, str]:
        """Return a non-sensitive service health response."""
        return {"status": "healthy", "service": "jobpilot-ai"}

    return application


app = create_application()
