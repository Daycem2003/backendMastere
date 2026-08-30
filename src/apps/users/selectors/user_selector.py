from django.db.models import Q, QuerySet

from src.apps.users.dto.user import UserFilterDTO
from src.apps.users.models import User


def get_user_by_id(user_id: int, include_deleted: bool = False) -> User | None:
    """Retrieve a user by their primary key id."""
    qs = User.objects.all()
    if not include_deleted:
        qs = qs.filter(deleted_at__isnull=True)
    return qs.filter(id=user_id).first()


def get_user_by_pubkey(pubkey: str, include_deleted: bool = False) -> User | None:
    """Retrieve a user by their public key."""
    qs = User.objects.all()
    if not include_deleted:
        qs = qs.filter(deleted_at__isnull=True)
    return qs.filter(pubkey=pubkey).first()


def get_user_by_email(email: str, include_deleted: bool = False) -> User | None:
    """Retrieve a user by normalized email."""
    normalized = User.objects.normalize_email(email)
    qs = User.objects.all()
    if not include_deleted:
        qs = qs.filter(deleted_at__isnull=True)
    return qs.filter(email=normalized).first()


def get_active_user_by_pubkey(pubkey: str) -> User | None:
    """Retrieve an active and non-deleted user by public key."""
    return User.objects.filter(pubkey=pubkey, is_active=True, deleted_at__isnull=True).first()


def get_active_user_by_email(email: str) -> User | None:
    """Retrieve an active and non-deleted user by normalized email."""
    normalized = User.objects.normalize_email(email)
    return User.objects.filter(email=normalized, is_active=True, deleted_at__isnull=True).first()


def list_users(filters: UserFilterDTO | None = None) -> QuerySet[User]:
    """Retrieve a filtered and optimized QuerySet of users."""
    qs = User.objects.all().order_by("-created_at")

    if filters is None:
        return qs.filter(deleted_at__isnull=True)

    if filters.is_deleted is True:
        qs = qs.filter(deleted_at__isnull=False)
    elif filters.is_deleted is False:
        qs = qs.filter(deleted_at__isnull=True)

    if filters.is_active is not None:
        qs = qs.filter(is_active=filters.is_active)

    if filters.search:
        search_term = filters.search.strip()
        qs = qs.filter(
            Q(email__icontains=search_term)
            | Q(pubkey__icontains=search_term)
        )

    return qs


def count_users(filters: UserFilterDTO | None = None) -> int:
    """Count total users matching the filter criteria."""
    return list_users(filters).count()
