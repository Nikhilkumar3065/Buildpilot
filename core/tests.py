from unittest.mock import patch

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

        # Create Team A client
        self.client_a = ClientModel.objects.create(
            workspace=self.workspace_a,
            name="Team A Client",
            email="clienta@example.com"
        )

        # Create Team A problem
        self.problem_a = Problem.objects.create(
            workspace=self.workspace_a,
            client=self.client_a,
            description="Team A problem"
        )

        # Create Team B client
        self.client_b = ClientModel.objects.create(
            workspace=self.workspace_b,
            name="Team B Private Client",
            email="clientb@example.com"
        )

        # Create Team B problem
        self.problem_b = Problem.objects.create(
            workspace=self.workspace_b,
            client=self.client_b,
            description="Team B private problem"
        )

        # Create approved technical plan for Team A
        self.plan_a = TechnicalPlan.objects.create(
            workspace=self.workspace_a,
            problem=self.problem_a,
            content="Team A technical plan",
            status="approved"
        )

        # Create approved technical plan for Team B
        self.plan_b = TechnicalPlan.objects.create(
            workspace=self.workspace_b,
            problem=self.problem_b,
            content="Team B technical plan",
            status="approved"
        )

        # Create Team A task
        self.task_a = Task.objects.create(
            workspace=self.workspace_a,
            technical_plan=self.plan_a,
            title="Team A task",
            description="This task belongs to Team A",
            status="backlog",
            task_order=1
        )

        # Create Team B task
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

        # Log in as Team B
        self.browser_b = DjangoClient()
        self.browser_b.force_login(self.user_b)

    # TEST 1: Client isolation

    def test_team_a_cannot_view_team_b_clients(self):

        response = self.browser.get(
            reverse("clients")
        )

        self.assertEqual(response.status_code, 200)

        self.assertContains(
            response,
            "Team A Client"
        )

        self.assertNotContains(
            response,
            "Team B Private Client"
        )

    # TEST 2: Problem isolation

    def test_team_a_cannot_view_team_b_problems(self):

        response = self.browser.get(
            reverse("problems")
        )

        self.assertEqual(response.status_code, 200)

        self.assertContains(
            response,
            "Team A problem"
        )

        self.assertNotContains(
            response,
            "Team B private problem"
        )

    # TEST 3: Reverse client isolation

    def test_team_b_cannot_view_team_a_clients(self):

        response = self.browser_b.get(
            reverse("clients")
        )

        self.assertEqual(response.status_code, 200)

        self.assertContains(
            response,
            "Team B Private Client"
        )

        self.assertNotContains(
            response,
            "Team A Client"
        )

    # TEST 4: Reverse problem isolation

    def test_team_b_cannot_view_team_a_problems(self):

        response = self.browser_b.get(
            reverse("problems")
        )

        self.assertEqual(response.status_code, 200)

        self.assertContains(
            response,
            "Team B private problem"
        )

        self.assertNotContains(
            response,
            "Team A problem"
        )

    # TEST 5: Direct URL access protection

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

    # TEST 6: Task board isolation

    def test_team_a_cannot_view_team_b_tasks(self):

        response = self.browser.get(
            reverse(
                "task_board",
                args=[self.problem_a.id]
            )
        )

        self.assertEqual(response.status_code, 200)

        self.assertContains(
            response,
            "Team A task"
        )

        self.assertNotContains(
            response,
            "Team B private task"
        )

    # TEST 7: Unauthorized task modification

    def test_team_a_cannot_change_team_b_task(self):

        response = self.browser.post(
            reverse(
                "task_board",
                args=[self.problem_a.id]
            ),
            {
                "action": "update_status",
                "task_id": self.task_b.id,
                "status": "ready_ai",
            }
        )

        self.assertIn(
            response.status_code,
            [302, 403, 404]
        )

        self.task_b.refresh_from_db()

        self.assertEqual(
            self.task_b.status,
            "backlog"
        )

    # TEST 8: Authorized task modification

    def test_team_a_can_update_own_task(self):

        response = self.browser.post(
            reverse(
                "task_board",
                args=[self.problem_a.id]
            ),
            {
                "action": "update_status",
                "task_id": self.task_a.id,
                "status": "ready_ai",
            }
        )

        self.assertEqual(
            response.status_code,
            302
        )

        self.task_a.refresh_from_db()

        self.assertEqual(
            self.task_a.status,
            "ready_ai"
        )

    # TEST 9: Unauthorized client association

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

    # TEST 10: Unauthorized deletion attempts

    def test_delete_urls_are_not_exposed(self):

        urls = [
            f"/clients/{self.client_b.id}/delete/",
            f"/problems/{self.problem_b.id}/delete/",
            f"/tasks/{self.task_b.id}/delete/",
        ]

        for url in urls:

            with self.subTest(url=url):

                response = self.browser.post(url)

                self.assertEqual(
                    response.status_code,
                    404
                )

        # Verify records still exist

        self.assertTrue(
            ClientModel.objects.filter(
                id=self.client_b.id
            ).exists()
        )

        self.assertTrue(
            Problem.objects.filter(
                id=self.problem_b.id
            ).exists()
        )

        self.assertTrue(
            Task.objects.filter(
                id=self.task_b.id
            ).exists()
        )

    # TEST 11: Unauthenticated page access

    def test_unauthenticated_user_cannot_access_protected_pages(self):

        anonymous_browser = DjangoClient()

        protected_urls = [
            reverse("home"),
            reverse("clients"),
            reverse("problems"),
            reverse(
                "brainstorm",
                args=[self.problem_a.id]
            ),
            reverse(
                "requirements",
                args=[self.problem_a.id]
            ),
            reverse(
                "technical_plan",
                args=[self.problem_a.id]
            ),
            reverse(
                "task_board",
                args=[self.problem_a.id]
            ),
        ]

        for url in protected_urls:

            with self.subTest(url=url):

                response = anonymous_browser.get(url)

                self.assertEqual(
                    response.status_code,
                    302
                )

                self.assertTrue(
                    response.url.startswith("/signup/")
                )

    # TEST 12: Unauthorized AI execution

    @patch("core.views.run_ai_build")
    def test_team_a_cannot_run_ai_on_team_b_task(
        self,
        mock_run_ai_build
    ):

        self.task_b.status = "ready_ai"
        self.task_b.save(update_fields=["status"])

        unauthorized_urls = [
            reverse(
                "run_ai_task",
                args=[
                    self.problem_b.id,
                    self.task_b.id
                ]
            ),
            reverse(
                "run_ai_task",
                args=[
                    self.problem_a.id,
                    self.task_b.id
                ]
            ),
        ]

        for url in unauthorized_urls:

            with self.subTest(url=url):

                response = self.browser.post(url)

                self.assertIn(
                    response.status_code,
                    [302, 403, 404]
                )

        mock_run_ai_build.assert_not_called()

        self.task_b.refresh_from_db()

        self.assertEqual(
            self.task_b.status,
            "ready_ai"
        )

    # TEST 13: Logged-out AI execution

    @patch("core.views.run_ai_build")
    def test_unauthenticated_user_cannot_run_ai(
        self,
        mock_run_ai_build
    ):

        anonymous_browser = DjangoClient()

        self.task_a.status = "ready_ai"
        self.task_a.save(update_fields=["status"])

        response = anonymous_browser.post(
            reverse(
                "run_ai_task",
                args=[
                    self.problem_a.id,
                    self.task_a.id
                ]
            )
        )

        self.assertEqual(
            response.status_code,
            302
        )

        self.assertTrue(
            response.url.startswith("/signup/")
        )

        mock_run_ai_build.assert_not_called()

        self.task_a.refresh_from_db()

        self.assertEqual(
            self.task_a.status,
            "ready_ai"
        )

    # TEST 14: Unauthorized human approval

    def test_team_a_cannot_approve_team_b_task(self):

        self.task_b.status = "needs_human_check"

        self.task_b.save(
            update_fields=["status"]
        )

        response = self.browser.post(
            reverse(
                "task_board",
                args=[self.problem_a.id]
            ),
            {
                "action": "approve",
                "task_id": self.task_b.id,
            }
        )

        self.assertIn(
            response.status_code,
            [302, 403, 404]
        )

        self.task_b.refresh_from_db()

        self.assertEqual(
            self.task_b.status,
            "needs_human_check"
        )

        self.assertIsNone(
            self.task_b.reviewed_at
        )

    # TEST 15: Unauthorized human feedback

    def test_team_a_cannot_send_back_team_b_task(self):

        self.task_b.status = "needs_human_check"

        self.task_b.save(
            update_fields=["status"]
        )

        response = self.browser.post(
            reverse(
                "task_board",
                args=[self.problem_a.id]
            ),
            {
                "action": "send_back",
                "task_id": self.task_b.id,
                "review_comment": "Unauthorized feedback",
            }
        )

        self.assertIn(
            response.status_code,
            [302, 403, 404]
        )

        self.task_b.refresh_from_db()

        self.assertEqual(
            self.task_b.status,
            "needs_human_check"
        )

        self.assertEqual(
            self.task_b.review_comment,
            ""
        )

        self.assertIsNone(
            self.task_b.reviewed_at
        )

    # TEST 16: Prevent direct Done status

    def test_task_cannot_be_marked_done_using_status_update(self):

        response = self.browser.post(
            reverse(
                "task_board",
                args=[self.problem_a.id]
            ),
            {
                "action": "update_status",
                "task_id": self.task_a.id,
                "status": "done",
            }
        )

        self.assertIn(
            response.status_code,
            [302, 400, 403]
        )

        self.task_a.refresh_from_db()

        self.assertEqual(
            self.task_a.status,
            "backlog"
        )

    # TEST 17: Authorized human approval

    def test_human_can_approve_own_task(self):

        self.task_a.status = "needs_human_check"

        self.task_a.save(
            update_fields=["status"]
        )

        response = self.browser.post(
            reverse(
                "task_board",
                args=[self.problem_a.id]
            ),
            {
                "action": "approve",
                "task_id": self.task_a.id,
            }
        )

        self.assertEqual(
            response.status_code,
            302
        )

        self.task_a.refresh_from_db()

        self.assertEqual(
            self.task_a.status,
            "done"
        )

        self.assertIsNotNone(
            self.task_a.reviewed_at
        )