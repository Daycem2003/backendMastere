import logging

from django.db import IntegrityError, transaction

from src.apps.authorization.exceptions.authorization_exceptions import (
    PrivilegeEscalationException,
    RoleAssignmentAlreadyExistsException,
    RoleAssignmentNotFoundException,
    RoleNotFoundException,
)
from src.apps.authorization.models import Role, UserRole
from src.apps.authorization.selectors.authorization_selector import invalidate_permission_cache
from src.apps.users.models import User
from src.shared.exceptions.auth_exceptions import UserNotFoundException

logger = logging.getLogger(__name__)


class RoleAssignmentService:
    @staticmethod
    @transaction.atomic
    def assign_role(user_pubkey: str, role_code: str, assigned_by_pubkey: str | None):
        user = User.objects.filter(pubkey=user_pubkey).first()
        if not user: raise UserNotFoundException()
        role = Role.objects.filter(code=role_code).first()
        if not role: raise RoleNotFoundException()
        if user_pubkey == assigned_by_pubkey and role.code == "ADMIN":
            raise PrivilegeEscalationException()
        assigner = User.objects.filter(pubkey=assigned_by_pubkey).first() if assigned_by_pubkey else None
        try:
            assignment = UserRole.objects.create(user=user, role=role, assigned_by=assigner)
        except IntegrityError as error:
            raise RoleAssignmentAlreadyExistsException() from error
        invalidate_permission_cache(user_pubkey)
        logger.info(
            "rbac_role_assigned",
            extra={
                "user_pubkey": user_pubkey,
                "role_code": role_code,
                "assigned_by_pubkey": assigned_by_pubkey,
            },
        )
        return assignment

    @staticmethod
    def revoke_role(user_pubkey: str, role_code: str) -> None:
        with transaction.atomic():
            deleted, _ = UserRole.objects.filter(user__pubkey=user_pubkey, role__code=role_code).delete()
        if not deleted: raise RoleAssignmentNotFoundException()
        invalidate_permission_cache(user_pubkey)
        logger.info(
            "rbac_role_revoked",
            extra={"user_pubkey": user_pubkey, "role_code": role_code},
        )

    @staticmethod
    def list_user_roles(user_pubkey: str):
        if not User.objects.filter(pubkey=user_pubkey).exists(): raise UserNotFoundException()
        return UserRole.objects.select_related("role").filter(user__pubkey=user_pubkey)
