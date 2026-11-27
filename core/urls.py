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
]
