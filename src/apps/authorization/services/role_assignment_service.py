import logging

from django.db import transaction

logger = logging.getLogger(__name__)


class RoleAssignmentService:
    """Seul point d'entrée prévu pour assigner ou changer le rôle d'un
    utilisateur. Garantit "un seul rôle actif" en logique métier, en plus
    de la contrainte DB (`OneToOneField` sur `UserRole.user`, voir
    `user_role.py`) — défense en profondeur : la contrainte DB protège
    contre les bugs et les accès concurrents, ce service protège contre un
    usage incorrect de l'API Python (créer un `UserRole` à la main
    ailleurs romprait l'invariant avant même d'atteindre la DB dans
    certains flux, ex. tests avec DB différée)."""

    @staticmethod
    @transaction.atomic
    def assign_role(user, role_code: str, assigned_by=None):
        from src.apps.authorization.exceptions.authorization_exceptions import RoleCodeNotFound
        from src.apps.authorization.models.role import Role
        from src.apps.authorization.models.user_role import UserRole

        role = Role.objects.filter(code=role_code, deleted_at__isnull=True).first()
        if not role:
            raise RoleCodeNotFound()

        assignment, created = UserRole.objects.update_or_create(
            user=user,
            defaults={"role": role, "assigned_by": assigned_by},
        )
        logger.info(
            "rbac_role_assigned",
            extra={
                "user_id": user.pk,
                "role_code": role_code,
                "was_created": created,
                "assigned_by_id": assigned_by.pk if assigned_by else None,
            },
        )
        return assignment

    @staticmethod
    def get_active_role_code(user) -> str | None:
        from src.apps.authorization.models.user_role import UserRole

        assignment = (
            UserRole.objects.filter(user=user).select_related("role").first()
        )
        return assignment.role.code if assignment else None
