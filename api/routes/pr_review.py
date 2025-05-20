from fastapi import status, Response, Request, HTTPException
from fastapi.responses import ORJSONResponse
from fastapi import APIRouter
import requests
import os

pr_review = APIRouter(prefix="/pr_review", tags=["PR-review-agent"])


@pr_review.get("/", status_code=status.HTTP_200_OK)
async def list_pr(request: Request, response: Response):
    owner = 'Benji918'
    repo = 'https://github.com/Benji918/PR-review-agent'
    url = f'https://api.github.com/repos/{owner}/{repo}/pulls'
    header = {
        'Accept': "application/vnd.github.v3.diff",
        'Authorization': f'Bearer {os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN")}',
      },
    response = requests.get(url, header)
    print(response.json())
    return ORJSONResponse(response.json())
