import requests
from fastapi import HTTPException
import os
from google import genai
from dotenv import load_dotenv


load_dotenv('.env')


api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)


github_token = os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN")
github_headers = {
    'Accept': 'application/vnd.github+json',
    'Authorization': f'Bearer {github_token}',
    'Content-Type': 'application/json',
    'X-GitHub-Api-Version': '2022-11-28'
}



async def get_pr(owner, repo):
    # owner = 'Benji918'
    # repo = 'PR-review-agent'
    url = f'https://api.github.com/repos/{owner}/{repo}/pulls?state=all'
    response = requests.get(url, headers=github_headers)
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
    data = {'body': comment}
    response = requests.post(url, headers=github_headers, json=data)

    if not response.ok:
        detail = {"message": response.text}
        raise HTTPException(status_code=response.status_code, detail=detail)

    return response.json()


#---------------------------ANALYSE REPOSITORY CONTENT TO POST ISSUES---------------------------#
async def fetch_repo_contents(owner, repo, path=""):
    """Recursively fetch all files in a repository"""
    contents_url = f'https://api.github.com/repos/{owner}/{repo}/contents/{path}'
    response = requests.get(contents_url, headers=github_headers)

    if not response.ok:
        print(f"Error fetching repo contents: {response.status_code} - {response.text}")
        return []

    items = response.json()


    if not isinstance(items, list):
        items = [items]

    all_files = []

    for item in items:
        if item['type'] == 'file':

            if (item['size'] < 100000 and
                    not item['name'].endswith(('.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico',
                                               '.woff', '.woff2', '.ttf', '.eot', '.pdf', '.zip',
                                               '.tar.gz', '.min.js', '.min.css'))):
                file_content = fetch_file_content(item['download_url'])
                all_files.append({
                    'name': item['path'],
                    'content': file_content
                })
        elif item['type'] == 'dir':
            all_files.extend(await fetch_repo_contents(owner, repo, item['path']))

    return all_files

def fetch_file_content(url):
    """Fetch content of a file from GitHub"""
    response = requests.get(url)
    if response.ok:
        return response.text
    return None

async def analyze_repo_with_gemini(files, owner, repo):
    """Analyze repository files with Gemini"""
    file_groups = {}

    for file in files:
        extension = os.path.splitext(file['name'])[1]
        if extension not in file_groups:
            file_groups[extension] = []
        file_groups[extension].append(file)

    issues = []

    # Analyze each group separately
    for ext, group_files in file_groups.items():
        # Skip if empty group
        if not group_files:
            continue

        # Prepare files for analysis - limit content length to avoid token limits
        analysis_files = []
        for file in group_files[:10]:  # Limit to 10 files per group to avoid context limits
            # Truncate very large files
            content = file['content']
            if content and len(content) > 10000:
                content = content[:10000] + "\n... [content truncated for length] ...\n"

            analysis_files.append({
                'name': file['name'],
                'content': content
            })

        # Create analysis prompt
        prompt = f"""
        You are a code quality expert analyzing a GitHub repository.

        Repository: {owner}/{repo}
        File type: {ext}

        I'll provide you with several {ext} files from this repository. Please analyze them for:
        1. Code quality issues
        2. Security vulnerabilities
        3. Performance problems
        4. Best practice violations
        5. Architecture concerns

        For each significant issue found, format your response as follows:

        ## Issue Title: [Brief descriptive title]
        - **Severity**: [High/Medium/Low]
        - **File**: [Filename]
        - **Description**: [Detailed explanation of the issue]
        - **Recommendation**: [How to fix]

        Only include actionable issues that should be addressed. Focus on the most important issues first.

        Here are the files:

        """

        for file in analysis_files:
            prompt += f"\n\n### {file['name']}\n```\n{file['content']}\n```"

        try:
            response = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
            raw_analysis = response.text


            issue_sections = raw_analysis.split("## Issue Title:")

            for section in issue_sections[1:]:
                lines = section.strip().split("\n")
                issue_title = lines[0].strip()

                # Extract severity, file, description and recommendation
                severity = "Medium"  # Default
                file_name = ""
                description = ""
                recommendation = ""

                for line in lines[1:]:
                    if "**Severity**:" in line:
                        severity = line.split("**Severity**:")[1].strip()
                    elif "**File**:" in line:
                        file_name = line.split("**File**:")[1].strip()
                    elif "**Description**:" in line:
                        desc_start = lines.index(line)
                        for i in range(desc_start + 1, len(lines)):
                            if lines[i].startswith("- **Recommendation"):
                                break
                            description += lines[i] + "\n"
                    elif "**Recommendation**:" in line:
                        rec_start = lines.index(line)
                        for i in range(rec_start + 1, len(lines)):
                            if i >= len(lines) or lines[i].startswith("## ") or lines[i].startswith("- **"):
                                break
                            recommendation += lines[i] + "\n"

                # Create structured issue
                issues.append({
                    "title": issue_title,
                    "severity": severity,
                    "file": file_name,
                    "description": description.strip(),
                    "recommendation": recommendation.strip()
                })

        except Exception as e:
            print(f"Error analyzing files with Gemini: {str(e)}")

    return issues

async def create_github_issues(owner, repo, issues):
    """Create GitHub issues based on analysis"""
    created_issues = []

    for issue in issues:
        # Format issue body
        body = f"""## Code Analysis Issue

**Severity**: {issue['severity']}
**File**: {issue['file']}

### Description
{issue['description']}

### Recommendation
{issue['recommendation']}

---
*This issue was automatically generated by code analysis.*
"""

        # Use labels based on severity
        labels = ["code-analysis"]
        if "High" in issue['severity']:
            labels.append("high-priority")
        elif "Medium" in issue['severity']:
            labels.append("medium-priority")
        else:
            labels.append("low-priority")

        # Create the issue
        issue_data = {
            "title": issue['title'],
            "body": body,
            "labels": labels
        }

        url = f'https://api.github.com/repos/{owner}/{repo}/issues'
        response = requests.post(url, headers=github_headers, json=issue_data)

        if response.ok:
            created_issues.append(response.json())
        else:
            print(f"Error creating issue: {response.status_code} - {response.text}")

    return created_issues
