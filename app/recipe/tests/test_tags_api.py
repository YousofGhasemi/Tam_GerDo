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

        Tag.objects.create(user=self.user, name="Carnivorous")
        Tag.objects.create(user=self.user, name="Veagan")

        res = self.client.get(TAGS_URL)
        tags = Tag.objects.all().order_by("-name")
        serializer = TagSerializer(tags, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_tags_limited_to_user(self):
        """Test list of tags is limited to authenticated user"""

        other_user = create_user(email="other@example.com")
        Tag.objects.create(user=other_user, name="Fruity")
        tag = Tag.objects.create(user=self.user, name="Fast Food")

        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]["name"], tag.name)
        self.assertEqual(res.data[0]["id"], tag.id)

    def test_update_tag(self):
        """Test updating a tag"""

        tag = Tag.objects.create(user=self.user, name="Dizi")
        payload = {"name": "GhormeSabzi"}
        url = detail_url(tag.id)
        res = self.client.patch(url, payload)

        tag.refresh_from_db()

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(tag.name, payload["name"])

    def test_delete_tag(self):
        """Test deleting a tag"""

        tag = Tag.objects.create(user=self.user, name="Gheime")
        url = detail_url(tag.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Tag.objects.filter(user=self.user).exists())

    def test_filter_tags_assigned_to_recipes(self):
        """Test listing tags by those assigned to recipes"""

        tag1 = Tag.objects.create(user=self.user, name="tag1")
        tag2 = Tag.objects.create(user=self.user, name="tag2")

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

        tag = Tag.objects.create(user=self.user, name="tag")
        Tag.objects.create(user=self.user, name="other tag")

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
