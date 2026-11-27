from django.test import TestCase, Client as DjangoClient
from django.contrib.auth.models import User
from django.urls import reverse

from .models import (
    Workspace,
    WorkspaceMember,
    Client as ClientModel,
    Problem,
    TechnicalPlan,
    Task,
)


class WorkspaceSecurityTests(TestCase):

    def setUp(self):
        # Create Team A
        self.user_a = User.objects.create_user(
            username="team_a_user",
            password="TestPassword123!"
        )
        self.workspace_a = Workspace.objects.create(
            name="Team A Workspace"
        )
        WorkspaceMember.objects.create(
            user=self.user_a,
            workspace=self.workspace_a
        )

        # Create Team B
        self.user_b = User.objects.create_user(
            username="team_b_user",
            password="TestPassword123!"
        )
        self.workspace_b = Workspace.objects.create(
            name="Team B Workspace"
        )
        WorkspaceMember.objects.create(
            user=self.user_b,
            workspace=self.workspace_b
        )

        # Create Team A client and problem
        self.client_a = ClientModel.objects.create(
            workspace=self.workspace_a,
            name="Team A Client",
            email="clienta@example.com"
        )
        self.problem_a = Problem.objects.create(
            workspace=self.workspace_a,
            client=self.client_a,
            description="Team A problem"
        )

        # Create Team B client and problem
        self.client_b = ClientModel.objects.create(
            workspace=self.workspace_b,
            name="Team B Private Client",
            email="clientb@example.com"
        )
        self.problem_b = Problem.objects.create(
            workspace=self.workspace_b,
            client=self.client_b,
            description="Team B private problem"
        )

        # Create approved plans for both teams
        self.plan_a = TechnicalPlan.objects.create(
            workspace=self.workspace_a,
            problem=self.problem_a,
            content="Team A technical plan",
            status="approved"
        )
        self.plan_b = TechnicalPlan.objects.create(
            workspace=self.workspace_b,
            problem=self.problem_b,
            content="Team B technical plan",
            status="approved"
        )

        # Create a task belonging to Team B
        self.task_b = Task.objects.create(
            workspace=self.workspace_b,
            technical_plan=self.plan_b,
            title="Team B private task",
            description="This task belongs to Team B",
            status="backlog",
            task_order=1
        )

        # Log in as Team A
        self.browser = DjangoClient()
        self.browser.force_login(self.user_a)

    def test_team_a_cannot_view_team_b_clients(self):
        response = self.browser.get(reverse("clients"))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(
            response,
            "Team B Private Client"
        )

    def test_team_a_cannot_view_team_b_problems(self):
        response = self.browser.get(reverse("problems"))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(
            response,
            "Team B private problem"
        )

    def test_team_a_cannot_open_team_b_problem_pages(self):
        protected_urls = [
            reverse(
                "brainstorm",
                args=[self.problem_b.id]
            ),
            reverse(
                "requirements",
                args=[self.problem_b.id]
            ),
            reverse(
                "technical_plan",
                args=[self.problem_b.id]
            ),
            reverse(
                "task_board",
                args=[self.problem_b.id]
            ),
        ]

        for url in protected_urls:
            with self.subTest(url=url):
                response = self.browser.get(url)

                self.assertRedirects(
                    response,
                    reverse("problems"),
                    fetch_redirect_response=False
                )

    def test_team_a_cannot_change_team_b_task(self):
        response = self.browser.post(
            reverse(
                "task_board",
                args=[self.problem_a.id]
            ),
            {
                "task_id": self.task_b.id,
                "status": "done",
            }
        )

        self.assertEqual(response.status_code, 302)

        self.task_b.refresh_from_db()

        self.assertEqual(
            self.task_b.status,
            "backlog"
        )

    def test_team_a_cannot_create_problem_for_team_b_client(self):
        initial_count = Problem.objects.count()

        self.browser.post(
            reverse("problems"),
            {
                "client": self.client_b.id,
                "description": "Unauthorized problem",
            }
        )

        self.assertEqual(
            Problem.objects.count(),
            initial_count
        )

    def test_delete_urls_are_not_exposed(self):
        # The current application has no delete URL patterns.
        urls = [
            f"/clients/{self.client_b.id}/delete/",
            f"/problems/{self.problem_b.id}/delete/",
            f"/tasks/{self.task_b.id}/delete/",
        ]

        for url in urls:
            with self.subTest(url=url):
                response = self.browser.post(url)
                self.assertEqual(response.status_code, 404)

    def test_unauthenticated_user_cannot_access_protected_pages(self):
        anonymous_browser = DjangoClient()

        protected_urls = [
            reverse("home"),
            reverse("clients"),
            reverse("problems"),
            reverse("brainstorm", args=[self.problem_a.id]),
            reverse("requirements", args=[self.problem_a.id]),
            reverse("technical_plan", args=[self.problem_a.id]),
            reverse("task_board", args=[self.problem_a.id]),
        ]

        for url in protected_urls:
            with self.subTest(url=url):
                response = anonymous_browser.get(url)

                self.assertEqual(response.status_code, 302)
                self.assertTrue(
                    response.url.startswith("/signup/")
                )
