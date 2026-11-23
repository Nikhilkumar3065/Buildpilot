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

from .ai_service import ( get_ai_response,generate_technical_plan,generate_tasks_from_plan)
from django.utils import timezone

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
        new_status = request.POST.get('status')

        valid_statuses = [
            choice[0]
            for choice in Task.STATUS_CHOICES
        ]

        task = Task.objects.filter(
            id=task_id,
            workspace=workspace,
            technical_plan=plan
        ).first()

        if task and new_status in valid_statuses:
            task.status = new_status
            task.save()

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
