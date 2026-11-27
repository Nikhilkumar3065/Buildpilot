import os
import base64
import requests
from urllib.parse import quote
from dotenv import load_dotenv

load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_OWNER = os.getenv("GITHUB_OWNER")
GITHUB_REPO = os.getenv("GITHUB_REPO")

GITHUB_API_URL = "https://api.github.com"


def get_github_headers():
    if not GITHUB_TOKEN:
        raise ValueError("GitHub token is missing.")

    return {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def validate_ai_branch(branch_name):
    if not isinstance(branch_name, str):
        raise ValueError("Branch name must be text.")

    if not branch_name.startswith("ai/"):
        raise ValueError(
            "AI operations are allowed only on ai/ branches."
        )

    if (
        len(branch_name) > 240
        or branch_name.endswith("/")
        or branch_name.endswith(".")
        or "//" in branch_name
        or ".." in branch_name.split("/")
        or any(char in branch_name for char in " ~^:?*[\\")
        or branch_name.startswith("/")
        or branch_name.endswith(".lock")
    ):
        raise ValueError("Invalid branch name.")


def validate_file_path(file_path):
    if not isinstance(file_path, str) or not file_path:
        raise ValueError("Invalid file path.")

    if (
        file_path.startswith("/")
        or "\\" in file_path
        or any(part in ("", ".", "..") for part in file_path.split("/"))
    ):
        raise ValueError("Invalid file path.")


def get_repository_info():
    if not GITHUB_OWNER or not GITHUB_REPO:
        raise ValueError("GitHub repository configuration is missing.")

    url = (
        f"{GITHUB_API_URL}/repos/"
        f"{GITHUB_OWNER}/{GITHUB_REPO}"
    )

    response = requests.get(
        url,
        headers=get_github_headers(),
        timeout=30,
    )

    if not response.ok:
        raise Exception(
            f"GitHub API Error {response.status_code}: "
            f"{response.text}"
        )

    return response.json()


def read_file(file_path, branch="main"):
    validate_file_path(file_path)

    if branch != "main":
        validate_ai_branch(branch)

    encoded_path = quote(file_path, safe="/")

    url = (
        f"{GITHUB_API_URL}/repos/"
        f"{GITHUB_OWNER}/{GITHUB_REPO}/contents/{encoded_path}"
    )

    response = requests.get(
        url,
        headers=get_github_headers(),
        params={"ref": branch},
        timeout=30,
    )

    if response.status_code == 404:
        raise FileNotFoundError(
            f"File not found: {file_path}"
        )

    if not response.ok:
        raise Exception(
            f"GitHub API Error {response.status_code}: "
            f"{response.text}"
        )

    data = response.json()

    if data.get("type") != "file":
        raise ValueError("The requested path is not a file.")

    content = base64.b64decode(
        data["content"]
    ).decode("utf-8")

    return content


def create_branch(branch_name, base_branch="main"):

    validate_ai_branch(branch_name)

    # Allow only main or a valid AI branch as the source.
    if base_branch != "main":
        validate_ai_branch(base_branch)

    if branch_name == base_branch:
        raise ValueError(
            "New branch and base branch must be different."
        )

    headers = get_github_headers()

    encoded_base = quote(base_branch, safe="/")

    base_url = (
        f"{GITHUB_API_URL}/repos/"
        f"{GITHUB_OWNER}/{GITHUB_REPO}/"
        f"git/ref/heads/{encoded_base}"
    )

    base_response = requests.get(
        base_url,
        headers=headers,
        timeout=30,
    )

    if not base_response.ok:
        raise Exception(
            f"Could not read base branch {base_branch}: "
            f"{base_response.status_code}: "
            f"{base_response.text}"
        )

    base_sha = base_response.json()["object"]["sha"]

    create_url = (
        f"{GITHUB_API_URL}/repos/"
        f"{GITHUB_OWNER}/{GITHUB_REPO}/git/refs"
    )

    response = requests.post(
        create_url,
        headers=headers,
        json={
            "ref": f"refs/heads/{branch_name}",
            "sha": base_sha,
        },
        timeout=30,
    )

    if not response.ok:
        raise Exception(
            f"Branch creation failed: "
            f"{response.status_code}: {response.text}"
        )

    return response.json()


def commit_and_push(file_path, content, branch_name, commit_message):
    validate_ai_branch(branch_name)
    validate_file_path(file_path)

    if not isinstance(content, str):
        raise ValueError("File content must be text.")

    if not commit_message or not commit_message.strip():
        raise ValueError("Commit message is required.")

    headers = get_github_headers()
    encoded_path = quote(file_path, safe="/")

    file_url = (
        f"{GITHUB_API_URL}/repos/"
        f"{GITHUB_OWNER}/{GITHUB_REPO}/contents/{encoded_path}"
    )

    # Check whether the file already exists on the AI branch.
    existing_response = requests.get(
        file_url,
        headers=headers,
        params={"ref": branch_name},
        timeout=30,
    )

    file_sha = None

    if existing_response.status_code == 200:
        existing_data = existing_response.json()

        if existing_data.get("type") != "file":
            raise ValueError("The requested path is not a file.")

        file_sha = existing_data["sha"]

    elif existing_response.status_code != 404:
        raise Exception(
            f"Could not check existing file: "
            f"{existing_response.status_code}: "
            f"{existing_response.text}"
        )

    # Encode the new file content.
    encoded_content = base64.b64encode(
        content.encode("utf-8")
    ).decode("utf-8")

    payload = {
        "message": commit_message,
        "content": encoded_content,
        "branch": branch_name,
    }

    # Include SHA when updating an existing file.
    if file_sha:
        payload["sha"] = file_sha

    response = requests.put(
        file_url,
        headers=headers,
        json=payload,
        timeout=30,
    )

    if not response.ok:
        raise Exception(
            f"Commit and push failed: "
            f"{response.status_code}: {response.text}"
        )

    return response.json()
def open_pull_request(
    branch_name,
    title,
    body,
    base_branch="main"
):

    validate_ai_branch(branch_name)

    if base_branch != "main":
        validate_ai_branch(base_branch)

    if branch_name == base_branch:
        raise ValueError(
            "Pull request head and base must be different."
        )

    if not title or not title.strip():
        raise ValueError(
            "Pull request title is required."
        )

    headers = get_github_headers()

    url = (
        f"{GITHUB_API_URL}/repos/"
        f"{GITHUB_OWNER}/{GITHUB_REPO}/pulls"
    )

    payload = {
        "title": title,
        "body": body,
        "head": branch_name,
        "base": base_branch,
    }

    response = requests.post(
        url,
        headers=headers,
        json=payload,
        timeout=30,
    )

    if not response.ok:
        raise Exception(
            f"Pull request creation failed: "
            f"{response.status_code}: {response.text}"
        )

    return response.json()