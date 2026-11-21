from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.db import transaction
from django.contrib.auth.decorators import login_required


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