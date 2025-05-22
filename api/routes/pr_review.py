import os

import requests
from fastapi import status, Response, Request, HTTPException
from fastapi.responses import ORJSONResponse, PlainTextResponse
from fastapi import APIRouter
from starlette.responses import JSONResponse

from api.services.pr_review_service import get_pr, analyze_diff_with_gemini, pr_comment, fetch_repo_contents, \
    analyze_repo_with_gemini, create_github_issues

pr_review = APIRouter(prefix="/pr_review", tags=["PR-review-agent"])


@pr_review.get("/", summary="List PRs", status_code=status.HTTP_200_OK)
async def list_pr(request: Request,
                  response: Response,
                  owner: str,
                  repo: str,):

    response = await get_pr(owner=owner, repo=repo)
    return ORJSONResponse(response.json())


@pr_review.get('/fetch_pr_diff', summary="Fetch specific PR diff")
async def fetch_pull_request_diff(
        owner: str,
        repo: str,
        pr_number: int
):

    api_url = f'https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}'
    headers = {
        'Accept': 'application/vnd.github+json',
        'Authorization': f'Bearer {os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN")}'
    }


    pr_response = requests.get(api_url, headers)

    if not pr_response.ok:
        detail = {"message": pr_response.text}
        raise HTTPException(status_code=pr_response.status_code, detail=detail)

    pr_data = pr_response.json()


    diff_url = f'https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}/files'
    files_response = requests.get(diff_url, headers)

    if not files_response.ok:
        detail = {"message": files_response.text}
        raise HTTPException(status_code=files_response.status_code, detail=detail)

    files_data = files_response.json()


    changes = []
    for file in files_data:
        change = {
            "filename": file["filename"],
            "status": file["status"],
            "additions": file["additions"],
            "deletions": file["deletions"],
            "patch": file.get("patch", "")
        }
        changes.append(change)


    formatted_diff = {
        "pr_title": pr_data["title"],
        "pr_description": pr_data["body"],
        "changes": changes
    }

    analysis_result = await analyze_diff_with_gemini(formatted_diff)

    if isinstance(analysis_result, HTTPException):
        return JSONResponse(
            content={"error": f"Analysis failed: {analysis_result.detail}"},
            status_code=analysis_result.status_code
        )

    comment = await pr_comment(owner=owner, repo=repo, pr_number=pr_number, comment=analysis_result)


    return JSONResponse(content={'message': 'PR review completed!', 'result': comment})



#--------------ANALYZE REPOSITORY CONTENT TO POST ISSUES--------------#
@pr_review.get('/analyze_repository', summary="Analyze repository")
async def analyze_repository(owner: str, repo: str):
    """Endpoint to analyze a repository and create issues"""
    try:
        # Step 1: Fetch repository contents
        files = await fetch_repo_contents(owner, repo)

        if not files:
            return {"message": "No files found or error fetching repository"}

        # Step 2: Analyze with Gemini
        issues = await analyze_repo_with_gemini(files, owner, repo)

        # Step 3: Create GitHub issues
        created_issues = await create_github_issues(owner, repo, issues)

        return JSONResponse(
            content={
                "message": f"Analysis complete. Created {len(created_issues)} issues.",
                "issues": created_issues
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))




