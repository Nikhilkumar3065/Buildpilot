# BuildPilot

BuildPilot is an application where consultants and AI collaborate to understand client problems, prepare requirements, create technical plans, and build software.

## Technology Stack

- Backend: Python, Django
- Database: PostgreSQL (Supabase)
- Database Driver: Psycopg
- Frontend: HTML, CSS, JavaScript

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

## Database

- Provider: Supabase
- Database: PostgreSQL
- Schema: public

## Current Implementation

- Django project setup
- Supabase PostgreSQL connection
- User signup
- Workspace creation
- Workspace membership
- Automatic login after signup
- Workspace display on home page
