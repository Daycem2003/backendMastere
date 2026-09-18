"""
Service d'assignation de rôle (relation utilisateur <-> role RBAC).

L'assignation est maintenant modelée via `authorization.UserRole` (relation
OneToOne utilisateur -> role unique via `UserRole.user`) et NON via un champ
`role` sur l'utilisateur : l'utilisateur n'a pas de column `role` mappée par
Django. `RoleAssignmentService` est le seul point d'entrée pour créer
`UserRole`; les autres modules ne créent pas de `UserRole` directement
(excepté les migrations/seed).

La signature accepte l'utilisateur (et son assigneur) soit en `User`
instancé (chemin interne `UserProvisioningService`), soit en clé publique
`pubkey` (couche API / view / DTO). `get_user_roles` lit UNIQUEMENT la
table `UserRole`, jamais un champ obsolète.
"""

from django.db import transaction
from django.utils import timezone

from src.apps.authorization.models import UserRole


class RoleAssignmentService:
    @staticmethod
    def _resolve_user(user_or_pubkey):
        """Return the User behind a `User` instance or a `pubkey` string.

        Returns `None` when a `pubkey` string does not resolve to an existing
        user. A non-saved `User` (no pk) is rejected.
        """
        from src.apps.users.models import User

        if isinstance(user_or_pubkey, User):
            assert user_or_pubkey.pk is not None, "Un utilisateur non sauvegardé."
            return user_or_pubkey

        if not user_or_pubkey:
            return None

        return User.objects.filter(pubkey=user_or_pubkey).first()

    @staticmethod
    @transaction.atomic
    def assign_role(
        user=None,
        role_code=None,
        *,
        assigned_by=None,
        assigned_by_pubkey=None,
        user_pubkey=None,
    ) -> "UserRole":
        """Assign a role to a user.

        Polymorphic on identity: the user (and, optionally, the actor that
        assigned it) may be passed either as a `User` instance or as a `pubkey`
        string, so the internal `UserProvisioningService` (object-based) and the
        API/view/DTO layer (`user_pubkey=`) share one entry point.
        """
        from src.apps.authorization.exceptions.authorization_exceptions import (
            RoleAssignmentAlreadyExistsException,
            RoleCodeNotFound,
        )
        from src.apps.authorization.models import Role, UserRole as UserRoleModel

        target = RoleAssignmentService._resolve_user(
            user if user is not None else user_pubkey
        )
        if target is None:
            referenced = user_pubkey if user is None else user
            raise ValueError(f"User pubkey not found: {referenced}")

        role = Role.objects.filter(code=role_code, deleted_at__isnull=True).first()
        if role is None:
            raise RoleCodeNotFound()

        actor_ref = assigned_by if assigned_by is not None else assigned_by_pubkey
        actor = RoleAssignmentService._resolve_user(actor_ref) if actor_ref is not None else None

        existing = UserRoleModel.objects.filter(user=target).first()
        if existing is not None:
            if existing.role_id == role.pk:
                # One row per user and that row already points at this role:
                # re-assigning it is a no-op surfaced as a 409 so callers cannot
                # mistake it for a fresh assignment.
                raise RoleAssignmentAlreadyExistsException()
            # Changing the role replaces the existing row (never a 2nd row).
            existing.role = role
            existing.assigned_by = actor
            existing.assigned_at = timezone.now()
            existing.save(update_fields=["role", "assigned_by", "assigned_at"])
            return existing

        assignment, _ = UserRoleModel.objects.update_or_create(
            user=target,
            defaults={"role": role, "assigned_by": actor},
        )
        return assignment

    @staticmethod
    def revoke_role(user=None, role_code=None, *, user_pubkey=None) -> None:
        """Revoke a role assignment from a user.

        Deletes the `UserRole` row for `user` (optionally only when its role's
        `code == role_code`). With a OneToOne relationship a user has at most
        one row, so this detaches it completely.
        """
        target = RoleAssignmentService._resolve_user(
            user if user is not None else user_pubkey
        )
        if target is None:
            return

        queryset = UserRole.objects.filter(user=target)
        if role_code is not None:
            queryset = queryset.filter(role__code=role_code)
        queryset.delete()

    @staticmethod
    def list_user_roles(user=None, *, user_pubkey=None) -> list["UserRole"]:
        """Return the active `UserRole` rows for a user (role relation loaded)."""
        target = RoleAssignmentService._resolve_user(
            user if user is not None else user_pubkey
        )
        if target is None:
            return []

        return list(UserRole.objects.filter(user=target).select_related("role"))

    @staticmethod
    def get_active_role_code(user_or_pubkey):
        """Return the user's active role `code`, or `None` if they have none.

        Reads only the `UserRole` table (the source of truth); the result is
        only ever surfaced through the API/auth path, never re-persisted into
        the user record.
        """
        target = RoleAssignmentService._resolve_user(user_or_pubkey)
        if target is None:
            return None

        role_assignment = UserRole.objects.filter(user=target).select_related("role").first()
        if role_assignment is None:
            return None

        return role_assignment.role.code
