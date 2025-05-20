import requests
from fastapi import HTTPException
import os
from google import genai
from dotenv import load_dotenv


load_dotenv('.env')


client = genai.Client(api_key='AIzaSyBWLwRoo7dakR1Z2S5Feyjc8K2-jRhlvHc')

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
You are a helpful and critical code reviewer powered by Google Gemini 2.0 Flash.
Review the following GitHub Pull Request diff. Provide constructive feedback focusing on:
- Potential bugs or logical errors
- Code clarity and readability
- Adherence to common best practices
- Possible performance issues
- Security vulnerabilities
- Suggestions for improvement

Analyze the changes file by file where applicable. If there are no significant issues or suggestions, state that clearly.
Format your review in Markdown. Use bullet points, code blocks, and bold text to make it easy to read. Make the review 
concise, short, and to the point. Do not include the actual code changes to the PR review

## Pull Request Diff:

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
    env = os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN")
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