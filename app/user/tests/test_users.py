from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.core import mail

from rest_framework import status
from rest_framework.test import APIClient

RESISTER_USER_URL = reverse('user:register')
AUTH_USER_URL = reverse('user:token_obtain')
REFRESH_TOKEN_URL = reverse('user:token_refresh')
VALIDATE_TOKEN_URL = reverse('user:password_reset:reset-password-validate')
PASSWORD_RESET_URL = reverse('user:password_reset:reset-password-request')
PASSWORD_RESET_CONFIRM_URL = reverse('user:password_reset:reset-password-confirm')


def create_user(**params):
    return get_user_model().objects.create_user(**params)


class UserApiTests(TestCase):
    """Test the users API. For coverage use: coverage run --omit=*/migrations/* manage.py test user"""

    def setUp(self):
        self.client = APIClient()

# TODO: tests