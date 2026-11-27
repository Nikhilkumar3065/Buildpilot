from django.db import transaction
from django.utils import timezone

from .models import ProjectSkill


DEFAULT_SKILL_CONTENT = """# Project Skill File

This document contains human-approved lessons from previous
development runs and bug fixes.

## Approved Lessons
"""


def get_project_skill(workspace, problem):

    # Validate workspace ownership.

    if problem.workspace_id != workspace.id:
        raise ValueError(
            "This project does not belong to the workspace."
        )

    skill, created = ProjectSkill.objects.get_or_create(
        workspace=workspace,
        problem=problem,
        defaults={
            "content": DEFAULT_SKILL_CONTENT
        }
    )

    return skill


def get_project_lessons(workspace, problem):

    skill = get_project_skill(
        workspace=workspace,
        problem=problem
    )

    return skill.content


@transaction.atomic
def save_bug_lesson(bug):

    # Only human-approved bug fixes can contribute lessons.

    if bug.status != "resolved":
        raise ValueError(
            "Only resolved bugs can contribute lessons."
        )

    lesson = (bug.lesson or "").strip()

    if not lesson:
        return False

    workspace = bug.workspace
    task = bug.task
    technical_plan = task.technical_plan
    problem = technical_plan.problem

    # Validate ownership across all related records.

    if (
        task.workspace_id != workspace.id
        or technical_plan.workspace_id != workspace.id
        or problem.workspace_id != workspace.id
    ):
        raise ValueError(
            "Workspace ownership validation failed."
        )

    skill = get_project_skill(
        workspace=workspace,
        problem=problem
    )

    # Lock the skill document to prevent concurrent updates.

    skill = ProjectSkill.objects.select_for_update().get(
        id=skill.id,
        workspace=workspace,
        problem=problem
    )

    # Prevent duplicate lessons from the same bug.

    lesson_marker = f"<!-- bug-lesson-{bug.id} -->"

    if lesson_marker in skill.content:
        return False

    approved_date = timezone.localtime(
        bug.resolved_at or timezone.now()
    ).strftime("%d %B %Y, %I:%M %p")

    lesson_entry = f"""

{lesson_marker}

### Bug #{bug.id}: {bug.title}

**Associated Task:** {task.title}

**Approved On:** {approved_date}

**Lesson Learned:**

{lesson}

---

"""

    skill.content = (
        skill.content.rstrip() + lesson_entry
    )

    skill.save(
        update_fields=[
            "content",
            "updated_at"
        ]
    )

    return True
