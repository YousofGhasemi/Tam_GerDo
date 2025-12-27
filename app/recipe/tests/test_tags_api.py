"""
Tests for the Tags API
"""

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from core.models import Recipe, Tag
from recipe.serializers import TagSerializer

TAGS_URL = reverse("recipe:tag-list")


def detail_url(tag_id):
    """Create and return a tag detail url"""

    return reverse("recipe:tag-detail", args=[tag_id])


def create_user(email="user@example.com", password="Pass@123"):
    """Create and return a new user"""

    return get_user_model().objects.create_user(email, password)


def create_tag(user, name="Sample Tag"):
    """Create and return a sample tag"""

    return Tag.objects.create(user=user, name=name)


class PublicTagsAPITests(TestCase):
    """Test unauthenticated API requests"""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test auth is requred for retrieving tags"""

        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateTagsAPITests(TestCase):
    """Test authenticated API requests"""

    def setUp(self):
        self.user = create_user()
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieve_tags(self):
        """Test retrieving a list of tags"""

        create_tag(self.user, name="Tag1")
        create_tag(self.user, name="Tag2")

        res = self.client.get(TAGS_URL)
        tags = Tag.objects.filter(user=self.user).order_by("-name")
        serializer = TagSerializer(tags, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_tags_limited_to_user(self):
        """Test list of tags is limited to authenticated user"""

        other_user = create_user(email="other@example.com")
        create_tag(other_user)
        tag = create_tag(self.user)

        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]["name"], tag.name)
        self.assertEqual(res.data[0]["id"], tag.id)

    def test_update_tag(self):
        """Test updating a tag"""

        tag = create_tag(self.user)
        payload = {"name": "Updated Tag"}
        url = detail_url(tag.id)
        res = self.client.patch(url, payload)

        tag.refresh_from_db()

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(tag.name, payload["name"])
        self.assertEqual(res.data["name"], "Updated Tag")

    def test_delete_tag(self):
        """Test deleting a tag"""

        tag = create_tag(self.user)
        url = detail_url(tag.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Tag.objects.filter(id=tag.id).exists())

    def test_filter_tags_assigned_to_recipes(self):
        """Test listing tags by those assigned to recipes"""

        tag1 = create_tag(self.user, name="tag1")
        tag2 = create_tag(self.user, name="tag2")

        recipe = Recipe.objects.create(
            user=self.user,
            title="simple recipe",
            time_minutes=60,
            price=Decimal("8.13"),
        )
        recipe.tags.add(tag1)

        serializer1 = TagSerializer(tag1)
        serializer2 = TagSerializer(tag2)

        res = self.client.get(TAGS_URL, {"assigned_only": 1})

        self.assertIn(serializer1.data, res.data)
        self.assertNotIn(serializer2.data, res.data)

    def test_filtered_tags_unique(self):
        """Test filtered tags returns a unique list"""

        tag = create_tag(self.user)
        create_tag(self.user, name="other tag")

        recipe1 = Recipe.objects.create(
            user=self.user,
            title="recipe1",
            time_minutes=60,
            price=Decimal("8.13"),
        )
        recipe2 = Recipe.objects.create(
            user=self.user,
            title="recipe2",
            time_minutes=30,
            price=Decimal("4.13"),
        )

        recipe1.tags.add(tag)
        recipe2.tags.add(tag)

        res = self.client.get(TAGS_URL, {"assigned_only": 1})

        self.assertEqual(len(res.data), 1)
