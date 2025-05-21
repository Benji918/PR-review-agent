import requests
from fastapi import HTTPException
import os
from google import genai
from dotenv import load_dotenv


load_dotenv('.env')


client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

async def get_pr(owner, repo):
    # owner = 'Benji918'
    # repo = 'PR-review-agent'
    url = f'https://api.github.com/repos/{owner}/{repo}/pulls?state=all'
    header = {
            'Accept': "application/vnd.github+json",
            'Authorization': f'Bearer {os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN")}',
            "X-GitHub-Api-Version": "2022-11-28"
    }
    response = requests.get(url, header)
    return response


async def analyze_diff_with_gemini(diff_content):
    if diff_content is None:
        return HTTPException(status_code=404, detail="PR diff not found")

    try:
        prompt = f"""
        You’re a Google engineer reviewing this PR. Scan the diff below and give me clear, actionable feedback on:

        - Bugs & logic errors 
        - Readability & style   
        -  Best practices   
        -  Performance hotspots   
        -  Security risks 

        Keep it very short, use Markdown with bold headings and bullet points, and skip pasting the actual diff.

        ## Diff
        ```diff
        {diff_content}
        """

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )
        return response.text

    except Exception as e:
        return HTTPException(status_code=500, detail=str(e))

async def pr_comment(owner, repo, pr_number, comment):
    url = f'https://api.github.com/repos/{owner}/{repo}/issues/{pr_number}/comments'
    headers = {
        'Accept': 'application/vnd.github+json',
        'Authorization': f'Bearer {os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN")}',
        "Content-Type": "application/json",
        'X-GitHub-Api-Version': '2022-11-28'
    }
    data = {'body': comment}
    response = requests.post(url, headers=headers, json=data)

    if not response.ok:
        detail = {"message": response.text}
        raise HTTPException(status_code=response.status_code, detail=detail)

    return response.json()