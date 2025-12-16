"""
Test for recipe APIs
"""

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from core.models import Recipe
from recipe.serializers import RecipeDetailSerializer, RecipeSerializer

RECIPES_URL = reverse("recipe:recipe-list")


def detail_url(recipe_id):
    """Create and return a recipe detail URL"""

    return reverse("recipe:recipe-detail", args=[recipe_id])


def create_recipe(user, **params):
    """Create and return a sample recipe"""

    defaults = {
        "title": "Sample recipe title",
        "time_minutes": 20,
        "price": Decimal("5.5"),
        "description": "Sample description",
        "link": "http://example.com/recipe.pdf",
    }
    defaults.update(params)

    return Recipe.objects.create(user=user, **defaults)


def create_user(**params):
    """create and return a new user"""

    return get_user_model().objects.create_user(**params)


class PublicRecipeAPITest(TestCase):
    """Test unauthenticated API requests"""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test auth is required to call API"""

        res = self.client.get(RECIPES_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipeAPITest(TestCase):
    """Test authenticated API requests"""

    def setUp(self):
        self.client = APIClient()
        self.user = create_user(
            email="user@example.com",
            password="Test@123",
        )
        self.client.force_authenticate(self.user)

    def test_retrieve_recipes(self):
        """Test Retrieving a list of recipes"""

        create_recipe(user=self.user)
        create_recipe(user=self.user)

        res = self.client.get(RECIPES_URL)
        recipes = Recipe.objects.order_by("-id")
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_recipe_list_limited_to_user(self):
        """Test list of recipes is limited to authenticated user"""

        other_user = create_user(
            email="other@example.com",
            password="Test@123",
        )
        create_recipe(user=other_user)
        create_recipe(user=self.user)

        res = self.client.get(RECIPES_URL)
        recipes = Recipe.objects.filter(user=self.user)
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_get_recipe_detail(self):
        """Test get recipe detail"""

        recipe = create_recipe(user=self.user)

        url = detail_url(recipe.id)
        res = self.client.get(url)

        serializer = RecipeDetailSerializer(recipe)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_create_recipe(self):
        """Test creating recipe"""

        payload = {
            "title": "Sample recipe title",
            "time_minutes": 20,
            "price": Decimal("5.50"),
            "description": "Sample description",
            "link": "http://example.com/recipe.pdf",
        }
        res = self.client.post(RECIPES_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        recipe = Recipe.objects.get(id=res.data["id"])

        for k, v in payload.items():
            self.assertEqual(getattr(recipe, k), v)
        self.assertEqual(recipe.user, self.user)

    def test_partial_update(self):
        """Test partial update of a recipe"""

        original_link = "https:/example.com/recipe.pdf"
        recipe = create_recipe(
            user=self.user,
            title="Sample title",
            link=original_link,
        )
        payload = {"title": "New recipe title"}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload)

        recipe.refresh_from_db()

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.title, payload["title"])
        self.assertEqual(recipe.link, original_link)
        self.assertEqual(recipe.user, self.user)

    def test_full_update(self):
        """Test full update of recipe"""

        recipe = create_recipe(
            user=self.user,
            title="Sample title",
            link="https:/example.com/recipe.pdf",
            description="Sample recipe description",
        )
        payload = {
            "title": "New title",
            "link": "https:/example.com/new_recipe.pdf",
            "description": "New recipe description",
            "time_minutes": 10,
            "price": Decimal("19.37"),
        }
        url = detail_url(recipe.id)
        res = self.client.put(url, payload)

        recipe.refresh_from_db()

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        for k, v in payload.items():
            self.assertEqual(getattr(recipe, k), v)
        self.assertEqual(recipe.user, self.user)

    def test_update_user_returns_error(self):
        """Test changing the recipe user results in an error"""

        new_user = create_user(
            email="newuser@example.com",
            password="Test@123",
        )
        recipe = create_recipe(user=self.user)
        payload = {"user": new_user.id}
        url = detail_url(recipe.id)
        self.client.patch(url, payload)
        recipe.refresh_from_db()

        self.assertEqual(recipe.user, self.user)

    def test_delete_recipe(self):
        """Test deleting a recipe successful"""

        recipe = create_recipe(user=self.user)
        url = detail_url(recipe.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Recipe.objects.filter(id=recipe.id).exists())

    def test_delete_other_users_recipe_error(self):
        """Test trying to delete another users recipe gives error"""

        new_user = create_user(
            email="Other@example.com",
            password="Test@123",
        )
        recipe = create_recipe(user=new_user)
        url = detail_url(recipe.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Recipe.objects.filter(id=recipe.id).exists())
