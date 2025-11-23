from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, role="reader", **extra_fields):
        if not email:
            raise ValueError("Users must have an email address")
        email = self.normalize_email(email)
        user = self.model(email=email, role=role, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("role", "admin")
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = (
        ("reader", "Reader"),
        ("worker", "Worker"),
        ("admin", "Admin"),
    )

    email = models.EmailField(unique=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default="reader")

    # Required for Django admin/permissions
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    def __str__(self):
        return f"{self.email} ({self.role})"
    

class Reader(models.Model):
    library_card_number = models.CharField(max_length=15, primary_key=True, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    def save(self, *args, **kwargs):
        if not self.library_card_number:
            last_card = Reader.objects.order_by("-library_card_number").first()
            if last_card:
                new_num = int(last_card.library_card_number) + 1
            else:
                new_num = 1
            self.library_card_number = f"{new_num:015d}"
        super().save(*args, **kwargs)


    def __str__(self):
        return f"{self.user.email} - Card: {self.library_card_number}"