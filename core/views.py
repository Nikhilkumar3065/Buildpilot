from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.db import transaction
from django.contrib.auth.decorators import login_required
from .forms import ClientForm, ProblemForm
from .models import Client, Problem

from .models import Workspace, WorkspaceMember


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