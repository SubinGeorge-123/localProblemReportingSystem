import os
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Issue

class IssueViewsTest(TestCase):
    def setUp(self):
        # Initialize client
        self.client = Client()

        # Get credentials from environment variables with fallbacks
        self.admin_username = os.getenv('TEST_ADMIN_USERNAME', 'admin')
        self.admin_password = os.getenv('TEST_ADMIN_PASSWORD', 'Subin@123')
        self.normal_username = os.getenv('TEST_NORMAL_USERNAME', 'user')
        self.normal_password = os.getenv('TEST_NORMAL_PASSWORD', 'user123')
        self.other_username = os.getenv('TEST_OTHER_USERNAME', 'other')
        self.other_password = os.getenv('TEST_OTHER_PASSWORD', 'other123')

        # Create users
        self.admin_user = User.objects.create_superuser(
            username=self.admin_username, 
            password=self.admin_password, 
            email='admin@example.com'
        )
        self.normal_user = User.objects.create_user(
            username=self.normal_username, 
            password=self.normal_password, 
            email='user@example.com'
        )
        self.other_user = User.objects.create_user(
            username=self.other_username, 
            password=self.other_password, 
            email='other@example.com'
        )

        # Create an issue for normal user
        self.issue = Issue.objects.create(
            user=self.normal_user,
            issue_name='Pothole on street',
            street_no='123',
            priority='Medium',
            description='Big pothole causing accidents',
            category='Roads',
            status='New'
        )

    # ---------------- DASHBOARD VIEW ----------------
    def test_dashboard_view_for_admin(self):
        self.client.login(username=self.admin_username, password=self.admin_password)
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.issue.issue_name)  # admin sees all issues

    def test_dashboard_view_for_normal_user(self):
        self.client.login(username=self.normal_username, password=self.normal_password)
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.issue.issue_name)
        # Normal user should not see issues of other users
        self.assertNotContains(response, 'Other User Issue')

    # ---------------- CREATE ISSUE VIEW ----------------
    def test_create_issue_view_get(self):
        self.client.login(username=self.normal_username, password=self.normal_password)
        response = self.client.get(reverse('create_issue'))
        self.assertEqual(response.status_code, 200)

    def test_create_issue_view_post_valid(self):
        self.client.login(username=self.normal_username, password=self.normal_password)
        response = self.client.post(reverse('create_issue'), {
            'issue_name': 'Broken streetlight',
            'street_no': '456',
            'priority': 'High',
            'description': 'Streetlight not working',
            'category': 'Electricity',
            'status': 'New'
        })
        self.assertEqual(response.status_code, 302)  # Redirect to dashboard
        self.assertTrue(Issue.objects.filter(issue_name='Broken streetlight').exists())

    # ---------------- UPDATE ISSUE VIEW ----------------
    def test_update_issue_view_admin_can_update_any_issue(self):
        self.client.login(username=self.admin_username, password=self.admin_password)
        response = self.client.post(reverse('update_issue', args=[self.issue.id]), {
            'issue_name': 'Pothole fixed',
            'street_no': '123',
            'priority': 'Low',
            'description': 'Issue resolved',
            'category': 'Roads',
            'status': 'Resolved'
        })
        self.assertRedirects(response, reverse('dashboard'))
        self.issue.refresh_from_db()
        self.assertEqual(self.issue.status, 'Resolved')

    def test_update_issue_view_user_cannot_update_others_issue(self):
        self.client.login(username=self.other_username, password=self.other_password)
        response = self.client.get(reverse('update_issue', args=[self.issue.id]))
        self.assertEqual(response.status_code, 404)  # Should not access others' issues

    # ---------------- DELETE ISSUE VIEW ----------------
    def test_delete_issue_view_admin_can_delete_any_issue(self):
        self.client.login(username=self.admin_username, password=self.admin_password)
        response = self.client.post(reverse('delete_issue', args=[self.issue.id]))
        self.assertRedirects(response, reverse('dashboard'))
        self.assertFalse(Issue.objects.filter(id=self.issue.id).exists())

    def test_delete_issue_view_user_can_delete_own_issue(self):
        self.client.login(username=self.normal_username, password=self.normal_password)
        response = self.client.post(reverse('delete_issue', args=[self.issue.id]))
        self.assertRedirects(response, reverse('dashboard'))
        self.assertFalse(Issue.objects.filter(id=self.issue.id).exists())

    def test_delete_issue_view_user_cannot_delete_others_issue(self):
        self.client.login(username=self.other_username, password=self.other_password)
        response = self.client.post(reverse('delete_issue', args=[self.issue.id]))
        self.assertEqual(response.status_code, 404)  # Should not delete others' issues