BuildPilot

BuildPilot is a web application where consultants and AI collaborate to understand client problems, prepare requirements, create technical plans, and organize software development tasks.

The application helps consultants convert client problems written in simple English into structured requirements and technical plans. AI assists with understanding and planning, while consultants review and approve important decisions.

Technology Stack

Component

Technology

Backend

Python, Django

Frontend

HTML, CSS, JavaScript

Database

PostgreSQL

Database Hosting

Supabase

Database Driver

Psycopg

AI Integration

OpenRouter API

AI Model

openrouter/free

Version Control

Git, GitHub

Environment Configuration

python-dotenv

Features

1. User Signup and Workspace Management

User registration and automatic login.

Workspace creation during signup.

Workspace membership management.

Workspace-based data separation.

2. Client and Problem Management

Create clients using name and email.

Submit client problems in simple English.

View clients and problems belonging to the user's workspace.

3. AI Brainstorming

AI asks questions to understand the client's problem.

AI suggests ideas for further discussion.

Consultants can answer questions and add ideas.

Brainstorming conversations are saved.

4. Requirements Document

AI generates a requirements document containing:

Problem Statement

Users

Must Do

Must Not Do

Success Criteria

Open Questions

Consultants can edit the requirements. Each edit is saved as a new version. The document can be approved by the client.

5. Technical Plan

AI generates a technical plan from the approved requirements.

The plan includes database tables, screens, and development tasks.

Consultants can review, edit, and approve the plan.

Approved plans are used to generate development tasks.

6. Task Board

The task board organizes development tasks using six statuses:

Status

Description

Backlog

Tasks waiting to be prepared

Ready for AI

Tasks waiting for an AI build run

AI Building

AI is working on the task

Needs Human Check

Work is waiting for review

Done

Work approved by a human

Sent Back

Work returned for changes

Tasks are displayed in their development order, and their statuses can be updated through the task board.

Database Structure

BuildPilot uses PostgreSQL hosted on Supabase.

Workspace-owned records are associated with a workspace using workspace_id to support workspace-level data isolation.

Database Table

Important Columns

core_workspace

id, name, created_at

core_workspacemember

id, workspace_id, user_id, joined_at

core_client

id, workspace_id, name, email, created_at

core_problem

id, workspace_id, client_id, description, created_at

core_brainstormsession

id, workspace_id, problem_id, created_at

core_brainstormmessage

id, workspace_id, session_id, sender, message, created_at

core_requirementdocument

id, workspace_id, problem_id, status, approved_at, created_at

core_requirementversion

id, document_id, workspace_id, version_number, problem_statement, users, must_do, must_not_do, success_criteria, open_questions, created_at

core_technicalplan

id, workspace_id, problem_id, content, status, approved_at, created_at

core_task

id, workspace_id, technical_plan_id, title, description, status, task_order, created_at

Django's built-in authentication tables are also used for user accounts.

AI Integration

Provider: OpenRouter

Model configured: openrouter/free

Execution: OpenRouter API

Usage: AI brainstorming, requirements generation, and technical planning.

Purpose: Provides AI-generated responses to assist consultants during the project workflow.

The configured free router can select from available models. It is used for initial development and testing.

Workspace Security

BuildPilot applies workspace-based access restrictions.

Users can access records belonging to their own workspace.

Client and problem listings are filtered by workspace.

Workflow pages check workspace ownership before displaying a problem.

Task updates check workspace and technical plan ownership.

Unauthenticated users are redirected to the signup page.

Automated Security Tests

Security tests are located in core/tests.py.

The seven automated tests verify:

Team A cannot view Team B's clients.

Team A cannot view Team B's problems.

Team A cannot access Team B's workflow pages.

Team A cannot modify Team B's tasks.

Team A cannot create problems using Team B's client records.

Delete endpoints are not exposed in the current application.

Unauthenticated users cannot access protected pages.

Test result: 7 tests passed.

Run the tests using:

python manage.py test core --keepdb

Environment Configuration

Sensitive credentials are stored in a local .env file and excluded from Git using .gitignore.

Environment variables used by the application:

DB_NAME=
DB_USER=
DB_PASSWORD=
DB_HOST=
DB_PORT=

DJANGO_SECRET_KEY=
DJANGO_DEBUG=
DJANGO_ALLOWED_HOSTS=

OPENROUTER_API_KEY=

Never commit database passwords, Django secret keys, or API keys to GitHub.

Installation and Setup

1. Clone the Repository

git clone https://github.com/Nikhilkumar3065/Buildpilot.git
cd Buildpilot

2. Create a Virtual Environment

python -m venv venv

Activate it on Windows:

venv\Scripts\activate

3. Install Dependencies

pip install -r requirements.txt

4. Configure Environment Variables

Create a .env file in the project root and provide the required PostgreSQL, Django, and OpenRouter credentials.

5. Apply Database Migrations

python manage.py migrate

6. Start the Development Server

python manage.py runserver

Open:

http://127.0.0.1:8000/

Project Repository

GitHub: https://github.com/Nikhilkumar3065/Buildpilot

Current Implementation

BuildPilot currently includes:

Django project and PostgreSQL database integration.

User signup and workspace creation.

Workspace membership.

Client and problem management.

AI brainstorming with saved conversations.

AI-generated requirements documents.

Requirements editing and version history.

Client approval of requirements.

AI-generated technical plans.

Technical plan editing and approval.

Development task generation.

Task board with six statuses.

Workspace-based access restrictions.

Seven automated workspace security tests.