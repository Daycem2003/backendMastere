"""
Ce projet n'utilise PAS Django ORM, donc pas de vrai framework de signaux
Django (post_save, etc.). Ce module fournit un émetteur d'événements
in-process minimal pour les mêmes besoins : découpler "un rôle vient d'être
assigné/révoqué" de ses effets de bord (invalider le cache de permissions,
écrire un log d'audit, notifier...).

Limite assumée : ces callbacks tournent dans le MÊME process, de façon
synchrone après l'action. Pour un vrai découplage inter-services (ex: queue
de notifications asynchrone), utiliser Celery (déjà présent dans le projet)
plutôt que ce mécanisme.
"""

from collections.abc import Awaitable, Callable

RoleAssignmentCallback = Callable[[str, str], Awaitable[None]]  # (user_pubkey, role_code)

_on_role_assigned: list[RoleAssignmentCallback] = []
_on_role_revoked: list[RoleAssignmentCallback] = []


def on_role_assigned(callback: RoleAssignmentCallback) -> None:
    _on_role_assigned.append(callback)


def on_role_revoked(callback: RoleAssignmentCallback) -> None:
    _on_role_revoked.append(callback)


async def emit_role_assigned(user_pubkey: str, role_code: str) -> None:
    for callback in _on_role_assigned:
        await callback(user_pubkey, role_code)


async def emit_role_revoked(user_pubkey: str, role_code: str) -> None:
    for callback in _on_role_revoked:
        await callback(user_pubkey, role_code)
