
from core.github_service import (
    list_files,
    read_file,
    create_branch,
    commit_and_push,
    open_pull_request,
    validate_ai_branch,
)


# ==========================================
# TOOLS AVAILABLE TO BUILDPILOT AI
# ==========================================

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": (
                "Discover files and directories in the "
                "demo repository. Use this tool before "
                "reading or modifying existing source files."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "branch": {
                        "type": "string",
                        "description": (
                            "Authorized branch to inspect. "
                            "Defaults to the assigned base branch."
                        )
                    },
                    "directory": {
                        "type": "string",
                        "description": (
                            "Optional directory path. "
                            "Use an empty string for the "
                            "entire repository."
                        )
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": (
                "Read a file from the demo repository "
                "using an authorized branch."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path of the file to read."
                    },
                    "branch": {
                        "type": "string",
                        "description": (
                            "Authorized branch to read from. "
                            "Defaults to the assigned base branch."
                        )
                    }
                },
                "required": ["file_path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_branch",
            "description": (
                "Create a new AI branch from the "
                "backend-assigned base branch."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "branch_name": {
                        "type": "string",
                        "description": (
                            "Exact assigned branch name "
                            "beginning with ai/."
                        )
                    }
                },
                "required": ["branch_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "commit_and_push",
            "description": (
                "Create or update a file and commit "
                "it to the assigned AI branch."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string"
                    },
                    "content": {
                        "type": "string"
                    },
                    "branch_name": {
                        "type": "string"
                    },
                    "commit_message": {
                        "type": "string"
                    }
                },
                "required": [
                    "file_path",
                    "content",
                    "branch_name",
                    "commit_message"
                ]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "open_pull_request",
            "description": (
                "Open a pull request from the assigned "
                "AI branch into the backend-assigned "
                "base branch."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "branch_name": {
                        "type": "string"
                    },
                    "title": {
                        "type": "string"
                    },
                    "body": {
                        "type": "string"
                    }
                },
                "required": [
                    "branch_name",
                    "title",
                    "body"
                ]
            }
        }
    }
]


# ==========================================
# TOOL EXECUTION ENGINE
# ==========================================

def execute_tool(
    tool_name,
    arguments,
    required_branch=None,
    base_branch="main"
):
    """
    Execute an AI-requested GitHub tool.

    required_branch:
        The exact AI branch assigned by Django.

    base_branch:
        The authorized source branch and PR target.

    Normal development uses main as the base.

    Bug fixing may use the original task branch
    when its pull request has not been merged.
    """

    if not isinstance(arguments, dict):
        raise ValueError(
            "Tool arguments must be a dictionary."
        )

    # ==========================================
    # VALIDATE BACKEND-ASSIGNED BASE BRANCH
    # ==========================================

    if base_branch != "main":

        validate_ai_branch(base_branch)

        if required_branch is None:
            raise ValueError(
                "An assigned destination branch is required "
                "when using a non-main base branch."
            )

    # ==========================================
    # VALIDATE ASSIGNED DESTINATION BRANCH
    # ==========================================

    if required_branch is not None:

        validate_ai_branch(required_branch)

        if required_branch == base_branch:
            raise ValueError(
                "Destination branch and base branch "
                "must be different."
            )

    # AI cannot override the backend-selected base.

    if "base_branch" in arguments:
        raise ValueError(
            "AI cannot select or override the base branch."
        )

    # ==========================================
    # VALIDATE READ OPERATIONS
    # ==========================================

    read_tools = {
        "list_files",
        "read_file"
    }

    if tool_name in read_tools:

        branch = arguments.get(
            "branch",
            base_branch
        )

        if not isinstance(branch, str):
            raise ValueError(
                "Branch name must be text."
            )

        allowed_branches = {
            "main",
            base_branch
        }

        if required_branch is not None:
            allowed_branches.add(required_branch)

        if branch not in allowed_branches:
            raise ValueError(
                "Reading from this branch is not allowed."
            )

    # ==========================================
    # LIST REPOSITORY FILES
    # ==========================================

    if tool_name == "list_files":

        return list_files(
            branch=branch,
            directory=arguments.get(
                "directory",
                ""
            )
        )

    # ==========================================
    # READ FILE
    # ==========================================

    if tool_name == "read_file":

        return read_file(
            file_path=arguments["file_path"],
            branch=branch
        )

    # ==========================================
    # VALIDATE WRITE OPERATIONS
    # ==========================================

    write_tools = {
        "create_branch",
        "commit_and_push",
        "open_pull_request"
    }

    if tool_name in write_tools:

        if required_branch is None:
            raise ValueError(
                "An assigned AI branch is required "
                "for write operations."
            )

        branch_name = arguments["branch_name"]

        validate_ai_branch(branch_name)

        if branch_name != required_branch:
            raise ValueError(
                "AI can operate only on its "
                "assigned branch."
            )

        if branch_name == base_branch:
            raise ValueError(
                "AI cannot modify the assigned base branch."
            )

    # ==========================================
    # CREATE BRANCH
    # ==========================================

    if tool_name == "create_branch":

        return create_branch(
            branch_name=arguments["branch_name"],
            base_branch=base_branch
        )

    # ==========================================
    # COMMIT AND PUSH
    # ==========================================

    if tool_name == "commit_and_push":

        return commit_and_push(
            file_path=arguments["file_path"],
            content=arguments["content"],
            branch_name=arguments["branch_name"],
            commit_message=arguments["commit_message"]
        )

    # ==========================================
    # OPEN PULL REQUEST
    # ==========================================

    if tool_name == "open_pull_request":

        return open_pull_request(
            branch_name=arguments["branch_name"],
            title=arguments["title"],
            body=arguments["body"],
            base_branch=base_branch
        )

    # ==========================================
    # REJECT UNSUPPORTED TOOLS
    # ==========================================

    raise ValueError(
        f"Unknown tool: {tool_name}"
    )
