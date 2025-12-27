"""
Test for recipe APIs
"""

import os
import tempfile
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from PIL import Image
from rest_framework import status
from rest_framework.test import APIClient

from core.models import Ingredient, Recipe, Tag
from recipe.serializers import RecipeDetailSerializer, RecipeSerializer

RECIPES_URL = reverse("recipe:recipe-list")


def detail_url(recipe_id):
    """Create and return a recipe detail URL"""

    return reverse("recipe:recipe-detail", args=[recipe_id])


def image_upload_url(recipe_id):
    """Create and return a recipe detail URL"""

    return reverse("recipe:recipe-upload-image", args=[recipe_id])


def create_user(email="user@example.com", password="Pass@123"):
    """Create and return a new user"""

    return get_user_model().objects.create_user(email, password)


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


def create_tag(user, name="Sample Tag"):
    """Create and return a sample tag"""

    return Tag.objects.create(user=user, name=name)


def create_ingredient(user, name="Sample Ingredient"):
    """Create and return a sample ingredient"""

    return Ingredient.objects.create(user=user, name=name)


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
        self.user = create_user()
        self.client.force_authenticate(self.user)

    def test_retrieve_recipes(self):
        """Test Retrieving a list of recipes"""

        create_recipe(self.user)
        create_recipe(self.user)

        res = self.client.get(RECIPES_URL)
        recipes = Recipe.objects.filter(user=self.user).order_by("-id")
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_recipe_list_limited_to_user(self):
        """Test list of recipes is limited to authenticated user"""

        other_user = create_user(email="other@example.com")
        create_recipe(user=other_user)
        create_recipe(self.user)

        res = self.client.get(RECIPES_URL)
        recipes = Recipe.objects.filter(user=self.user)
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_get_recipe_detail(self):
        """Test get recipe detail"""

        recipe = create_recipe(self.user)

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

        original_link = "https://example.com/recipe.pdf"
        recipe = create_recipe(
            self.user,
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
            self.user,
            title="Sample title",
            link="https://example.com/recipe.pdf",
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

        other_user = create_user(email="other@example.com")
        recipe = create_recipe(self.user)
        payload = {"user": other_user.id}
        url = detail_url(recipe.id)

        self.client.patch(url, payload)
        recipe.refresh_from_db()

        self.assertEqual(recipe.user, self.user)

    def test_delete_recipe(self):
        """Test deleting a recipe successful"""

        recipe = create_recipe(self.user)
        url = detail_url(recipe.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Recipe.objects.filter(id=recipe.id).exists())

    def test_delete_other_users_recipe_error(self):
        """Test trying to delete another users recipe gives error"""

        other_user = create_user(email="other@example.com")
        recipe = create_recipe(user=other_user)
        url = detail_url(recipe.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Recipe.objects.filter(id=recipe.id).exists())

    def test_create_recipe_with_new_tags(self):
        """Test creating a recipe with new tags"""

        payload = {
            "title": "Kabab kobide",
            "time_minutes": 36,
            "price": Decimal("8.3"),
            "tags": [
                {"name": "Nahar"},
                {"name": "Carnivorous"},
            ],
        }
        res = self.client.post(RECIPES_URL, payload, format="json")
        recipes = Recipe.objects.filter(user=self.user)
        recipe = recipes[0]

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(recipes.count(), 1)
        self.assertEqual(recipe.tags.count(), 2)
        for tag in payload["tags"]:
            exists = recipe.tags.filter(
                name=tag["name"],
                user=self.user,
            ).exists()
            self.assertTrue(exists)

    def test_create_recipe_with_existing_tag(self):
        """Test creating a recipe with existing tag"""

        sample_tag = create_tag(self.user, name="Tag")
        payload = {
            "title": "Kabab kobide",
            "time_minutes": 36,
            "price": Decimal("8.3"),
            "tags": [
                {"name": "Nahar"},
                {"name": "Tag"},
            ],
        }
        res = self.client.post(RECIPES_URL, payload, format="json")
        recipes = Recipe.objects.filter(user=self.user)
        recipe = recipes[0]

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(recipes.count(), 1)
        self.assertEqual(recipe.tags.count(), 2)
        self.assertIn(sample_tag, recipe.tags.all())
        for tag in payload["tags"]:
            exists = recipe.tags.filter(
                name=tag["name"],
                user=self.user,
            ).exists()
            self.assertTrue(exists)

    def test_create_tag_on_update(self):
        recipe = create_recipe(self.user)
        payload = {"tags": [{"name": "new tag"}]}
        url = detail_url(recipe.id)

        res = self.client.patch(url, payload, format="json")
        recipe.refresh_from_db()

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertTrue(recipe.tags.filter(name="new tag").exists())

    def test_update_recipe_assign_tag(self):
        """Test assigning tag when updating a recipe"""

        tag1 = create_tag(self.user, "Tag1")
        tag2 = create_tag(self.user, "Tag2")

        recipe = create_recipe(self.user)
        recipe.tags.add(tag1)

        payload = {"tags": [{"name": "Tag2"}]}

        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format="json")
        recipe.refresh_from_db()

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(tag2, recipe.tags.all())
        self.assertNotIn(tag1, recipe.tags.all())

    def test_clear_recipe_tags(self):
        """Test clearing a recipe tags"""

        sample_tag = create_tag(self.user)
        recipe = create_recipe(self.user)
        recipe.tags.add(sample_tag)

        payload = {"tags": []}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format="json")

        recipe.refresh_from_db()

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.tags.count(), 0)

    def test_create_recipe_with_new_ingredients(self):
        """Test creating a recipe with new ingredients is successful"""

        payload = {
            "title": "Kabab kobide",
            "time_minutes": 36,
            "price": Decimal("8.3"),
            "ingredients": [
                {"name": "Meat"},
                {"name": "Onion"},
            ],
        }

        res = self.client.post(RECIPES_URL, payload, format="json")
        recipes = Recipe.objects.filter(user=self.user)
        recipe = recipes[0]

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(recipes.count(), 1)
        self.assertEqual(recipe.ingredients.count(), 2)
        for ingredient in payload["ingredients"]:
            exists = recipe.ingredients.filter(
                name=ingredient["name"],
                user=self.user,
            ).exists()
            self.assertTrue(exists)

    def test_create_recipe_with_existing_ingredient(self):
        """Test creating a new recipe with existing ingredient"""

        sample_ingredient = create_ingredient(self.user, name="Ing")

        payload = {
            "title": "Kabab kobide",
            "time_minutes": 36,
            "price": Decimal("8.3"),
            "ingredients": [
                {"name": "Ing"},
                {"name": "Onion"},
            ],
        }

        res = self.client.post(RECIPES_URL, payload, format="json")
        recipes = Recipe.objects.filter(user=self.user)
        recipe = recipes[0]

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(recipes.count(), 1)
        self.assertEqual(recipe.ingredients.count(), 2)
        self.assertIn(sample_ingredient, recipe.ingredients.all())
        for ingredient in payload["ingredients"]:
            exists = recipe.ingredients.filter(
                name=ingredient["name"],
                user=self.user,
            ).exists()
            self.assertTrue(exists)

    def test_create_ingredient_on_updating(self):
        """Test creating a new ingredient when updating a recipe"""

        recipe = create_recipe(self.user)
        payload = {"ingredients": [{"name": "Ing"}]}
        url = detail_url(recipe.id)

        res = self.client.patch(url, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        recipe.refresh_from_db()
        ingredients = recipe.ingredients.all()

        self.assertEqual(ingredients.count(), 1)
        self.assertEqual(ingredients.first().name, "Ing")
        self.assertTrue(Ingredient.objects.filter(user=self.user, name="Ing").exists())

    def test_update_recipe_assign_ingredient(self):
        """Test assigning an existing ingredient when updating a recipe"""

        ingredient1 = create_ingredient(self.user, "Ing1")
        ingredient2 = create_ingredient(self.user, "Ing2")

        payload = {"ingredients": [{"name": "Ing2"}]}

        recipe = create_recipe(self.user)
        recipe.ingredients.add(ingredient1)

        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format="json")
        recipe.refresh_from_db()

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.ingredients.count(), 1)
        self.assertIn(ingredient2, recipe.ingredients.all())
        self.assertNotIn(ingredient1, recipe.ingredients.all())

    def test_clear_recipe_ingredients(self):
        """Test clearing all ingredients from a recipe"""

        sample_ingredient = create_ingredient(self.user)
        recipe = create_recipe(self.user)
        recipe.ingredients.add(sample_ingredient)

        payload = {"ingredients": []}
        url = detail_url(recipe.id)

        res = self.client.patch(url, payload, format="json")
        recipe.refresh_from_db()

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.ingredients.count(), 0)

    def test_filter_by_tags(self):
        """Test filtring recipes by tags"""

        recipe1 = create_recipe(self.user, title="recipe1")
        recipe2 = create_recipe(self.user, title="recipe2")
        recipe3 = create_recipe(self.user, title="recipe3")

        tag1 = create_tag(self.user, "tag1")
        tag2 = create_tag(self.user, "tag2")

        recipe1.tags.add(tag1)
        recipe2.tags.add(tag2)

        params = {"tags": f"{tag1.id},{tag2.id}"}

        res = self.client.get(RECIPES_URL, params)

        serializer1 = RecipeSerializer(recipe1)
        serializer2 = RecipeSerializer(recipe2)
        serializer3 = RecipeSerializer(recipe3)

        self.assertIn(serializer1.data, res.data)
        self.assertIn(serializer2.data, res.data)
        self.assertNotIn(serializer3.data, res.data)

    def test_filter_by_ingredients(self):
        """Test filtring recipes by ingredients"""

        recipe1 = create_recipe(self.user, title="recipe1")
        recipe2 = create_recipe(self.user, title="recipe2")
        recipe3 = create_recipe(self.user, title="recipe3")

        ingredient1 = create_ingredient(self.user, "Ing1")
        ingredient2 = create_ingredient(self.user, "Ing2")

        recipe1.ingredients.add(ingredient1)
        recipe2.ingredients.add(ingredient2)

        params = {"ingredients": f"{ingredient1.id},{ingredient2.id}"}

        res = self.client.get(RECIPES_URL, params)

        serializer1 = RecipeSerializer(recipe1)
        serializer2 = RecipeSerializer(recipe2)
        serializer3 = RecipeSerializer(recipe3)

        self.assertIn(serializer1.data, res.data)
        self.assertIn(serializer2.data, res.data)
        self.assertNotIn(serializer3.data, res.data)


class ImageUploadTest(TestCase):
    """Test for the image upload API"""

    def setUp(self):
        self.client = APIClient()
        self.user = create_user()
        self.client.force_authenticate(self.user)
        self.recipe = create_recipe(self.user)

    def tearDown(self):
        if self.recipe.image:
            self.recipe.image.delete()

    def test_upload_image(self):
        """Test uploading an image to the recipe"""

        url = image_upload_url(self.recipe.id)

        with tempfile.NamedTemporaryFile(suffix=".jpg") as image_file:
            img = Image.new("RGB", (10, 10))
            img.save(image_file, format="JPEG")
            image_file.seek(0)
            payload = {"image": image_file}

            res = self.client.post(url, payload, format="multipart")

        self.recipe.refresh_from_db()

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("image", res.data)
        self.assertTrue(os.path.exists(self.recipe.image.path))

    def test_upload_image_bad_request(self):
        """Test uploading invalid image"""

        url = image_upload_url(self.recipe.id)
        payload = {"image": "NotAnImage"}
        res = self.client.post(url, payload, format="multipart")

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
