from django.urls import path
from . import views

urlpatterns = [
    path('signup/', views.signup, name='signup'),
    path('', views.home, name='home'),
    path('clients/', views.clients, name='clients'),
    path('problems/', views.problems, name='problems'),

    path(
        'brainstorm/<int:problem_id>/',
        views.brainstorm,
        name='brainstorm'
    ),
    path(
    'requirements/<int:problem_id>/',
    views.requirements,
    name='requirements'
    ),
    path(
        'technical_plan/<int:problem_id>/',
        views.technical_plan,
        name='technical_plan'
    ),
    path(
    'technical-plan/<int:problem_id>/',
    views.technical_plan,
    name='technical_plan'
    ),
    path(
        'task-board/<int:problem_id>/',
        views.task_board,
        name='task_board'
    ), 
        path(
        'run-ai/<int:problem_id>/<int:task_id>/',
        views.run_ai_task,
        name='run_ai_task'
    ),
    # Bug Reporting System

    path(
        'report-bug/<int:problem_id>/<int:task_id>/',
        views.report_bug,
        name='report_bug'
    ),

    path(
        'bug-reports/<int:problem_id>/',
        views.bug_reports,
        name='bug_reports'
    ),

    path(
    'bug-detail/<int:problem_id>/<int:bug_id>/',
        views.bug_detail,
        name='bug_detail'
    ),

    path(
        'update-bug-status/<int:problem_id>/<int:bug_id>/',
        views.update_bug_status,
        name='update_bug_status'
    ),
    path(
    'run-ai-bug/<int:problem_id>/<int:bug_id>/',
    views.run_ai_bug,
    name='run_ai_bug'
    ),
    path(
    'review-bug-fix/<int:problem_id>/<int:bug_id>/',
    views.review_bug_fix,
    name='review_bug_fix'
    ),
    path(
    'project-skill/<int:problem_id>/',
    views.project_skill,
    name='project_skill'
    ),

    path(
        'project-skill/<int:problem_id>/download/',
        views.download_project_skill,
        name='download_project_skill'
    ),
]