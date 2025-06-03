# PR review agent

PR review agent is an AI-powered code review assistant that leverages Google's Gemini LLM to analyze GitHub Pull Requests and repositories. It automatically reviews code changes, identifies issues, and provides constructive feedback by posting comments directly to pull requests or creating GitHub issues.

![image](https://github.com/Benji918/PR-review-agent/blob/main/Prompt%20Title_%C2%A0Generate%20Application%20Flow%20Diagram%20for%20Simple%20PR%20Review%20Agent%20-%20visual%20selection.png)

## Features

- 🔍 **Pull Request Analysis**: Automatically reviews PR diffs and posts feedback as comments
- 📊 **Repository Scanning**: Analyzes entire repositories to identify code quality issues
- 🚀 **Issue Creation**: Generates GitHub issues from analysis findings
- 🛠️ **Customizable Analysis**: Focus on bugs, performance issues, security vulnerabilities, and more
- 💬 **Clear Feedback**: Well-formatted markdown outlsldldput with actionable recommendations

## Getting Started

### Prerequisites

- Python 3.8+
- GitHub account with access to target repositories
- Google Cloud account (for Gemini API access)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/Benji918/PR-review-agent.git
   cd PR-review-agent
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file in the project root with the following variables:
   ```
   GITHUB_PERSONAL_ACCESS_TOKEN=your_github_token
   GEMINI_API_KEY=your_gemini_api_key
   ```

### Setting Up API Keys

#### GitHub Personal Access Token

1. Go to your GitHub account settings: https://github.com/settings/tokens
2. Click "Generate new token" (classic)
3. Give it a descriptive name (e.g., "CodeReviewBot")
4. Select the following scopes:
   - `repo` (Full control of private repositories) or `public_repo` (for public repositories only)
   - `read:org` (if working with organization repositories)
5. Click "Generate token"
6. Copy the token and add it to your `.env` file

#### Gemini API Key

1. Visit the Google AI Studio: https://aistudio.google.com/
2. Create or sign in to your Google Cloud account
3. Navigate to the API Keys section
4. Create a new API key
5. Copy the key and add it to your `.env` file

## Usage

### Running the Application

Start the FastAPI server:

```bash
uvicorn main:app --reload
```

The server will be available at `http://localhost:8000`.

### API Endpoints

#### Pull Request Review

To analyze a pull request and post feedback as a comment:

```
GET /fetch_pr_diff?owner={OWNER}&repo={REPO}&pr_number={PR_NUMBER}
```

**Example**:
```
GET /fetch_pr_diff?owner=yourusername&repo=yourproject&pr_number=42
```

#### Repository Analysis

To analyze an entire repository and create issues:

```
POST /analyze-repo?owner={OWNER}&repo={REPO}
```

**Example**:
```
POST /analyze-repo?owner=yourusername&repo=yourproject
```

## Configuration

You can customize the behavior of CodeReviewBot by modifying the following parameters:

### PR Review Customization

Edit the prompt in `analyze_diff_with_gemini()` to focus on specific aspects of code review:

```python
prompt = f"""
You are a helpful and critical code reviewer powered by Google Gemini 2.0 Flash.
Review the following GitHub Pull Request diff. Provide constructive feedback focusing on:
- Potential bugs or logical errors
- Code clarity and readability
- Adherence to common best practices
- Possible performance issues
- Security vulnerabilities
- Suggestions for improvement

# Add or remove focus areas as needed
"""
```

### Repository Analysis Customization

Adjust file filtering in `fetch_repo_contents()` to include or exclude specific file types:

```python
# Skip binary files, large files, and files we probably don't want to analyze
if (item['size'] < 100000 and 
    not item['name'].endswith(('.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico', 
                              '.woff', '.woff2', '.ttf', '.eot', '.pdf', '.zip', 
                              '.tar.gz', '.min.js', '.min.css'))):
    # Process file
```


## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

