from fastapi import FastAPI, Request, HTTPException, Response, status
import uvicorn
from fastapi.responses import ORJSONResponse
from api.services.pr_review_service import fetch_pull_request_diff_with_app
from api.routes import api_version_one
import os
import requests

app = FastAPI(
    title="PR-review-agent",
    description="A simple agent for PR reviews",
    version="1.0",
    default_response_class=ORJSONResponse,

)

app.include_router(api_version_one)

@app.get("/", tags=["Home"])
async def get_root(request: Request):
    """Base endpoint"""
    return "Welcome to PR-review-agent API",

@app.post("/webhook")
async def github_webhook(request: Request):
    """Webhook to automatically review PRs when opened"""
    try:
        payload = await request.json()
        raw = await request.body()
        print(raw)
        print(payload)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid JSON body: {e}")

    # Check if it's a PR opened or reopened event
    if (payload.get('action') == 'opened' or payload.get('action') == 'reopened'  and  'pull_request' in payload):
        owner = payload['repository']['owner']['login']
        repo_name = payload['repository']['name']
        pr_number = payload['pull_request']['number']

        try:
            await fetch_pull_request_diff_with_app(owner, repo_name, pr_number)
            return ORJSONResponse({"status": "success", "message": "PR reviewed automatically"})
        except Exception as e:
            print(e)
            return ORJSONResponse({"status": "error", "message": str(e)}, status_code=500)

    return ORJSONResponse({"status": "ok"})



if __name__ == '__main__':
    host = "0.0.0.0" if os.getenv("ENVIRONMENT") == "prod" else "127.0.0.1"
    reload = os.getenv("ENVIRONMENT") != "prod"
    uvicorn.run('main:app', host=host, port=3001, reload=reload)
