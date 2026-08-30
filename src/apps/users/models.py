import uuid

from django.db import models

from src.shared.models import PostgreSQLEnumField


class UserRole(models.TextChoices):
    """Legacy database enum choices for MST_USERS.role.
    
    NOTE: Real RBAC authorization (roles, permissions, assignments) is exclusively
    managed by the `authorization` module.
    """
    CANDIDATE = "CANDIDATE", "Candidate"
    COORDINATOR = "COORDINATOR", "Coordinator"
    ADMIN = "ADMIN", "Administrator"


class UserManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset()

    def active(self):
        """Filter users who are active and not soft-deleted."""
        return self.filter(is_active=True, deleted_at__isnull=True)

    def create_user(
        self,
        *,
        email: str,
        password: str,
        pubkey: str | None = None,
        role: str = UserRole.CANDIDATE,  # Legacy column default
        is_active: bool = True,
        **extra_fields,
    ) -> "User":
        """Create a user identity and credential record.

        NOTE: Role authority belongs exclusively to `authorization.services.RoleAssignmentService`.
        The `role` parameter only populates the legacy `MST_USERS.role` database column for
        schema compatibility and is NEVER consulted for authorization decisions.
        """
        from src.apps.authentication.services.password_service import PasswordService

        normalized_email = self.normalize_email(email)
        user_pubkey = pubkey or f"usr_{uuid.uuid4().hex[:20]}"
        hashed_password = PasswordService.hash_password(password)

        return self.create(
            pubkey=user_pubkey,
            email=normalized_email,
            password=hashed_password,
            role=role,
            is_active=is_active,
            **extra_fields,
        )

    @staticmethod
    def normalize_email(email: str) -> str:
        return email.strip().lower()


class User(models.Model):
    """Identity and user lifecycle record mapped to MST_USERS."""

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ()

    id = models.AutoField(primary_key=True)
    pubkey = models.TextField(unique=True)
    email = models.TextField(unique=True)
    password = models.TextField()
    role = PostgreSQLEnumField(
        enum_name="UserRoleEnum",
        choices=UserRole.choices,
        default=UserRole.CANDIDATE,
    )
    is_active = models.BooleanField(default=True, db_column="isActive")
    created_at = models.DateTimeField(auto_now_add=True, db_column="createdAt")
    updated_at = models.DateTimeField(auto_now=True, db_column="updatedAt", null=True, blank=True)
    deleted_at = models.DateTimeField(null=True, blank=True, db_column="deletedAt")

    objects = UserManager()

    @property
    def is_authenticated(self) -> bool:
        return True

    @property
    def is_anonymous(self) -> bool:
        return False

    @property
    def isActive(self) -> bool:
        return self.is_active

    @property
    def is_active_user(self) -> bool:
        return self.is_active and self.deleted_at is None

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None

    @property
    def profile_type(self) -> str:
        return str(self.role)

    def __str__(self) -> str:
        return f"User({self.pubkey}, email={self.email}, active={self.is_active})"

    class Meta:
        managed = True
        db_table = "MST_USERS"
