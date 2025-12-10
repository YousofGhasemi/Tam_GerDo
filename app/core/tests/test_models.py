"""
Tests for Models
"""

from django.contrib.auth import get_user_model
from django.test import TestCase


class ModleTests(TestCase):
    """Test models"""

    def test_create_user_with_email(self):
        """Testing for user creation via email"""

        email = "test@example.com"
        password = "Test@123"
        user = get_user_model().objects.create_user(
            email=email,
            password=password,
        )

        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))

    def test_new_user_email_normalized(self):
        """Test email is normalized for new users"""

        sample_emails = [
            ["test1@EXAMPLE.com", "test1@example.com"],
            ["Test2@Example.com", "Test2@example.com"],
            ["TEST3@EXAMPLE.COM", "TEST3@example.com"],
            ["test4@EXAMPLE.COM", "test4@example.com"],
        ]
        for email, expected in sample_emails:
            user = get_user_model().objects.create_user(email, "Sample123")
            self.assertEqual(user.email, expected)

    def test_new_user_without_email_raises_error(self):
        """Test that creating a user without an email raises ValueError"""

        with self.assertRaises(ValueError):
            get_user_model().objects.create_user("", "Test123")

    def test_create_superuser(self):
        """TEst creating a superuser."""

        user = get_user_model().objects.create_superuser(
            "test@example.com",
            "Test@123",
        )

        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)
