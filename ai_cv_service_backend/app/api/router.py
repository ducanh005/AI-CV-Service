from fastapi import APIRouter

from app.api.v1.endpoints import ai, applications, auth, companies, cvs, integrations, interviews, jobs, users

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(companies.router, prefix="/companies", tags=["Companies"])
api_router.include_router(jobs.router, prefix="/jobs", tags=["Jobs"])
api_router.include_router(cvs.router, prefix="/cvs", tags=["CV"])
api_router.include_router(ai.router, prefix="/ai", tags=["AI"])
api_router.include_router(applications.router, prefix="/applications", tags=["Applications"])
api_router.include_router(interviews.router, prefix="/interviews", tags=["Interviews"])
api_router.include_router(integrations.router, prefix="/integrations", tags=["Integrations"])
