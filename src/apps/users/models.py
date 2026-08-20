from django.db import models

from src.shared.models import PostgreSQLEnumField, TimestampedSoftDeleteModel


class UserRole(models.TextChoices):
    CANDIDATE = "CANDIDATE", "Candidate"
    COORDINATOR = "COORDINATOR", "Coordinator"
    ADMIN = "ADMIN", "Administrator"


class UserManager(models.Manager):
    def create_user(self, *, email: str, password: str, **extra_fields):
        from src.apps.authentication.services.password_service import PasswordService
        return self.create(email=self.normalize_email(email), password=PasswordService.hash_password(password), **extra_fields)

    @staticmethod
    def normalize_email(email: str) -> str:
        return email.strip().lower()


class User(TimestampedSoftDeleteModel):
    """Identity record mapped exactly to legacy MST_USERS; not Django auth.User."""

    pubkey = models.TextField(unique=True)
    email = models.TextField(unique=True)
    password = models.TextField()
    role = PostgreSQLEnumField(enum_name="UserRoleEnum", choices=UserRole.choices, default=UserRole.CANDIDATE)
    is_active = models.BooleanField(default=True, db_column="isActive")
    objects = UserManager()

    @property
    def is_authenticated(self) -> bool:
        return True

    @property
    def isActive(self) -> bool:
        return self.is_active

    class Meta:
        managed = False
        db_table = "MST_USERS"
