"""
Tests for the ingredeints API
"""

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from core.models import Ingredient, Recipe
from recipe.serializers import IngredientSerializer

INGREDIENT_URLS = reverse("recipe:ingredient-list")


def detail_url(ingredient_id):
    """Create and return and ingredient detail URL"""

    return reverse("recipe:ingredient-detail", args=[ingredient_id])


def create_user(email="test@example.com", password="Test@123"):
    """Create and return user"""

    return get_user_model().objects.create_user(email=email, password=password)


class PublicIngredientsAPITest(TestCase):
    """Test unathenticated API requests"""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test authenticated is required"""

        res = self.client.get(INGREDIENT_URLS)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateIngredientAPITest(TestCase):
    """Test authenticated API requests"""

    def setUp(self):
        self.client = APIClient()
        self.user = create_user()
        self.client.force_authenticate(user=self.user)

    def test_retrieve_ingredients(self):
        """Test retrieving a list of ingredients"""

        Ingredient.objects.create(user=self.user, name="Ing1")
        Ingredient.objects.create(user=self.user, name="Ing2")

        res = self.client.get(INGREDIENT_URLS)
        ingredients = Ingredient.objects.all().order_by("-name")
        serializer = IngredientSerializer(ingredients, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_ingredients_limited_to_user(self):
        """Test list of ingredients is limited to authenticated user"""

        other_user = create_user(email="other@example.com")
        Ingredient.objects.create(user=other_user, name="Ing1")
        ingredient = Ingredient.objects.create(user=self.user, name="Ing2")

        res = self.client.get(INGREDIENT_URLS)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]["name"], ingredient.name)
        self.assertEqual(res.data[0]["id"], ingredient.id)

    def test_update_ingredient(self):
        """Test Updating an ingredient"""

        ingredient = Ingredient.objects.create(user=self.user, name="Ing1")
        payload = {"name": "Updated Ing"}
        url = detail_url(ingredient.id)

        res = self.client.patch(url, payload)
        ingredient.refresh_from_db()

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(ingredient.name, payload["name"])

    def test_delete_ingredient(self):
        """Test delete an ingrediet"""

        ingredient = Ingredient.objects.create(user=self.user, name="Ing")
        url = detail_url(ingredient.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Ingredient.objects.filter(user=self.user).exists())

    def test_filter_ingredients_assigned_to_recipes(self):
        """Test listing ingredients by those assigned to recipes"""

        ingredient1 = Ingredient.objects.create(user=self.user, name="ingredient1")
        ingredient2 = Ingredient.objects.create(user=self.user, name="ingredient2")

        recipe = Recipe.objects.create(
            user=self.user,
            title="simple recipe",
            time_minutes=60,
            price=Decimal("8.13"),
        )
        recipe.ingredients.add(ingredient1)

        serializer1 = IngredientSerializer(ingredient1)
        serializer2 = IngredientSerializer(ingredient2)

        res = self.client.get(INGREDIENT_URLS, {"assigned_only": 1})

        self.assertIn(serializer1.data, res.data)
        self.assertNotIn(serializer2.data, res.data)

    def test_filtered_ingredients_unique(self):
        """Test filtered ingredients returns a unique list"""

        ingredient = Ingredient.objects.create(user=self.user, name="ingredient")
        Ingredient.objects.create(user=self.user, name="other ingredient")

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

        recipe1.ingredients.add(ingredient)
        recipe2.ingredients.add(ingredient)

        res = self.client.get(INGREDIENT_URLS, {"assigned_only": 1})

        self.assertEqual(len(res.data), 1)
