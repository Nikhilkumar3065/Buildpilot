import json
import markdown
import bleach
from django.contrib.admin import action
from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.db import transaction
from django.contrib.auth.decorators import login_required
from urllib3 import request
from .ai_tools import TOOLS
from .forms import ClientForm, ProblemForm,RequirementForm,TechnicalPlanForm
from .models import (
    Client,
    Problem,
    RequirementDocument,
    Workspace,
    WorkspaceMember,
    BrainstormSession,
    BrainstormMessage,
    RequirementVersion,
    RequirementDocument,
    TechnicalPlan,
    Task
)

from .ai_service import ( get_ai_response,generate_technical_plan,generate_tasks_from_plan,run_ai_build)
from django.utils import timezone
from django.contrib import messages
from django.views.decorators.http import require_POST
def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        workspace_name = request.POST.get('workspace_name', '').strip()

        if form.is_valid() and workspace_name:
            with transaction.atomic():
                user = form.save()

                workspace = Workspace.objects.create(
                    name=workspace_name
                )

                WorkspaceMember.objects.create(
                    workspace=workspace,
                    user=user
                )

            login(request, user)
            return redirect('home')

    else:
        form = UserCreationForm()

    return render(request, 'core/signup.html', {
        'form': form
    })

@login_required
def home(request):
    membership = WorkspaceMember.objects.filter(
        user=request.user
    ).select_related('workspace').first()

    return render(request, 'core/home.html', {
        'workspace': membership.workspace if membership else None
    })
@login_required
def clients(request):
    membership = WorkspaceMember.objects.filter(
        user=request.user
    ).select_related('workspace').first()

    if not membership:
        return redirect('signup')

    workspace = membership.workspace

    if request.method == 'POST':
        form = ClientForm(request.POST)

        if form.is_valid():
            client = form.save(commit=False)
            client.workspace = workspace
            client.save()
            return redirect('clients')
    else:
        form = ClientForm()

    client_list = Client.objects.filter(workspace=workspace)

    return render(request, 'core/clients.html', {
        'form': form,
        'clients': client_list
    })


@login_required
def problems(request):
    membership = WorkspaceMember.objects.filter(
        user=request.user
    ).select_related('workspace').first()

    if not membership:
        return redirect('signup')

    workspace = membership.workspace

    if request.method == 'POST':
        form = ProblemForm(request.POST)
        form.fields['client'].queryset = Client.objects.filter(
            workspace=workspace
        )

        if form.is_valid():
            problem = form.save(commit=False)
            problem.workspace = workspace
            problem.save()
            return redirect('problems')
    else:
        form = ProblemForm()
        form.fields['client'].queryset = Client.objects.filter(
            workspace=workspace
        )

    problem_list = Problem.objects.filter(
        workspace=workspace
    ).select_related('client')

    return render(request, 'core/problems.html', {
        'form': form,
        'problems': problem_list
    })

@login_required
def brainstorm(request, problem_id):
    membership = WorkspaceMember.objects.filter(
        user=request.user
    ).select_related('workspace').first()

    if not membership:
        return redirect('signup')

    workspace = membership.workspace

    # Only allow access to problems in this workspace
    problem = Problem.objects.filter(
        id=problem_id,
        workspace=workspace
    ).select_related('client').first()

    if not problem:
        return redirect('problems')

    session, created = BrainstormSession.objects.get_or_create(
        workspace=workspace,
        problem=problem
    )

    if request.method == 'POST':
        consultant_message = request.POST.get(
            'message', ''
        ).strip()

        if consultant_message:
            BrainstormMessage.objects.create(
                workspace=workspace,
                session=session,
                sender='consultant',
                message=consultant_message
            )

            chat_history = [
                {
                    'role': 'system',
                    'content': (
                        'You are BuildPilot, an AI software consultant. '
                        'Understand the client problem, ask questions '
                        'one at a time, and suggest useful ideas. '
                        'Do not ask multiple questions at once. '
                        'Keep responses clear and beginner-friendly.'
                    )
                }
            ]

            for item in session.messages.order_by('created_at'):
                chat_history.append({
                    'role': (
                        'assistant'
                        if item.sender == 'ai'
                        else 'user'
                    ),
                    'content': item.message
                })

            try:
                ai_reply = get_ai_response(chat_history)

                BrainstormMessage.objects.create(
                    workspace=workspace,
                    session=session,
                    sender='ai',
                    message=ai_reply
                )

            except Exception as error:
                print("AI Error:", error)

        return redirect('brainstorm', problem_id=problem.id)

    # Ask the AI its first question
    if not session.messages.exists():
        initial_prompt = (
            f"The client is {problem.client.name}. "
            f"Their problem is: {problem.description}. "
            "Start the brainstorming conversation. "
            "Ask the consultant one important question "
            "to understand the problem better."
        )

        try:
            ai_reply = get_ai_response([
                {
                    'role': 'system',
                    'content': (
                        'You are BuildPilot, an AI software consultant. '
                        'Ask one question at a time and suggest useful ideas.'
                    )
                },
                {
                    'role': 'user',
                    'content': initial_prompt
                }
            ])

            BrainstormMessage.objects.create(
                workspace=workspace,
                session=session,
                sender='ai',
                message=ai_reply
            )

        except Exception as error:
            print("AI Error:", error)

    messages = session.messages.order_by('created_at')

    return render(request, 'core/brainstorm.html', {
        'problem': problem,
        'session': session,
        'messages': messages
    })

def generate_requirements_content(problem):
    session = problem.brainstorm_sessions.order_by(
        '-created_at'
    ).first()

    if not session or not session.messages.exists():
        raise ValueError("No brainstorming conversation found.")

    conversation = "\n".join([
        f"{message.sender}: {message.message}"
        for message in session.messages.order_by('created_at')
    ])

    messages = [
        {
            "role": "system",
            "content": (
                "You are a software requirements analyst inside BuildPilot. "
                "Create a plain-English requirements document using only "
                "the information provided. Do not invent confirmed facts. "
                "Put missing information in open_questions. "
                "Return valid JSON only, without Markdown formatting, "
                "using exactly these six keys: "
                "problem_statement, users, must_do, must_not_do, "
                "success_criteria, open_questions. "
                "Every value must be a string."
            )
        },
        {
            "role": "user",
            "content": (
                f"Client: {problem.client.name}\n"
                f"Original problem: {problem.description}\n\n"
                f"Brainstorming conversation:\n{conversation}\n\n"
                "Generate the requirements document."
            )
        }
    ]

    ai_response = get_ai_response(messages).strip()

    # Remove Markdown code fences if the AI adds them
    if ai_response.startswith("```"):
        ai_response = ai_response.split("\n", 1)[1]
        ai_response = ai_response.rsplit("```", 1)[0].strip()

    data = json.loads(ai_response)

    required_fields = [
        'problem_statement',
        'users',
        'must_do',
        'must_not_do',
        'success_criteria',
        'open_questions'
    ]

    for field in required_fields:
        if field not in data or not isinstance(data[field], str):
            raise ValueError(f"Invalid AI requirements field: {field}")

    return data


@login_required
def requirements(request, problem_id):
    membership = WorkspaceMember.objects.filter(
        user=request.user
    ).select_related('workspace').first()

    if not membership:
        return redirect('signup')

    workspace = membership.workspace

    problem = Problem.objects.filter(
        id=problem_id,
        workspace=workspace
    ).select_related('client').first()

    if not problem:
        return redirect('problems')

    document = RequirementDocument.objects.filter(
        problem=problem,
        workspace=workspace
    ).first()

    if request.method == 'POST':

        action = request.POST.get('action')
        # Approve requirements document
        if action == 'approve' and document:
            if document.status == 'draft':
                document.status = 'approved'
                document.approved_at = timezone.now()
                document.save()

            return redirect(
                'requirements',
                problem_id=problem.id
            )

        # Generate the first requirements document using AI
        if action == 'generate' and not document:
            try:
                data = generate_requirements_content(problem)

                document = RequirementDocument.objects.create(
                    workspace=workspace,
                    problem=problem
                )

                RequirementVersion.objects.create(
                    document=document,
                    workspace=workspace,
                    version_number=1,
                    **data
                )

                return redirect(
                    'requirements',
                    problem_id=problem.id
                )

            except Exception as error:
                print("Requirements Generation Error:", error)
                return render(request, 'core/requirements.html', {
                    'problem': problem,
                    'document': None,
                    'form': RequirementForm(),
                    'versions': [],
                    'error': str(error)
                })

        # Save edits as a new version
        if document and document.status == 'draft':
            form = RequirementForm(request.POST)

            if form.is_valid():
                latest_version = document.versions.order_by(
                    '-version_number'
                ).first()

                new_version = form.save(commit=False)
                new_version.document = document
                new_version.workspace = workspace
                new_version.version_number = (
                    latest_version.version_number + 1
                )

                new_version.save()

            return redirect(
                'requirements',
                problem_id=problem.id
            )

    latest_version = (
        document.versions.order_by('-version_number').first()
        if document else None
    )

    form = (
        RequirementForm(instance=latest_version)
        if latest_version else RequirementForm()
    )

    versions = document.versions.all() if document else []

    return render(request, 'core/requirements.html', {
        'problem': problem,
        'document': document,
        'form': form,
        'versions': versions
    })


@login_required
def technical_plan(request, problem_id):

    membership = WorkspaceMember.objects.filter(
        user=request.user
    ).select_related('workspace').first()

    if not membership:
        return redirect('signup')

    workspace = membership.workspace

    problem = Problem.objects.filter(
        id=problem_id,
        workspace=workspace
    ).select_related('client').first()

    if not problem:
        return redirect('problems')

    document = RequirementDocument.objects.filter(
        problem=problem,
        workspace=workspace,
        status='approved'
    ).first()

    if not document:
        return redirect(
            'requirements',
            problem_id=problem.id
        )

    latest_version = document.versions.order_by(
        '-version_number'
    ).first()

    if not latest_version:
        return redirect(
            'requirements',
            problem_id=problem.id
        )

    plan = TechnicalPlan.objects.filter(
        problem=problem,
        workspace=workspace
    ).first()

    error = None

    if request.method == 'POST':

        action = request.POST.get('action')

        # Approve technical plan and create tasks
        if action == 'approve' and plan:

            if plan.status == 'draft':

                try:
                    generated_tasks = generate_tasks_from_plan(
                        plan.content
                    )

                    for index, task_data in enumerate(
                        generated_tasks,
                        start=1
                    ):
                        Task.objects.create(
                            workspace=workspace,
                            technical_plan=plan,
                            title=task_data['title'],
                            description=task_data['description'],
                            status='backlog',
                            task_order=index
                        )

                    plan.status = 'approved'
                    plan.approved_at = timezone.now()
                    plan.save()

                    return redirect(
                        'technical_plan',
                        problem_id=problem.id
                    )

                except Exception as exception:
                    print(
                        "Task Generation Error:",
                        exception
                    )
                    error = str(exception)

            else:
                return redirect(
                    'technical_plan',
                    problem_id=problem.id
                )

        # Generate technical plan using AI
        elif action == 'generate' and not plan:

            try:
                content = generate_technical_plan(
                    latest_version
                )

                TechnicalPlan.objects.create(
                    workspace=workspace,
                    problem=problem,
                    content=content
                )

                return redirect(
                    'technical_plan',
                    problem_id=problem.id
                )

            except Exception as exception:
                print(
                    "Technical Plan Error:",
                    exception
                )
                error = str(exception)

        # Save technical plan edits
        elif plan and plan.status == 'draft':

            form = TechnicalPlanForm(request.POST)

            if form.is_valid():

                plan.content = form.cleaned_data['content']
                plan.save()

                return redirect(
                    'technical_plan',
                    problem_id=problem.id
                )

    # Prepare the technical plan form
    form = (
        TechnicalPlanForm(instance=plan)
        if plan else TechnicalPlanForm()
    )

    # Convert Markdown into formatted HTML
    plan_html = ""

    if plan:

        rendered_content = markdown.markdown(
            plan.content,
            extensions=[
                'tables',
                'fenced_code'
            ]
        )

        allowed_tags = bleach.sanitizer.ALLOWED_TAGS.union({
            'h1', 'h2', 'h3', 'h4',
            'p', 'br', 'hr',
            'ul', 'ol', 'li',
            'pre', 'code',
            'table', 'thead', 'tbody',
            'tr', 'th', 'td',
            'blockquote',
            'strong', 'em'
        })

        plan_html = bleach.clean(
            rendered_content,
            tags=allowed_tags,
            attributes={
                'a': ['href', 'title'],
                'code': ['class'],
                'pre': ['class']
            },
            protocols=[
                'http',
                'https',
                'mailto'
            ],
            strip=True
        )

    return render(
        request,
        'core/technical_plan.html',
        {
            'problem': problem,
            'plan': plan,
            'form': form,
            'plan_html': plan_html,
            'error': error
        }
    )




@login_required
def task_board(request, problem_id):

    membership = WorkspaceMember.objects.filter(
        user=request.user
    ).select_related('workspace').first()

    if not membership:
        return redirect('signup')

    workspace = membership.workspace

    problem = Problem.objects.filter(
        id=problem_id,
        workspace=workspace
    ).select_related('client').first()

    if not problem:
        return redirect('problems')

    plan = TechnicalPlan.objects.filter(
        problem=problem,
        workspace=workspace,
        status='approved'
    ).first()

    if not plan:
        return redirect(
            'technical_plan',
            problem_id=problem.id
        )

    if request.method == 'POST':

        task_id = request.POST.get('task_id')
        action = request.POST.get('action')

        task = Task.objects.filter(
            id=task_id,
            workspace=workspace,
            technical_plan=plan
        ).first()

        if not task:
            messages.error(
                request,
                'Task not found.'
            )

            return redirect(
                'task_board',
                problem_id=problem.id
            )

        # Human approves AI-generated work.
        if action == 'approve':

            if task.status != 'needs_human_check':

                messages.error(
                    request,
                    'Only tasks awaiting human review can be approved.'
                )

            else:

                task.status = 'done'
                task.reviewed_at = timezone.now()

                task.save(update_fields=[
                    'status',
                    'reviewed_at'
                ])

                messages.success(
                    request,
                    'Task approved successfully!'
                )

        # Human sends AI-generated work back.
        elif action == 'send_back':

            if task.status != 'needs_human_check':

                messages.error(
                    request,
                    'Only tasks awaiting human review can be sent back.'
                )

            else:

                review_comment = request.POST.get(
                    'review_comment',
                    ''
                ).strip()

                if not review_comment:

                    messages.error(
                        request,
                        'Please provide a comment before sending the task back.'
                    )

                else:

                    task.status = 'sent_back'
                    task.review_comment = review_comment
                    task.reviewed_at = timezone.now()

                    task.save(update_fields=[
                        'status',
                        'review_comment',
                        'reviewed_at'
                    ])

                    messages.success(
                        request,
                        'Task sent back for rework. Feedback saved successfully.'
                    )

        # Allow ordinary status movement, but never direct approval.
        elif action == 'update_status':

            new_status = request.POST.get('status')

            allowed_statuses = [
                'backlog',
                'ready_ai',
                'ai_building',
                'needs_human_check',
                'sent_back',
            ]

            if new_status in allowed_statuses:

                task.status = new_status

                task.save(update_fields=[
                    'status'
                ])

                messages.success(
                    request,
                    'Task status updated successfully.'
                )

            else:

                messages.error(
                    request,
                    'Invalid task status.'
                )

        else:

            messages.error(
                request,
                'Invalid task action.'
            )

        return redirect(
            'task_board',
            problem_id=problem.id
        )

    tasks = Task.objects.filter(
        workspace=workspace,
        technical_plan=plan
    ).order_by('task_order')

    return render(
        request,
        'core/task_board.html',
        {
            'problem': problem,
            'plan': plan,
            'tasks': tasks,
            'status_choices': Task.STATUS_CHOICES
        }
    )

@login_required
@require_POST
def run_ai_task(request, problem_id, task_id):

    # 1. Get the logged-in user's workspace.
    membership = WorkspaceMember.objects.filter(
        user=request.user
    ).select_related('workspace').first()

    if not membership:
        messages.error(
            request,
            "Workspace membership not found."
        )
        return redirect('problems')

    workspace = membership.workspace

    # 2. Find the problem inside this workspace.
    problem = Problem.objects.filter(
        id=problem_id,
        workspace=workspace
    ).first()

    if not problem:
        messages.error(request, "Problem not found.")
        return redirect('problems')

    # 3. Find the approved technical plan.
    plan = TechnicalPlan.objects.filter(
        problem=problem,
        workspace=workspace,
        status='approved'
    ).first()

    if not plan:
        messages.error(
            request,
            "An approved technical plan is required."
        )
        return redirect(
            'task_board',
            problem_id=problem.id
        )

    # 4. Find the task inside this workspace and plan.
    task = Task.objects.filter(
        id=task_id,
        workspace=workspace,
        technical_plan=plan
    ).first()

    if not task:
        messages.error(request, "Task not found.")
        return redirect(
            'task_board',
            problem_id=problem.id
        )

    # 5. Allow new tasks and sent-back tasks.
    if task.status not in ['ready_ai', 'sent_back']:
        messages.error(
            request,
            "Only Ready for AI or Sent Back tasks "
            "can be executed."
        )
        return redirect(
            'task_board',
            problem_id=problem.id
        )

    # Remember the original status in case execution fails.
    original_status = task.status

    # Determine whether this is a rework.
    is_rework = original_status == 'sent_back'

    # 6. Prepare branch and pull request details.
    if is_rework:

        # Reuse the original branch and pull request.
        branch_name = task.ai_branch
        pull_request_url = task.pull_request_url

        if not branch_name or not pull_request_url:
            messages.error(
                request,
                "Existing AI branch or pull request "
                "details are missing."
            )
            return redirect(
                'task_board',
                problem_id=problem.id
            )

        if not task.review_comment.strip():
            messages.error(
                request,
                "Human review feedback is required."
            )
            return redirect(
                'task_board',
                problem_id=problem.id
            )

        # Restrict tools for sent-back tasks.
        available_tools = [
            tool for tool in TOOLS
            if tool["function"]["name"] in {
                "read_file",
                "commit_and_push",
            }
        ]

    else:

        # Generate a new branch for a new task.
        branch_name = (
            f"ai/task-{task.id}-"
            f"{timezone.now().strftime('%Y%m%d%H%M%S')}"
        )

        pull_request_url = ""

        # Allow all registered GitHub tools.
        available_tools = TOOLS

    # 7. Mark the task as AI Building.
    # Conditional update prevents two simultaneous runs.
    updated = Task.objects.filter(
        id=task.id,
        workspace=workspace,
        technical_plan=plan,
        status=original_status
    ).update(status='ai_building')

    if not updated:
        messages.error(
            request,
            "This task is already being processed "
            "or its status has changed."
        )
        return redirect(
            'task_board',
            problem_id=problem.id
        )

    task.status = 'ai_building'

    try:

        # 8. Prepare the AI prompts.
        if is_rework:

            system_prompt = """
You are BuildPilot AI, an autonomous software
development assistant.

Your job is to improve an existing implementation
based on human review feedback.

IMPORTANT RULES:

1. Work only in the configured demo repository.
2. Never push changes to the main branch.
3. Use only the existing AI branch supplied.
4. Read README.md from the main branch first.
5. Read relevant existing files from the AI branch.
6. Do not guess existing file contents.
7. Address the human review feedback.
8. Preserve existing functionality.
9. Make only necessary changes.
10. Commit and push improvements to the same branch.
11. Do not create a new branch.
12. Do not create a new pull request.
13. Never claim success if a tool call fails.
14. Never mark a task as Done.

The existing pull request will automatically
include new commits pushed to its branch.

Return a clear summary of the improvements
and files modified.
"""

            user_prompt = f"""
Improve this existing BuildPilot task.

TASK TITLE:
{task.title}

TASK DESCRIPTION:
{task.description}

HUMAN REVIEW FEEDBACK:
{task.review_comment}

EXISTING AI BRANCH:
{branch_name}

EXISTING PULL REQUEST:
{pull_request_url}

Follow this order:

1. Read README.md from main.
2. Read relevant files from the existing AI branch.
3. Understand the human review feedback.
4. Implement the requested improvements.
5. Commit and push changes to the same AI branch.
6. Return a summary of the improvements.

Do not create a new branch.
Do not create a new pull request.
"""

        else:

            system_prompt = """
You are BuildPilot AI, an autonomous software
development assistant.

Your job is to implement exactly one task
in the configured demo GitHub repository.

IMPORTANT RULES:

1. Work only in the configured demo repository.
2. Never push changes to the main branch.
3. All changes must be made on the exact
   AI branch supplied by the user.
4. Read README.md from the main branch first.
5. Inspect relevant existing files using read_file.
6. Do not guess existing file contents.
7. Implement only the requested task.
8. Preserve existing functionality.
9. Use commit_and_push to save your changes.
10. Open a pull request from the AI branch to main.
11. Never claim success if a tool call fails.
12. Never mark a task as Done.

Use the available GitHub tools to perform the work.

Return a clear summary of changes, files modified,
branch name, and pull request URL.
"""

            user_prompt = f"""
Implement this BuildPilot task.

TASK TITLE:
{task.title}

TASK DESCRIPTION:
{task.description}

REQUIRED BRANCH:
{branch_name}

Follow this order:

1. Read README.md from main.
2. Inspect relevant files.
3. Create the required branch.
4. Implement the task.
5. Commit and push your changes.
6. Open a pull request to main.
7. Return the implementation summary
   and pull request URL.
"""

        # 9. Execute the AI build.
        result = run_ai_build(
            [
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": user_prompt
                }
            ],
            max_tool_calls=20,
            available_tools=available_tools,
            required_branch=branch_name
        )

        # 10. Verify actual GitHub tool execution.
        tool_results = result.get("tool_results", [])

        successful_tools = {
            item.get("tool")
            for item in tool_results
            if item.get("success") is True
        }

        if is_rework:

            # Rework requires reading and committing files.
            required_tools = {
                "read_file",
                "commit_and_push",
            }

        else:

            # New tasks require the complete GitHub workflow.
            required_tools = {
                "read_file",
                "create_branch",
                "commit_and_push",
                "open_pull_request",
            }

        missing_tools = required_tools - successful_tools

        if missing_tools:
            raise Exception(
                "GitHub execution incomplete. "
                "Missing successful operations: "
                + ", ".join(sorted(missing_tools))
            )

        # 11. Retrieve the new PR URL for new tasks.
        if not is_rework:

            pr_result = next(
                (
                    item.get("result", {})
                    for item in reversed(tool_results)
                    if item.get("tool") == "open_pull_request"
                    and item.get("success") is True
                ),
                {}
            )

            pull_request_url = pr_result.get("html_url")

            if not pull_request_url:
                raise Exception(
                    "GitHub did not return a valid "
                    "pull request URL."
                )

        # 12. Save GitHub details and move to human review.
        task.ai_branch = branch_name
        task.pull_request_url = pull_request_url
        task.status = 'needs_human_check'

        task.save(
            update_fields=[
                'ai_branch',
                'pull_request_url',
                'status',
            ]
        )

        # 13. Display the success message.
        if is_rework:

            messages.success(
                request,
                "AI applied the review feedback "
                "and pushed changes to the existing branch. "
                f"Review the pull request: {pull_request_url}"
            )

        else:

            messages.success(
                request,
                "AI execution completed. "
                f"Review the pull request: {pull_request_url}"
            )

    except Exception as error:

        # Print the actual error in the Django terminal.
        print("\n========== BUILDPILOT AI ERROR ==========")
        print("Error type:", type(error).__name__)
        print("Error message:", repr(error))
        print("=========================================\n")

        # Restore the original status if execution fails.
        task.status = original_status
        task.save(update_fields=['status'])

        messages.error(
            request,
            "AI execution failed. Check the Django terminal "
            "for details."
        )

    return redirect(
        'task_board',
        problem_id=problem.id
    )