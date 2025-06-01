from fastapi import FastAPI, Request, HTTPException, Response, status
import uvicorn
from fastapi.responses import ORJSONResponse
from api.routes import api_version_one

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




if __name__ == '__main__':
    uvicorn.run('main:app', host="127.0.0.1", port=3001, reload=True)

