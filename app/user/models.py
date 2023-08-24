from django.contrib.auth.base_user import BaseUserManager, AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from django.db import models
from django.utils.translation import gettext_lazy as _
from uuid import uuid4

from core import exception
from core.models import safe_file_path
from core.validators import validate_file_size, email_validator, phone_validator


class UserManager(BaseUserManager):
    """User manager class for creating users and superusers"""

    def create_user(self, email: str, password: str = None, **extra_fields: dict) -> 'User':
        """
        Creates and saves new user
        :param email: user email
        :param password: user password
        :param extra_fields: additional parameters
        :return: created user model
        """
        if not email:
            raise exception.get(ValueError, 'User must have email address')
        user = self.model(email=self.normalize_email(email), **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email: str, password: str) -> 'User':
        """
        Creates and saves new super user
        :param email: user email
        :param password: user password
        :return: created user model
        """
        user = self.create_user(email, password)
        user.is_staff = True
        user.is_superuser = True
        user.save()
        return user


class User(AbstractBaseUser, PermissionsMixin):
    uid = models.UUIDField(unique=True, default=uuid4, editable=False)
    email = models.EmailField(
        max_length=255,
        unique=True,
        error_messages={'unique': "email_already_used"},
        verbose_name = _("Email"),
        validators=[email_validator],
    )
    phone = models.CharField(
        max_length=255,
        verbose_name=_("Phone"),
        null=True,
        blank=True,
        validators=[phone_validator],
        unique=True,
        error_messages={'unique': "phone_already_used"},
    )
    is_phone_verified = models.BooleanField(
        default=False,
        verbose_name=_("Is phone verified?"),
    )
    name = models.CharField(
        default='',
        max_length=64,
        verbose_name=_("Name")
    )
    surname = models.CharField(
        default='',
        max_length=64,
        verbose_name=_("Surname")
    )
    avatar = models.ImageField(
        upload_to=safe_file_path,
        null=True,
        default=None,
        blank=True,
        validators=[validate_file_size],
        verbose_name=_('Avatar'),
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        editable=False,
        verbose_name=_("Created at")
    )
    is_email_verified = models.BooleanField(
        default=False,
        verbose_name=_("Is email verified?")
    )
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(
        default=False,
        verbose_name=_("Is staff?"),
        help_text=_("Use this option for create Staff")
    )
    push_id = models.CharField(
        max_length=255,
        blank=True,
        default='',
        verbose_name=_("Push notification id"),
    )
    device_id = models.CharField(
        blank=True,
        default='',
        max_length=100,
    )
    objects = UserManager()
    USERNAME_FIELD = 'email'

    # FOR USING phone INSTEAD OF email
    #
    # phone = models.CharField(
    #     max_length=255,
    #     verbose_name=_("Phone"),
    #     validators=[phone_validator],
    #     unique=True,
    #     error_messages={'unique': "phone_already_used"},
    # )
    # email = models.EmailField(
    #     max_length=255,
    #     unique=True,
    #     error_messages={'unique': "email_already_used"},
    #     verbose_name = _("Email"),
    #     validators=[email_validator],
    #     null=True,
    #     blank=True,
    # )
    # USERNAME_FIELD = 'phone'