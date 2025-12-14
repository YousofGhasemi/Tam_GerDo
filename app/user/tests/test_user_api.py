"""
Tests for the user API
"""

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

CREATE_USER_URL = reverse("user:create")
TOKEN_URL = reverse("user:token")


def create_user(**params):
    """Create and return a new user."""
    return get_user_model().objects.create_user(**params)


class PublicUserAPITest(TestCase):
    """Test the public features of the user api"""

    def setUp(self):
        self.client = APIClient()

    def test_create_user_success(self):
        """Test creating a user is successfull."""

        payload = {
            "email": "test@example.com",
            "password": "Test@123",
            "name": "Test name",
        }

        res = self.client.post(CREATE_USER_URL, payload)
        user = get_user_model().objects.get(email=payload["email"])

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertTrue(user.check_password(payload["password"]))
        self.assertNotIn("password", res.data)

    def test_user_with_email_exist_error(self):
        """Test error returned if user with email exists."""

        payload = {
            "email": "test@example.com",
            "password": "Test@123",
            "name": "Test name",
        }

        create_user(**payload)
        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_too_short_error(self):
        """Test and error is returned if password is less than 4 chars"""

        payload = {
            "email": "test@example.com",
            "password": "ts",
            "name": "Test name",
        }

        res = self.client.post(CREATE_USER_URL, payload)
        user_exist = get_user_model().objects.filter(email=payload["email"]).exists()

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(user_exist)

    def test_create_toke_for_user(self):
        """Test generates token for valid credentials."""

        user_details = {
            "email": "test@example.com",
            "password": "Test@123",
            "name": "Test name",
        }

        create_user(**user_details)
        payload = {
            "email": user_details["email"],
            "password": user_details["password"],
        }

        res = self.client.post(TOKEN_URL, payload)

        self.assertIn("token", res.data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_create_token_bad_credentials(self):
        """Test returns error if credentials invalid."""

        payload = {
            "email": "test@example.com",
            "password": "badpass",
        }

        create_user(email="test@example.com", password="goodpass")
        res = self.client.post(TOKEN_URL, payload)

        self.assertNotIn("token", res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_blank_password(self):
        """Test returns error if password is blank."""

        payload = {
            "email": "test@example.com",
            "password": "",
        }

        create_user(email="test@example.com", password="goodpass")
        res = self.client.post(TOKEN_URL, payload)

        self.assertNotIn("token", res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
