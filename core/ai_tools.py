from core.github_service import (
    read_file,
    create_branch,
    commit_and_push,
    open_pull_request,
)


# Tools available to BuildPilot AI
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read a file from the demo repository.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path of the file to read."
                    },
                    "branch": {
                        "type": "string",
                        "description": "Branch name. Defaults to main."
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
            "description": "Create a new AI branch from main.",
            "parameters": {
                "type": "object",
                "properties": {
                    "branch_name": {
                        "type": "string",
                        "description": "New branch name beginning with ai/."
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
            "description": "Create or update a file and commit it to an AI branch.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string"},
                    "content": {"type": "string"},
                    "branch_name": {"type": "string"},
                    "commit_message": {"type": "string"}
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
            "description": "Open a pull request from an AI branch into main.",
            "parameters": {
                "type": "object",
                "properties": {
                    "branch_name": {"type": "string"},
                    "title": {"type": "string"},
                    "body": {"type": "string"}
                },
                "required": ["branch_name", "title", "body"]
            }
        }
    }
]


def execute_tool(tool_name, arguments):
    """Execute an AI-requested GitHub tool."""

    if not isinstance(arguments, dict):
        raise ValueError("Tool arguments must be a dictionary.")

    if tool_name == "read_file":
        return read_file(
            file_path=arguments["file_path"],
            branch=arguments.get("branch", "main")
        )

    if tool_name == "create_branch":
        return create_branch(
            branch_name=arguments["branch_name"]
        )

    if tool_name == "commit_and_push":
        return commit_and_push(
            file_path=arguments["file_path"],
            content=arguments["content"],
            branch_name=arguments["branch_name"],
            commit_message=arguments["commit_message"]
        )

    if tool_name == "open_pull_request":
        return open_pull_request(
            branch_name=arguments["branch_name"],
            title=arguments["title"],
            body=arguments["body"]
        )

    raise ValueError(f"Unknown tool: {tool_name}")
