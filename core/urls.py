from django.urls import path
from . import views

urlpatterns = [
    path('signup/', views.signup, name='signup'),
    path('', views.home, name='home'),
    path('clients/', views.clients, name='clients'),
    path('problems/', views.problems, name='problems'),
]