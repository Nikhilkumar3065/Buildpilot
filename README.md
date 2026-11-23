BuildPilot

BuildPilot is an application where consultants and AI collaborate to understand client problems, prepare requirements, create technical plans, and build software.

The goal is to help consultants understand client requirements in plain English while AI assists with planning, coding, debugging, and software development. Human consultants review and approve the work at important stages.

Project Objectives

Understand client problems written in simple language.

Use AI to brainstorm and clarify requirements.

Generate editable requirements documents.

Create technical plans from approved requirements.

Convert technical plans into development tasks.

Allow AI to build software through controlled development runs.

Keep humans responsible for reviewing and approving AI-generated code.

Learn from bugs and save project-specific lessons for future AI runs.

Technology Stack

Component

Technology

Backend

Python, Django

Database

PostgreSQL

Database Hosting

Supabase

Database Driver

Psycopg

Frontend

HTML, CSS, JavaScript

AI Integration

OpenRouter API

AI Model

OpenRouter Free Router (openrouter/free) for initial development testing

Version Control

Git and GitHub

Environment Configuration

Python dotenv

Core Workflow

BuildPilot follows a seven-step workflow.

1. Client Problem

Consultant creates a client using name and email.

Consultant describes the client's problem in simple English.

The application saves the client and problem in the consultant's workspace.

2. Brainstorm

AI asks questions one at a time.

AI suggests ideas to help understand the problem.

Consultant answers questions and adds ideas.

The complete brainstorming conversation is saved.

3. Requirements Document

AI generates a plain-English requirements document containing:

Problem Statement

Users

Must Do

Must Not Do

Success Criteria

Open Questions

The consultant can edit the document. Every edit creates a new version. Once the client agrees, the consultant selects Approved by Client.

4. Technical Plan

AI reads the approved requirements document.

AI prepares a technical plan.

The plan includes database tables, screens, development tasks, and development order.

Consultant reviews and approves the technical plan.

Approved plans generate development tasks for the task board.

5. AI Build Run

Consultant moves a task to Ready for AI.

AI picks up eligible tasks during the next build run.

AI creates a separate Git branch.

AI reads project files and writes code.

AI commits and pushes changes.

AI opens a pull request.

The task moves to Needs Human Check.

Build runs can be started manually and through a timer.

6. Human Check

The consultant reviews:

AI-generated code summary.

Files changed.

Git branch.

Pull request link.

The consultant can:

Approve the work, moving the task to Done.

Send the task back with a comment.

Only a human can mark a task as Done.

7. Bugs and Learning

Consultant reports a bug with title, steps, expected result, actual result, and related task.

AI investigates the cause and fixes the bug on a new branch.

AI writes a lesson based on the issue.

Lessons are saved in a project-specific skill file.

Every future AI build run reads the project's skill file first.

Consultant can read and edit the saved lessons.

Database Tables

BuildPilot uses PostgreSQL hosted on Supabase.

All workspace-owned business records are associated with a workspace using workspace_id to support workspace-level data isolation. The Workspace table is the root workspace record.

Table

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

Task Board

The task board supports six required statuses:

Status

Description

Backlog

Tasks waiting to be prepared

Ready for AI

Tasks waiting for an AI build run

AI Building

AI is currently working on the task

Needs Human Check

AI work is waiting for consultant review

Done

Work approved by a human

Sent Back

Work returned for changes

Tasks are generated from the approved technical plan and displayed on the task board.

Native GitHub Tools

BuildPilot uses native code-based tools for repository operations.

Tool Name

Who Runs It

Purpose

create_branch

Code

Creates a new Git branch

list_files

Code

Lists files in the project repository

read_file

Code

Reads a file from the repository

commit_and_push

Code

Commits changes and pushes them to GitHub

open_pull_request

Code

Creates a pull request for review

change_task_status

Code

Updates a task's status

save_lesson

Code

Saves a lesson learned from a bug or task

check_permission

Code

Checks whether an operation is permitted

AI responsibilities: Ask questions, generate requirements, prepare technical plans, select files, write code, investigate bugs, and write lessons.

Code responsibilities: Execute repository operations, enforce permissions, update task statuses, save lessons, and maintain run records.

AI decides when to call the available native tools. Each run must have limits on the number of steps and cost.

AI Model

Initial development model: openrouter/free

Provider: OpenRouter

Hosting: OpenRouter API

Purpose: AI-powered brainstorming, requirements generation, and technical planning.

Development testing: Successfully tested with an AI chat completion request.

The final AI build-run model must support tool calling. The selected model must be checked against the available model list before implementation. Free models may have rate limits and are not relied upon for the final demonstration.

The final selected model name, hosting provider, and reason for selection will be documented here after verification.

Security and Workspace Isolation

BuildPilot must enforce the following security requirements:

Every workspace-owned business record must be associated with its workspace.

Team A must never access Team B's clients, problems, documents, tasks, repositories, runs, or lessons.

Workspace access must be checked on the backend.

Requests without authentication must not access protected resources.

GitHub tokens and AI API keys must be stored in environment variables.

API keys must never be committed to GitHub or exposed in the application or demonstration video.

GitHub access must be restricted to the designated demo repository.

AI can only modify branches whose names start with ai/.

AI must never push directly to the main branch.

AI must never delete repository content.

AI must never mark a task as Done.

Permission checks must be implemented in code, not only in AI prompts.

Workspace isolation will be tested using two separate teams, including attempts to access and modify another team's records by ID and requests without authentication.

AI Build Run Log

Every AI build run must save a record of its execution.

The Run Log must capture:

Each execution step.

Tool name.

Input.

Result.

Execution time.

Whether the step was performed by code or AI.

This provides visibility into how the AI builds software and how native tools are used.

Demo Application: Scope Guard

The demonstration application is called Scope Guard.

Problem

Small software agencies often receive additional client requests that are not included in the original project scope.

Objective

Build a simple application that helps agencies distinguish between included work and extra work.

Main Requirements

Maintain client and project information.

Maintain Included and Not Included scope items.

Manage project tasks.

Allow consultants to submit new client requests.

Classify each request as In Scope or Extra Work.

Display the classification result and explanation.

BuildPilot must generate the Scope Guard technical plan and use AI build runs to implement at least three tasks in a separate public GitHub repository named:

buildpilot-demo-output

Scope Guard must be created through BuildPilot's workflow rather than manually coded as a separate application.

Development Stages

Stage 1 — Days 1–6

Target submission: Wednesday, November 25, 2026.

Project setup and database.

User signup and workspace creation.

Client and problem management.

Brainstorming conversation.

Requirements document and versioning.

Client approval.

Technical plan generation and approval.

Task board and task statuses.

Native GitHub tools working through simple buttons.

AI model tool-calling test.

Workspace isolation testing.

Deployment and demonstration video.

Stage 2 — Days 7–10

Target submission: Sunday, November 29, 2026.

AI build-run implementation.

AI branch creation.

AI code generation.

Git commit and push.

Pull request creation.

Human review and approval.

Send-back workflow.

Bug reporting and AI bug fixing.

Project-specific skill file.

Run Log.

Final Tools table.

Deployment and final demonstration video.

Submission Requirements

Stage 1 Submission

Live application link.

Public BuildPilot GitHub repository.

5–10 minute Loom demonstration with camera.

Demonstrate workflow steps 1–4 using the demo client.

Demonstrate GitHub branch creation and pull request.

Demonstrate that two teams cannot access each other's data.

Stage 2 Submission

Live application link.

Public BuildPilot GitHub repository.

Public buildpilot-demo-output repository.

10–15 minute Loom demonstration with camera.

Demonstrate the complete BuildPilot workflow.

Demonstrate at least three AI-built tasks.

Demonstrate a task being sent back.

Demonstrate bug reporting and AI bug fixing.

Demonstrate lessons saved in the project skill file.

Demonstrate a later AI run using the saved lessons.

Demonstrate the Run Log and Tools table.

Include a short note explaining what broke and how it was fixed.

Current Implementation

The following features have been implemented and tested:

Django project setup.

Supabase PostgreSQL connection.

User signup.

Workspace creation.

Workspace membership.

Automatic login after signup.

Workspace display on home page.

Client creation with name and email.

Workspace-based client listing.

Client problem submission.

Workspace-based problem listing.

Brainstorming conversation with AI.

Saving consultant and AI messages.

AI-generated requirements document.

Editing requirements and saving new versions.

Client approval of requirements.

AI-generated technical plan.

Technical plan editing and approval.

AI-generated development tasks.

Task board with six required statuses.

Task status updates.

Workspace-scoped task board access.

Project Repository

GitHub: https://github.com/Nikhilkumar3065/Buildpilot

Database Configuration

Provider: Supabase

Database: PostgreSQL

Schema: public

Connection: Django PostgreSQL backend using Psycopg

Environment configuration: .env

Sensitive credentials and API keys are excluded from Git using .gitignore.

Development Principles

Follow the specified seven-step workflow.

Keep the Scope Guard demonstration application small.

Use AI for planning and coding, with human review.

Use code for native tools and security enforcement.

Preserve workspace-level data isolation.

Keep every development run traceable.

Use small, meaningful Git commits.

Understand and test all AI-generated code before accepting it.

Project Name: BuildPilot
Repository: Nikhilkumar3065/Buildpilot
Database: PostgreSQL (Supabase)
Backend: Django and Python
AI Integration: OpenRouter API