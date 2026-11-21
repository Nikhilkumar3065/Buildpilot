# BuildPilot

BuildPilot is an application where consultants and AI collaborate to understand client problems, prepare requirements, create technical plans, and build software.

## Technology Stack

- **Backend:** Python, Django
- **Database:** PostgreSQL (Supabase)
- **Database Driver:** Psycopg
- **Frontend:** HTML, CSS, JavaScript
- **Version Control:** Git and GitHub

## Database Tables

### 1. core_workspace

Stores workspace information.

| Column | Description |
|---|---|
| id | Primary key |
| name | Workspace name |
| created_at | Workspace creation date and time |

### 2. core_workspacemember

Connects users to their workspaces.

| Column | Description |
|---|---|
| id | Primary key |
| workspace_id | Foreign key referencing core_workspace |
| user_id | Foreign key referencing Django auth_user |
| joined_at | Membership creation date and time |

### 3. core_client

Stores client information associated with a workspace.

| Column | Description |
|---|---|
| id | Primary key |
| workspace_id | Foreign key referencing core_workspace |
| name | Client name |
| email | Client email address |
| created_at | Client creation date and time |

### 4. core_problem

Stores client problems and descriptions associated with a workspace.

| Column | Description |
|---|---|
| id | Primary key |
| workspace_id | Foreign key referencing core_workspace |
| client_id | Foreign key referencing core_client |
| description | Client problem description in plain English |
| created_at | Problem creation date and time |

## Database

- **Provider:** Supabase
- **Database:** PostgreSQL
- **Schema:** public

## Current Implementation

- Django project setup
- Supabase PostgreSQL connection
- User signup
- Workspace creation
- Workspace membership
- Automatic login after signup
- Workspace display on home page
- Client creation with name and email
- Workspace-based client listing
- Client problem submission
- Client selection when submitting a problem
- Workspace-based problem listing
- Workspace-level filtering for clients and problems

## Project Repository

GitHub - BuildPilot : https://github.com/Nikhilkumar3065/Buildpilot

## Tools

| Tool Name | Who Runs It | Purpose |
|---|---|---|
| create_branch | Code | Creates a new Git branch for AI changes |
| list_files | Code | Lists files in the project repository |
| read_file | Code | Reads a file from the repository |
| commit_and_push | Code | Commits changes and pushes them to GitHub |
| open_pull_request | Code | Creates a pull request for review |
| change_task_status | Code | Updates the status of a task |
| save_lesson | Code | Saves a lesson learned from a bug or task |
| check_permission | Code | Checks whether an operation is permitted |

These tools are planned for implementation and testing during the upcoming development days

## AI Model

- Model: GLM 5.3 Flash
- Provider: OpenRouter
- Hosting: OpenRouter API
- Reason: Supports tool calling and is suitable for coding and AI agent workflows.