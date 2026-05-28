from fastapi import APIRouter

from app.api.v1.endpoints import clients, job_search, job_title, salary, search

api_v1_router = APIRouter()

api_v1_router.include_router(job_search.router)
api_v1_router.include_router(job_title.router)
api_v1_router.include_router(salary.router)
api_v1_router.include_router(search.router)
api_v1_router.include_router(clients.router, prefix="/clients", tags=["clients"])
