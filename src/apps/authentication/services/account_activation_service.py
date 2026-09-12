import secrets
import uuid
from datetime import timedelta

from django.utils import timezone

from src.apps.authentication.models import AccountActivationToken
from src.apps.authentication.services.password_service import PasswordService
from src.apps.users.models import User
from src.shared.exceptions.auth_exceptions import InvalidTokenException


class AccountActivationService:
    DEFAULT_TTL_HOURS = 48

    @classmethod
    def create_activation_token(
        cls, user: User, ttl_hours: int = DEFAULT_TTL_HOURS
    ) -> AccountActivationToken:
        # Invalider d'anciens jetons non utilisés pour cet utilisateur
        AccountActivationToken.objects.filter(user=user, used_at__isnull=True).delete()

        token_str = secrets.token_urlsafe(32)
        pubkey = f"act_{uuid.uuid4().hex[:20]}"
        expires_at = timezone.now() + timedelta(hours=ttl_hours)

        return AccountActivationToken.objects.create(
            pubkey=pubkey,
            token=token_str,
            user=user,
            expires_at=expires_at,
        )

    @classmethod
    def activate_account(cls, token_str: str, new_password: str) -> User:
        now = timezone.now()
        activation_record = (
            AccountActivationToken.objects.select_related("user")
            .filter(
                token=token_str,
                used_at__isnull=True,
                deleted_at__isnull=True,
            )
            .first()
        )

        if not activation_record or activation_record.expires_at < now:
            raise InvalidTokenException()

        user = activation_record.user
        user.password = PasswordService.hash_password(new_password)
        user.is_active = True
        user.save(update_fields=["password", "is_active"])

        activation_record.used_at = now
        activation_record.save(update_fields=["used_at"])

        return user
