from fastapi import APIRouter
from api.routes.pr_review import pr_review


api_version_one = APIRouter(prefix="/api/v1")
api_version_one.include_router(pr_review)