from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

User = get_user_model()

REGISTER_URL = reverse("users:register")
TOKEN_URL = reverse("users:token_obtain_pair")
TOKEN_REFRESH_URL = reverse("users:token_refresh")
ME_URL = reverse("users:me")


class UserRegisterTest(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_register_success(self):
        data = {
            "email": "test@test.com",
            "password": "qwerty",
            "first_name": "test_first",
            "last_name": "test_last",
        }
        result = self.client.post(REGISTER_URL, data)
        self.assertEqual(result.status_code, status.HTTP_201_CREATED)
        self.assertNotIn("password", result.data)
        user = User.objects.get(email=data["email"])
        self.assertTrue(user.check_password(data["password"]))

    def test_register_short_password(self):
        data = {
            "email": "test@test.com",
            "password": "qwe",
        }
        result = self.client.post(REGISTER_URL, data)
        self.assertEqual(result.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_duplicate_email(self):
        User.objects.create_user(email="test@test.com", password="qwe")
        data = {
            "email": "test@test.com",
            "password": "qwe",
        }
        result = self.client.post(REGISTER_URL, data)
        self.assertEqual(result.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_without_password(self):
        data = {
            "email": "test@test.com",
        }
        result = self.client.post(REGISTER_URL, data)
        self.assertEqual(result.status_code, status.HTTP_400_BAD_REQUEST)


class UserTokenTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(email="test@test.com", password="qwerty")

    def test_token_obtained_success(self):
        result = self.client.post(
            TOKEN_URL, {"email": "test@test.com", "password": "qwerty"}
        )

        self.assertEqual(result.status_code, status.HTTP_200_OK)
        self.assertIn("access", result.data)
        self.assertIn("refresh", result.data)

    def test_token_wrong_password(self):
        result = self.client.post(
            TOKEN_URL, {"email": "test@test.com", "password": "wrong"}
        )

        self.assertEqual(result.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_token_refresh_success(self):
        tokens = self.client.post(
            TOKEN_URL, {"email": "test@test.com", "password": "qwerty"}
        )
        refresh = tokens.data["refresh"]
        result = self.client.post(TOKEN_REFRESH_URL, {"refresh": refresh})
        self.assertEqual(result.status_code, status.HTTP_200_OK)
        self.assertIn("access", result.data)


class UserMeTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="test@test.com",
            password="qwerty",
            first_name="test_first",
            last_name="test_last",
        )
        self.client.force_authenticate(user=self.user)

    def test_me_get(self):
        result = self.client.get(ME_URL)
        self.assertEqual(result.status_code, status.HTTP_200_OK)
        self.assertEqual(result.data["email"], self.user.email)
        self.assertNotIn("password", result.data)

    def test_me_patch(self):
        result = self.client.patch(ME_URL, {"first_name": "updated"})
        self.assertEqual(result.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(result.data["first_name"], self.user.first_name)

    def test_me_unauthorized(self):
        client = APIClient()
        result = client.get(ME_URL)
        self.assertEqual(result.status_code, status.HTTP_401_UNAUTHORIZED)
