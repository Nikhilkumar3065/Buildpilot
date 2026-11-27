# BuildPilot

BuildPilot is a web application where consultants and AI collaborate to understand client problems, prepare requirements, create technical plans, and build software through an AI-assisted development workflow.

The application converts client problems written in simple English into structured requirements, technical plans, and development tasks.

AI assists with brainstorming, planning, code generation, and GitHub operations, while consultants review and approve important decisions and generated software.

---

## Technology Stack

| Component | Technology |
|---|---|
| Backend | Python, Django |
| Frontend | HTML, CSS, JavaScript |
| Database | PostgreSQL |
| Database Hosting | Supabase |
| Database Driver | Psycopg |
| AI Integration | OpenRouter API |
| AI Model Configuration | `openrouter/free` |
| AI Tool Calling | OpenRouter Function Calling |
| GitHub Integration | GitHub REST API |
| HTTP Client | Requests |
| Version Control | Git, GitHub |
| Environment Configuration | python-dotenv |
| Authentication | Django Authentication |

---

## Project Workflow

BuildPilot follows a consultant-and-AI development workflow:

1. Create a client and describe the client's problem.
2. Brainstorm with AI to understand the requirements.
3. Generate, edit, and approve a requirements document.
4. Generate and approve a technical plan.
5. Generate development tasks and organize them on the task board.
6. Run AI to implement selected tasks in a separate GitHub repository.
7. Review the generated changes and approve or send them back for improvements.

Bug reporting, AI bug fixing, and project-specific learning are planned as additional workflow capabilities.

---

## Features

### 1. User Signup and Workspace Management

- User registration and automatic login.
- Workspace creation during signup.
- Workspace membership management.
- Workspace-based data separation.
- Django session-based authentication.

### 2. Client and Problem Management

- Create clients using name and email.
- Submit client problems in simple English.
- View clients belonging to the user's workspace.
- View problems belonging to the user's workspace.
- Associate each problem with its client.

### 3. AI Brainstorming

- AI asks questions to understand the client's problem.
- AI suggests ideas for further discussion.
- Consultants can answer questions and add ideas.
- Brainstorming conversations are saved in PostgreSQL.
- Conversations are associated with their corresponding workspace and problem.

### 4. Requirements Document

AI generates a requirements document containing:

- Problem Statement
- Users
- Must Do
- Must Not Do
- Success Criteria
- Open Questions

Consultants can review and edit the generated requirements.

Each edit is saved as a new version, allowing previous requirements versions to be retained.

The consultant can mark the requirements document as approved by the client.

### 5. Technical Plan

- AI generates a technical plan from the approved requirements.
- The plan includes database tables, screens, and development tasks.
- Consultants can review, edit, and approve the plan.
- Approved technical plans are used to generate development tasks.
- Generated tasks are displayed on the project task board.

### 6. Task Board

The task board organizes development tasks using six statuses:

| Status | Description |
|---|---|
| Backlog | Tasks waiting to be prepared |
| Ready for AI | Tasks available for an AI build run |
| AI Building | AI is working on the task |
| Needs Human Check | AI-generated work is waiting for human review |
| Done | Work approved by a human reviewer |
| Sent Back | Work returned to AI for improvements |

Tasks are displayed in their development order.

Consultants can manage tasks, initiate AI build runs, review generated work, and provide feedback.

### 7. AI Build Execution

BuildPilot integrates AI tool calling with native GitHub operations.

When a consultant runs an eligible task:

1. BuildPilot validates workspace ownership and task status.
2. The task moves to AI Building.
3. AI receives the task title, description, and available tools.
4. AI reads relevant repository files.
5. AI creates a dedicated branch using the `ai/` prefix.
6. AI generates the required code.
7. Native GitHub tools commit and push the generated files.
8. AI requests the creation of a pull request.
9. BuildPilot checks the required tool execution results.
10. The task moves to Needs Human Check after successful execution.

GitHub branch names and pull request URLs are stored in the database.

Failed executions return the task to its previous status.

### 8. GitHub Integration

BuildPilot uses the GitHub REST API to perform repository operations.

Implemented GitHub operations include:

- Retrieve repository information.
- Read repository files.
- Create AI development branches.
- Create or update files.
- Commit and push generated code.
- Open pull requests.

AI-generated software is stored in a separate public demonstration repository.

The BuildPilot application repository is separate from the AI-generated output repository.

### 9. Human Review and Approval

After an AI build run, the task moves to Needs Human Check.

The consultant can:

- Review the AI-generated changes.
- Inspect the GitHub branch and pull request.
- Approve the task.
- Send the task back with feedback.

Approving a task changes its status to Done.

Sending a task back changes its status to Sent Back and stores the consultant's feedback.

AI does not have a tool that can directly mark a task as Done.

### 10. Feedback-Based AI Rework

Tasks sent back by a human reviewer can be executed again using the Re-run AI with Feedback button.

During a rework execution:

1. AI receives the original task and human feedback.
2. AI reads relevant files from the existing branch.
3. AI generates improvements based on the feedback.
4. Changes are committed to the existing AI branch.
5. The existing pull request receives the new commits.
6. The task returns to Needs Human Check.

A new pull request is not required for the same rework execution.

---

## Project Structure

The main application components are organized as follows:

```text
Buildpilot/
│
├── config/
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
│
├── core/
│   ├── migrations/
│   ├── templates/
│   │   └── core/
│   ├── ai_service.py
│   ├── ai_tools.py
│   ├── github_service.py
│   ├── models.py
│   ├── forms.py
│   ├── views.py
│   ├── urls.py
│   ├── tests.py
│   └── admin.py
│
├── .env
├── .gitignore
├── manage.py
├── requirements.txt
└── README.md
```

The `.env` file is local and must not be committed to GitHub.

---

## Database Structure

BuildPilot uses PostgreSQL hosted on Supabase.

Workspace-owned application records are associated with a workspace using `workspace_id` to support workspace-level data isolation.

| Database Table | Important Columns |
|---|---|
| core_workspace | id, name, created_at |
| core_workspacemember | id, workspace_id, user_id, joined_at |
| core_client | id, workspace_id, name, email, created_at |
| core_problem | id, workspace_id, client_id, description, created_at |
| core_brainstormsession | id, workspace_id, problem_id, created_at |
| core_brainstormmessage | id, workspace_id, session_id, sender, message, created_at |
| core_requirementdocument | id, workspace_id, problem_id, status, approved_at, created_at |
| core_requirementversion | id, document_id, workspace_id, version_number, problem_statement, users, must_do, must_not_do, success_criteria, open_questions, created_at |
| core_technicalplan | id, workspace_id, problem_id, content, status, approved_at, created_at |
| core_task | id, workspace_id, technical_plan_id, title, description, status, task_order, review_comment, reviewed_at, ai_branch, pull_request_url, created_at |

Django's built-in authentication and session tables are also used.

SQLite is not used as the application database.

---

## AI Integration

| Configuration | Value |
|---|---|
| AI Provider | OpenRouter |
| Configured Model | `openrouter/free` |
| API Endpoint | `https://openrouter.ai/api/v1/chat/completions` |
| Integration File | `core/ai_service.py` |
| Tool Definitions | `core/ai_tools.py` |
| GitHub Operations | `core/github_service.py` |

The current model configuration in `core/ai_service.py` is:

```python
MODEL_NAME = "openrouter/free"
```

AI is used for:

- Brainstorming.
- Understanding client requirements.
- Requirements document generation.
- Technical plan generation.
- Development task generation.
- Code generation.
- GitHub tool selection.
- Feedback-based code improvements.

### Model Selection and Limitations

The current development configuration uses OpenRouter's free model router.

The router dynamically selects an available underlying model rather than guaranteeing one fixed model.

Tool-calling availability, response quality, rate limits, and execution reliability may vary depending on the selected underlying model.

GitHub tool-calling executions have been demonstrated during local development.

A fixed non-free model has not been configured because the current development setup is limited to free API usage.

Therefore, the requirement for one exact non-free model remains outstanding.

---

## AI and Native Code Responsibilities

BuildPilot separates AI reasoning from native application operations.

AI is responsible for understanding requirements, planning work, selecting tools, generating code, and responding to human feedback.

Native Python and Django code is responsible for executing repository operations, validating permissions, managing database records, and updating task statuses.

### Tools Table

| Tool or Operation | Who Performs It | Purpose |
|---|---|---|
| Brainstorming | AI | Understand the client's problem |
| Requirements generation | AI | Generate structured requirements |
| Technical planning | AI | Prepare implementation plans |
| Task generation | AI | Divide plans into development tasks |
| Tool selection | AI | Decide which available tool to call |
| Code generation | AI | Generate software implementation |
| Feedback interpretation | AI | Understand requested improvements |
| `get_repository_info` | Native Python | Retrieve configured repository information |
| `read_file` | Native Python | Read repository file contents |
| `create_branch` | Native Python | Create an authorized AI branch |
| `commit_and_push` | Native Python | Commit and push generated files |
| `open_pull_request` | Native Python | Create a GitHub pull request |
| `execute_tool` | Native Python | Validate and dispatch tool calls |
| `run_ai_build` | AI and Native Python | Coordinate AI reasoning and tool execution |
| Branch validation | Native Python | Restrict repository branch access |
| File path validation | Native Python | Validate repository file paths |
| Workspace permission checks | Django | Restrict access to workspace-owned records |
| Task status management | Django | Manage development workflow states |
| Human approval | Consultant | Approve generated work |
| Human feedback | Consultant | Request improvements |

The AI requests GitHub operations through tool calls.

Native Python functions perform the actual GitHub API requests.

---

## GitHub Security

BuildPilot applies code-level restrictions to AI-generated repository operations.

Implemented restrictions include:

- GitHub operations use the configured demonstration repository.
- AI development branches must use the `ai/` prefix.
- AI cannot commit directly to the main branch through the exposed tools.
- AI cannot delete repository files through the exposed tools.
- Repository file paths are validated.
- AI write operations are restricted to the branch authorized for the current run.
- Feedback-based rework uses the existing authorized branch.
- AI cannot directly mark tasks as Done.
- Tool calls are limited per AI build execution.
- GitHub credentials are loaded from environment variables.

The current demonstration configuration uses one configured GitHub output repository.

Separate repository isolation for multiple workspaces requires further verification and implementation.

---

## Workspace Security

BuildPilot applies workspace-based access restrictions to application records.

Security measures include:

- Users must be authenticated to access protected workflow pages.
- Client and problem listings are filtered by workspace.
- Workflow pages check workspace ownership.
- Task updates validate workspace and technical plan ownership.
- AI build requests validate workspace and task ownership.
- Cross-workspace record access is restricted through application queries.
- Unauthenticated users are redirected to the configured authentication page.
- State-changing forms use Django CSRF protection.

Workspace ownership is enforced through backend application logic rather than relying only on frontend visibility.

Additional security tests and permission audits are part of the ongoing development process.

## Automated Security Tests

Security tests are located in `core/tests.py`.

BuildPilot includes 17 automated security and workflow tests.

The tests verify:

1. Team A cannot view Team B's clients.
2. Team A cannot view Team B's problems.
3. Team B cannot view Team A's clients.
4. Team B cannot view Team A's problems.
5. Unauthorized direct access to workflow pages is blocked.
6. Team A cannot view Team B's tasks.
7. Team A cannot modify Team B's tasks.
8. Authorized users can update their own tasks.
9. Team A cannot create problems using Team B's clients.
10. Unsupported deletion requests cannot remove records.
11. Unauthenticated users cannot access protected pages.
12. Team A cannot execute AI on Team B's tasks.
13. Unauthenticated users cannot execute AI.
14. Team A cannot approve Team B's tasks.
15. Team A cannot send back Team B's tasks.
16. Tasks cannot be marked Done through direct status updates.
17. Authorized human reviewers can approve their own tasks.

### Verified Test Results

| Metric | Result |
|---|---|
| Test Date | 27 November 2026 |
| Total Tests | 17 |
| Passed | 17 |
| Failed | 0 |
| Pass Rate | 100% |
| Execution Time | 388.179 seconds |
| Test Database | PostgreSQL |
| Django System Check | No issues |

Run the tests using:


python manage.py test core --keepdb -v 2


Verified terminal output:

Found 17 test(s).
System check identified no issues (0 silenced).

Ran 17 tests in 388.179s

OK


AI execution security tests use mocked AI calls to avoid
external API requests and unintended GitHub operations.

The application currently does not expose dedicated deletion
endpoints. Tests verify that unsupported deletion requests
do not remove protected records.


## Environment Configuration

Sensitive credentials are stored in a local `.env` file and excluded from Git using `.gitignore`.

Create a `.env` file in the project root.

### PostgreSQL Configuration

```env
DB_NAME=
DB_USER=
DB_PASSWORD=
DB_HOST=
DB_PORT=
```

### Django Configuration


DJANGO_SECRET_KEY=
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1


### OpenRouter Configuration


OPENROUTER_API_KEY=


### GitHub Configuration


GITHUB_TOKEN=
GITHUB_OWNER=
GITHUB_REPO=buildpilot-demo-output


Replace the empty values with your own configuration.

For deployment, configure the actual application hostname in `DJANGO_ALLOWED_HOSTS`.

The GitHub token should have access only to the demonstration output repository, with the minimum permissions required for repository contents and pull requests.

Never commit database passwords, Django secret keys, OpenRouter API keys, or GitHub access tokens.



## Django DEBUG Configuration

DEBUG is disabled by default.

The configuration in `config/settings.py` is:


DEBUG = os.getenv(
    'DJANGO_DEBUG',
    'False'
).lower() == 'true'


Production configuration:


DJANGO_DEBUG=False


Verify the effective DEBUG setting:


python manage.py shell -c "from django.conf import settings; print('DEBUG =', settings.DEBUG)"


Expected production output:


DEBUG = False


The Django secret key is loaded from the environment rather than being hardcoded in the application.



## Installation and Setup

### 1. Clone the Repository


git clone https://github.com/Nikhilkumar3065/Buildpilot.git
cd Buildpilot


### 2. Create a Virtual Environment


python -m venv venv


Activate the virtual environment on Windows:


venv\Scripts\activate


For Linux or macOS:


source venv/bin/activate


### 3. Install Dependencies


pip install -r requirements.txt


### 4. Configure Environment Variables

Create a `.env` file in the project root.

Provide the required PostgreSQL, Django, OpenRouter, and GitHub credentials.

A working PostgreSQL database is required.

### 5. Apply Database Migrations


python manage.py migrate


### 6. Verify Django Configuration


python manage.py check


### 7. Run Automated Tests


python manage.py test core --keepdb


### 8. Start the Development Server


python manage.py runserver

open the application:

http://127.0.0.1:8000/



## Demonstration Project — Scope Guard

Scope Guard is the demonstration software project used to showcase BuildPilot's AI-assisted development workflow.

The project addresses a common problem faced by small agencies: clients requesting additional work outside the originally agreed project scope.

The intended functionality includes:

- Track included project scope items.
- Track excluded project scope items.
- Record new client requests.
- Identify whether requests are in scope or require additional work.
- Organize development tasks.

BuildPilot is used to generate requirements, technical plans, and AI development tasks for the demonstration project.

AI-generated implementations are committed to a separate GitHub repository.

The complete Scope Guard functionality is still under development.

---

## Demonstrating AI Tool Calling

To demonstrate an AI build execution:

1. Sign in to BuildPilot.
2. Open a client problem.
3. Complete the requirements and technical planning workflow.
4. Approve the technical plan.
5. Open the task board.
6. Move a development task to Ready for AI.
7. Click Run AI.
8. Wait for the AI tool execution to finish.
9. Verify the generated branch and pull request in the demo repository.
10. Review the generated files and commits.
11. Approve the task or send it back with feedback.

A successful AI build run demonstrates the interaction between AI reasoning and native GitHub tools.

Actual tool execution results should be verified in GitHub rather than relying only on an AI-generated response.

---

## Project Repositories

### BuildPilot Application

https://github.com/Nikhilkumar3065/Buildpilot

Contains the Django application, database models, AI integration, GitHub tools, templates, and tests.

### AI-Generated Demo Output

https://github.com/Nikhilkumar3065/buildpilot-demo-output

Contains AI-generated software files, development branches, commits, and pull requests created through BuildPilot.

---

## Current Implementation Status

| Feature | Status |
|---|---|
| Django application setup | Implemented |
| PostgreSQL integration | Implemented |
| User signup and authentication | Implemented |
| Workspace management | Implemented |
| Client and problem management | Implemented |
| AI brainstorming | Implemented |
| Saved brainstorming conversations | Implemented |
| Requirements generation | Implemented |
| Requirements editing and version history | Implemented |
| Client requirements approval | Implemented |
| Technical plan generation | Implemented |
| Technical plan editing and approval | Implemented |
| Development task generation | Implemented |
| Six-status task board | Implemented |
| Native GitHub operations | Implemented |
| AI tool calling | Implemented |
| AI branch creation | Implemented |
| AI-generated commits | Implemented |
| Pull request creation | Implemented |
| Human approval | Implemented |
| Human review feedback | Implemented |
| Feedback-based AI rework | Implemented |
| Workspace access restrictions | Implemented and tested |
| DEBUG disabled by default | Implemented |
| Environment-based credentials | Implemented |
| Automated security tests | 17/17 tests passed |
| Fixed non-free AI model | Not configured |
| Complete human review details | Partially implemented |
| Automatic next-task selection | Pending |
| Timer-based AI execution | Pending |
| Bug reporting | Pending |
| AI bug fixing | Pending |
| Project-specific skill file | Pending |
| Persistent Run Log | Pending |
| Complete Scope Guard demonstration | In progress |
| Live deployment verification | Pending verification |

---

## Known Limitations

- The current AI configuration uses a free model router rather than one fixed non-free model.
- AI response quality and tool-calling reliability may vary.
- AI executions are currently initiated manually.
- Generated code requires human review and functional testing.
- Successful GitHub operations do not guarantee that generated software is functionally correct.
- Persistent execution logging is not yet complete.
- Complete AI implementation summaries and changed-file details are not yet stored for human review.
- Bug reporting and AI learning are planned features.
- Additional workspace isolation and permission tests are required.
- The demonstration repository is currently shared through one application-level configuration.

---

## Future Improvements

- Automatic selection of the next Ready for AI task.
- Timer-based AI build execution.
- Persistent AI and native tool execution logs.
- Additional repository file discovery tools.
- Bug reporting and AI-assisted bug fixing.
- Project-specific skill files and reusable lessons.
- Improved human review summaries.
- Additional security and workspace isolation tests.
- Improved execution limits and reliability.
- Completion of the Scope Guard demonstration.

---

## Development Approach

BuildPilot follows an AI-assisted development approach in which AI helps with understanding requirements, planning, implementation, and improvements.

Native application code controls database access, permissions, GitHub operations, and workflow state changes.

Human consultants remain responsible for reviewing requirements, approving plans, validating generated software, and approving completed tasks.

The project is being developed incrementally, with individual features implemented, tested, reviewed, and committed to GitHub.