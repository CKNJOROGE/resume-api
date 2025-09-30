from django.db import models
from django.conf import settings
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
        # Superusers should have plenty of credits for testing
        extra_fields.setdefault("credits", 9999)
        return self.create_user(username, email, password, **extra_fields)

class CustomUser(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(max_length=150)
    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    # The 'premium' field is replaced with 'credits'
    credits = models.IntegerField(default=0, help_text="User's current credit balance.")

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    objects = CustomUserManager()

    def __str__(self):
        return self.email

# New model to track manual payment submissions
class PendingPayment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('revoked', 'Revoked'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='payments')
    transaction_id = models.CharField(max_length=50, unique=True, help_text="The M-Pesa transaction ID submitted by the user.")
    amount = models.IntegerField(default=300)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        # Using get_status_display() shows the human-readable status
        return f"{self.user.email} - {self.transaction_id} ({self.get_status_display()})"

    class Meta:
        ordering = ['-created_at']


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