import os
import json
from django.template import response
import requests
from dotenv import load_dotenv

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
        f"OpenRouter Error {response.status_code}: {response.text}"
    )
    result = response.json()

    return result["choices"][0]["message"]["content"]
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
            raise ValueError("A task is missing its title or description.")

    return tasks
