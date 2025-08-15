from django.db import models
from django.conf import settings
from django.contrib.postgres.fields import JSONField
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin

class CustomUserManager(BaseUserManager):
    def create_user(self, username, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required")
        if not username:
            raise ValueError("Username is required")
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, username, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(username, email, password, **extra_fields)

class CustomUser(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(max_length=150)
    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    premium = models.BooleanField(default=False)  # ✅ NEW

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    objects = CustomUserManager()

    def __str__(self):
        return self.email


class Resume(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    TEMPLATE_CHOICES = [
        ('modern', 'Modern'),
        ('classic', 'Classic'),
        ('ats', 'ATS'),
    ]

    template = models.CharField(max_length=50, choices=TEMPLATE_CHOICES, default='modern')
    title = models.CharField(max_length=255, default="Untitled Resume")
    data = models.JSONField(default=dict)
    profile_image = models.ImageField(
        upload_to='profile_images/',
        null=True,
        blank=True,
    )
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    hidden_sections = models.JSONField(
        default=dict,
        blank=True,
        help_text=_("Flags for which sections (or sub-fields) should be hidden in print/PDF")
    )

    def __str__(self):
        return f"Resume #{self.id} ({self.user.username})"

