"""
Test for favorite recipe APIs
"""

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from core.models import Recipe

FAVORITE_URL = reverse("recipe:favorite_list")


def detail_url(recipe_id):
    """Create and return a favorite detail url"""

    return reverse("recipe:favorite-recipe", args=[recipe_id])


def create_user(**params):
    """Create and return a user"""

    defaults = {
        "email": "user@example.com",
        "password": "Pass@123",
    }
    defaults.update(**params)

    return get_user_model().objects.create(**defaults)


def create_recipe(user, **params):
    """Create and return a sample recipe"""

    defaults = {
        "title": "Sample recipe title",
        "time_minutes": 20,
        "price": Decimal("5.5"),
        "description": "Sample description",
        "link": "http://example.com/recipe.pdf",
    }
    defaults.update(**params)

    return Recipe.objects.create(user=user, **defaults)


class PublicFavoriteAPITest(TestCase):
    """Test unauthenticated API requests"""

    def setUp(self):
        self.client = APIClient()

    def test_unauthenticated_user_cannot_access_favorites(self):
        """Test unauthenticated user connot favorite a recipe"""

        user = create_user()
        recipe = create_recipe(user=user)

        url = detail_url(recipe.id)
        res = self.client.post(url)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthenticated_user_cannot_unfavorite_a_recipe(self):
        """Test unauthenticated user cannot unfavorite a recipe"""

        user = create_user()
        recipe = create_recipe(user=user)
        url = detail_url(recipe.id)

        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthenticated_user_cannot_list_favorites(self):
        """Unauthenticated user cannot list favorites"""

        res = self.client.get(FAVORITE_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateFavoriteAPITest(TestCase):
    """Test authenticated API requests"""

    def setUp(self):
        self.client = APIClient()
        self.user = create_user()
        self.client.force_authenticate(user=self.user)

    def test_user_can_favorite_a_recipe(self):
        """Test authenticated user can favorite a recipe"""

        recipe = create_recipe(self.user)
        url = detail_url(recipe.id)

        res = self.client.post(url)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertTrue(self.user.favorites.filter(id=recipe.id).exists())

    def test_uthenticated_user_can_unfavorite_a_recipe(self):
        """Test authenticated user can unfavorite a recipe"""

        recipe = create_recipe(self.user)
        self.user.favorites.add(recipe)
        url = detail_url(recipe.id)

        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(self.user.favorites.filter(id=recipe.id).exists())

    def test_recipe_cannot_be_favorited_twice(self):
        """Test recipe cannot be favorited twice"""

        recipe = create_recipe(self.user)
        self.user.favorites.add(recipe)
        url = detail_url(recipe.id)

        res = self.client.post(url)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(recipe, self.user.favorites.all())
        self.assertEqual(self.user.favorites.filter(id=recipe.id).count(), 1)

    def test_only_users_favorites_can_be_displaied_in_favorites_list(self):
        """Test Display favorites list (only own favorites)"""

        other_user = create_user(email="other@example.com")

        recipe1 = create_recipe(user=self.user)
        recipe2 = create_recipe(user=self.user)
        recipe3 = create_recipe(user=other_user)

        self.user.favorites.add(recipe1)
        self.user.favorites.add(recipe3)
        other_user.favorites.add(recipe2)

        res = self.client.get(FAVORITE_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        returned_ids = [item["id"] for item in res.data]

        self.assertIn(recipe1.id, returned_ids)
        self.assertIn(recipe3.id, returned_ids)
        self.assertNotIn(recipe2.id, returned_ids)

        self.assertEqual(len(returned_ids), 2)

    def test_removing_non_favorited_recipe_is_safe(self):
        """Test Removing non-favorited recipe is safe"""

        recipe = create_recipe(self.user)

        url = detail_url(recipe.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(len(res.data), 0)
