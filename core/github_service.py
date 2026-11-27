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
        or any(
            part in ("", ".", "..")
            for part in file_path.split("/")
        )
    ):
        raise ValueError("Invalid file path.")


# ==========================================
# GET REPOSITORY INFORMATION
# ==========================================

def get_repository_info():
    if not GITHUB_OWNER or not GITHUB_REPO:
        raise ValueError(
            "GitHub repository configuration is missing."
        )

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


# ==========================================
# LIST REPOSITORY FILES
# ==========================================

def list_files(branch="main", directory=""):

    if not GITHUB_OWNER or not GITHUB_REPO:
        raise ValueError(
            "GitHub repository configuration is missing."
        )

    if branch != "main":
        validate_ai_branch(branch)

    if not isinstance(directory, str):
        raise ValueError("Directory must be text.")

    if directory:
        validate_file_path(directory)

    headers = get_github_headers()

    encoded_branch = quote(branch, safe="")

    # Retrieve the Git tree for the selected branch.

    url = (
        f"{GITHUB_API_URL}/repos/"
        f"{GITHUB_OWNER}/{GITHUB_REPO}/"
        f"git/trees/{encoded_branch}"
    )

    response = requests.get(
        url,
        headers=headers,
        params={"recursive": "1"},
        timeout=30,
    )

    if response.status_code == 404:
        raise FileNotFoundError(
            f"Branch or repository tree not found: {branch}"
        )

    if not response.ok:
        raise RuntimeError(
            f"GitHub file listing failed: "
            f"HTTP {response.status_code}"
        )

    data = response.json()

    tree = data.get("tree", [])

    files = []
    directories = []

    directory_prefix = (
        f"{directory}/" if directory else ""
    )

    directory_exists = not directory

    for item in tree:

        path = item.get("path", "")
        item_type = item.get("type", "")

        if not path:
            continue

        if path == directory and item_type == "tree":
            directory_exists = True

        # Return only files inside the requested directory.

        if directory_prefix:
            if not path.startswith(directory_prefix):
                continue

            directory_exists = True

        if item_type == "blob":
            files.append(path)

        elif item_type == "tree":
            directories.append(path)

    github_truncated = bool(
        data.get("truncated", False)
    )

    if not directory_exists and not github_truncated:
        raise FileNotFoundError(
            f"Directory not found: {directory}"
        )

    files.sort()
    directories.sort()

    # Limit output size to avoid excessive AI token usage.

    max_files = 500
    max_directories = 200

    total_files = len(files)
    total_directories = len(directories)

    output_truncated = (
        total_files > max_files
        or total_directories > max_directories
    )

    return {
        "branch": branch,
        "directory": directory or "/",
        "total_files": total_files,
        "total_directories": total_directories,
        "files": files[:max_files],
        "directories": directories[:max_directories],
        "truncated": (
            github_truncated or output_truncated
        ),
    }


# ==========================================
# READ REPOSITORY FILE
# ==========================================

def read_file(file_path, branch="main"):

    validate_file_path(file_path)

    if branch != "main":
        validate_ai_branch(branch)

    encoded_path = quote(file_path, safe="/")

    url = (
        f"{GITHUB_API_URL}/repos/"
        f"{GITHUB_OWNER}/{GITHUB_REPO}/"
        f"contents/{encoded_path}"
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
        raise ValueError(
            "The requested path is not a file."
        )

    content = base64.b64decode(
        data["content"]
    ).decode("utf-8")

    return content


# ==========================================
# CREATE AI BRANCH
# ==========================================

def create_branch(branch_name, base_branch="main"):

    validate_ai_branch(branch_name)

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


# ==========================================
# COMMIT AND PUSH FILE
# ==========================================

def commit_and_push(
    file_path,
    content,
    branch_name,
    commit_message
):

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
        f"{GITHUB_OWNER}/{GITHUB_REPO}/"
        f"contents/{encoded_path}"
    )

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
            raise ValueError(
                "The requested path is not a file."
            )

        file_sha = existing_data["sha"]

    elif existing_response.status_code != 404:

        raise Exception(
            f"Could not check existing file: "
            f"{existing_response.status_code}: "
            f"{existing_response.text}"
        )

    encoded_content = base64.b64encode(
        content.encode("utf-8")
    ).decode("utf-8")

    payload = {
        "message": commit_message,
        "content": encoded_content,
        "branch": branch_name,
    }

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


# ==========================================
# OPEN PULL REQUEST
# ==========================================

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
