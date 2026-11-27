import os
import json
import requests

from dotenv import load_dotenv

from core.ai_tools import TOOLS, execute_tool

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

API_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL_NAME = "openrouter/free"


def get_ai_response(messages):
    if not OPENROUTER_API_KEY:
        raise ValueError("OpenRouter API key is missing.")

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": MODEL_NAME,
        "messages": messages,
        "temperature": 0.7,
    }

    response = requests.post(
        API_URL,
        headers=headers,
        json=payload,
        timeout=60,
    )

    if not response.ok:
        raise Exception(
            f"OpenRouter Error {response.status_code}: "
            f"{response.text}"
        )

    result = response.json()
    return result["choices"][0]["message"]["content"]
def run_ai_build(
    messages,
    max_tool_calls=5,
    available_tools=None,
    required_branch=None
):
    """
    Run AI with GitHub tools and return actual execution results.
    """

    if not OPENROUTER_API_KEY:
        raise ValueError("OpenRouter API key is missing.")

    conversation = list(messages)
    total_tool_calls = 0
    tool_results = []

    # Select tools allowed for this AI run.
    active_tools = (
        available_tools
        if available_tools is not None
        else TOOLS
    )

    # Create a set of allowed tool names.
    allowed_tool_names = {
        tool["function"]["name"]
        for tool in active_tools
    }

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }

    while True:

        payload = {
            "model": MODEL_NAME,
            "messages": conversation,
            "tools": active_tools,
            "tool_choice": "auto",
            "temperature": 0.2,
        }

        response = requests.post(
            API_URL,
            headers=headers,
            json=payload,
            timeout=120,
        )

        if not response.ok:
            raise Exception(
                f"OpenRouter Tool Calling Error "
                f"{response.status_code}: {response.text}"
            )

        result = response.json()
        message = result["choices"][0]["message"]

        tool_calls = message.get("tool_calls") or []

        # AI has finished its response.
        if not tool_calls:

            final_answer = message.get("content", "")

            if not final_answer:
                raise Exception(
                    "AI returned an empty final response."
                )

            return {
                "final_answer": final_answer,
                "tool_results": tool_results,
            }

        # Enforce the maximum tool-call limit.
        if total_tool_calls + len(tool_calls) > max_tool_calls:
            raise Exception(
                "AI reached the maximum tool-call limit. "
                "Execution was not confirmed."
            )

        conversation.append(message)

        for tool_call in tool_calls:

            total_tool_calls += 1

            tool_name = tool_call["function"]["name"]
            arguments_text = tool_call["function"]["arguments"]

            try:

                # Enforce tool permissions at code level.
                if tool_name not in allowed_tool_names:
                    raise PermissionError(
                        f"Tool '{tool_name}' is not allowed "
                        f"for this run."
                    )

                arguments = json.loads(arguments_text)

                # Validate tool arguments.
                if not isinstance(arguments, dict):
                    raise ValueError(
                        "Tool arguments must be a dictionary."
                    )

                # Enforce the exact assigned branch.
                if required_branch is not None:

                    # Restrict GitHub write operations.
                    if tool_name in {
                        "create_branch",
                        "commit_and_push",
                        "open_pull_request",
                    }:

                        if (
                            arguments.get("branch_name")
                            != required_branch
                        ):
                            raise PermissionError(
                                "AI cannot modify an "
                                "unauthorized branch."
                            )

                    # Restrict GitHub read operations.
                    if tool_name == "read_file":

                        requested_branch = arguments.get(
                            "branch",
                            "main"
                        )

                        if requested_branch not in {
                            "main",
                            required_branch
                        }:
                            raise PermissionError(
                                "AI cannot read an "
                                "unauthorized branch."
                            )

                # Execute the permitted GitHub tool.
                tool_result = execute_tool(
                    tool_name,
                    arguments
                )

                # Store successful execution results.
                tool_results.append({
                    "tool": tool_name,
                    "success": True,
                    "result": tool_result,
                })

                if isinstance(tool_result, (dict, list)):
                    tool_content = json.dumps(tool_result)
                else:
                    tool_content = str(tool_result)

            except Exception as error:

                error_result = {
                    "error": str(error)
                }

                # Store failed execution results.
                tool_results.append({
                    "tool": tool_name,
                    "success": False,
                    "result": error_result,
                })

                tool_content = json.dumps(error_result)

            # Return the tool result to the AI.
            conversation.append({
                "role": "tool",
                "tool_call_id": tool_call["id"],
                "content": tool_content,
            })
            
def generate_technical_plan(requirements):
    messages = [
        {
            "role": "system",
            "content": (
                "You are a senior software architect inside BuildPilot. "
                "Create a practical technical plan using only the "
                "approved requirements provided. "
                "Do not invent additional features. "
                "Keep the project simple and suitable for a small team. "
                "Include these sections:\n"
                "1. Project Overview\n"
                "2. Database Tables and Their Important Columns\n"
                "3. Application Screens\n"
                "4. Backend Tasks\n"
                "5. Frontend Tasks\n"
                "6. Development Order\n"
                "7. Assumptions and Open Questions\n"
                "Break the work into small, clear development tasks. "
                "Return plain text with clear headings."
            )
        },
        {
            "role": "user",
            "content": (
                "Create a technical plan for these approved requirements:\n\n"
                f"Problem: {requirements.problem_statement}\n\n"
                f"Users: {requirements.users}\n\n"
                f"Must Do: {requirements.must_do}\n\n"
                f"Must Not Do: {requirements.must_not_do}\n\n"
                f"Success Criteria: {requirements.success_criteria}\n\n"
                f"Open Questions: {requirements.open_questions}"
            )
        }
    ]

    return get_ai_response(messages)


def generate_tasks_from_plan(plan_content):
    messages = [
        {
            "role": "system",
            "content": (
                "You are a software project planner inside BuildPilot. "
                "Read the approved technical plan and extract its "
                "development tasks. Do not invent additional features "
                "or tasks outside the plan. Break work into small, "
                "clear tasks. Return ONLY valid JSON in this format: "
                '{"tasks": [{"title": "Task title", '
                '"description": "Task description"}]}. '
                "Do not include Markdown code fences or explanations."
            )
        },
        {
            "role": "user",
            "content": (
                "Extract the development tasks from this approved "
                "technical plan:\n\n"
                f"{plan_content}"
            )
        }
    ]

    response = get_ai_response(messages)

    try:
        data = json.loads(response)
    except json.JSONDecodeError:
        raise ValueError(
            "AI returned an invalid task format. Please try again."
        )

    tasks = data.get("tasks")

    if not isinstance(tasks, list) or not tasks:
        raise ValueError(
            "AI did not return any valid development tasks."
        )

    for task in tasks:
        if not isinstance(task, dict):
            raise ValueError("Invalid task returned by AI.")

        if not task.get("title") or not task.get("description"):
            raise ValueError(
                "A task is missing its title or description."
            )

    return tasks
