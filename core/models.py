from django.db import models
from django.contrib.auth.models import User


# Workspace
class Workspace(models.Model):
    name = models.CharField(max_length=150)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


# Workspace Members
class WorkspaceMember(models.Model):
    workspace = models.ForeignKey(
        Workspace,
        on_delete=models.CASCADE,
        related_name='members'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='workspace_memberships'
    )
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('workspace', 'user')

    def __str__(self):
        return f"{self.user.username} - {self.workspace.name}"


# Clients
class Client(models.Model):
    workspace = models.ForeignKey(
        Workspace,
        on_delete=models.CASCADE,
        related_name='clients'
    )
    name = models.CharField(max_length=150)
    email = models.EmailField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


# Client Problems
class Problem(models.Model):
    workspace = models.ForeignKey(
        Workspace,
        on_delete=models.CASCADE,
        related_name='problems'
    )
    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name='problems'
    )
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Problem for {self.client.name}"


# Brainstorming Sessions
class BrainstormSession(models.Model):
    workspace = models.ForeignKey(
        Workspace,
        on_delete=models.CASCADE,
        related_name='brainstorm_sessions'
    )
    problem = models.ForeignKey(
        Problem,
        on_delete=models.CASCADE,
        related_name='brainstorm_sessions'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Brainstorming - {self.problem.client.name}"


# Brainstorming Messages
class BrainstormMessage(models.Model):

    SENDER_CHOICES = [
        ('consultant', 'Consultant'),
        ('ai', 'AI'),
    ]

    workspace = models.ForeignKey(
        Workspace,
        on_delete=models.CASCADE,
        related_name='brainstorm_messages'
    )
    session = models.ForeignKey(
        BrainstormSession,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    sender = models.CharField(
        max_length=20,
        choices=SENDER_CHOICES
    )
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.sender}: {self.message[:50]}"


# Requirements Document
class RequirementDocument(models.Model):

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('approved', 'Approved by client'),
    ]

    workspace = models.ForeignKey(
        Workspace,
        on_delete=models.CASCADE,
        related_name='requirement_documents'
    )
    problem = models.ForeignKey(
        Problem,
        on_delete=models.CASCADE,
        related_name='requirement_documents'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Requirements - {self.problem.client.name}"


# Requirements Document Versions
class RequirementVersion(models.Model):

    document = models.ForeignKey(
        RequirementDocument,
        on_delete=models.CASCADE,
        related_name='versions'
    )
    workspace = models.ForeignKey(
        Workspace,
        on_delete=models.CASCADE,
        related_name='requirement_versions'
    )
    version_number = models.PositiveIntegerField()

    problem_statement = models.TextField()
    users = models.TextField()
    must_do = models.TextField()
    must_not_do = models.TextField()
    success_criteria = models.TextField()
    open_questions = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('document', 'version_number')
        ordering = ['-version_number']

    def __str__(self):
        return f"Version {self.version_number}"
class TechnicalPlan(models.Model):

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('approved', 'Approved'),
    ]

    workspace = models.ForeignKey(
        Workspace,
        on_delete=models.CASCADE
    )

    problem = models.ForeignKey(
        Problem,
        on_delete=models.CASCADE
    )

    content = models.TextField()

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft'
    )

    approved_at = models.DateTimeField(
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"Technical Plan - {self.problem}"

class Task(models.Model):

    STATUS_CHOICES = [
        ('backlog', 'Backlog'),
        ('ready_ai', 'Ready for AI'),
        ('ai_building', 'AI Building'),
        ('needs_human_check', 'Needs Human Check'),
        ('done', 'Done'),
        ('sent_back', 'Sent Back'),
    ]

    workspace = models.ForeignKey(
        Workspace,
        on_delete=models.CASCADE
    )

    technical_plan = models.ForeignKey(
        TechnicalPlan,
        on_delete=models.CASCADE,
        related_name='tasks'
    )

    title = models.CharField(
        max_length=200
    )

    description = models.TextField()

    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default='backlog'
    )

    task_order = models.PositiveIntegerField(
        default=1
    )

    # Human review feedback
    review_comment = models.TextField(
        blank=True,
        default=''
    )

    # Human review timestamp
    reviewed_at = models.DateTimeField(
        null=True,
        blank=True
    )
        # AI-generated GitHub branch
    ai_branch = models.CharField(
        max_length=255,
        blank=True,
        default=''
    )

    # GitHub pull request URL
    pull_request_url = models.URLField(
        blank=True,
        default=''
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.title
