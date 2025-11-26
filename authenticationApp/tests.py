import os
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib.messages import get_messages

class AuthViewsTest(TestCase):

    def setUp(self):
        # Use environment variables with fallbacks
        self.username = os.getenv('TEST_USERNAME', 'testuser')
        self.password = os.getenv('TEST_PASSWORD', 'TestPass123')
        self.new_user_password = os.getenv('TEST_NEW_PASSWORD', 'StrongPass123!')
        
        self.user = User.objects.create_user(
            username=self.username, 
            email='testuser@example.com', 
            password=self.password
        )

    def test_signup_view_get(self):
        response = self.client.get(reverse('signup'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'signup.html')

    def test_signup_view_post_valid(self):
        response = self.client.post(reverse('signup'), {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': self.new_user_password,
            'password2': self.new_user_password,
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('login'))
        self.assertTrue(User.objects.filter(username='newuser').exists())

        messages = [m.message for m in get_messages(response.wsgi_request)]
        self.assertTrue(any("Account created for newuser" in m for m in messages))

    def test_signup_view_post_invalid(self):
        response = self.client.post(reverse('signup'), {
            'username': 'baduser',
            'email': 'baduser@example.com',
            'password1': 'abc',
            'password2': 'xyz',
        })
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'signup.html')
        self.assertFalse(User.objects.filter(username='baduser').exists())

    def test_login_view_get(self):
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'login.html')

    def test_login_view_post_valid(self):
        response = self.client.post(reverse('login'), {
            'username': self.username,
            'password': self.password,
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('dashboard'))
        self.assertTrue(response.wsgi_request.user.is_authenticated)

    def test_login_view_post_invalid(self):
        response = self.client.post(reverse('login'), {
            'username': self.username,
            'password': 'wrongpass',
        })
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'login.html')
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_logout_view_redirects(self):
        self.client.login(username=self.username, password=self.password)
        response = self.client.get(reverse('logout'))
        self.assertRedirects(response, reverse('login'))
        self.assertFalse(response.wsgi_request.user.is_authenticated)