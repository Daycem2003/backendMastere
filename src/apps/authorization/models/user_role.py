from django.db import models

from src.shared.models import ManagedModel


class UserRole(ManagedModel):
    """CHANGEMENT vs version précédente : la contrainte d'unicité passe de
    `(user, role)` à `user` seul. Un utilisateur ne peut désormais avoir
    qu'UNE SEULE ligne dans cette table — donc un seul rôle actif, garanti
    au niveau base de données, pas seulement en logique applicative.

    Changer le rôle d'un utilisateur = remplacer la valeur de `role` sur
    sa ligne existante (ou la créer si absente), jamais ajouter une
    deuxième ligne. Voir `services/role_assignment_service.py`
    (`update_or_create`), qui est désormais le SEUL point d'entrée prévu
    pour modifier une assignation — plus de création directe de `UserRole`
    ailleurs dans le code.

    Pas de champ `deleted_at` sur ce modèle (vérifié, pas supposé) : il
    n'y a pas de notion de soft-delete ici, l'existence de la ligne suffit
    à représenter le rôle actif.
    """

    user = models.OneToOneField(
        "users.User", on_delete=models.CASCADE, related_name="role_assignment", db_column="userId"
    )
    role = models.ForeignKey(
        "authorization.Role", on_delete=models.CASCADE, related_name="user_assignments", db_column="roleId"
    )
    assigned_by = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_roles",
        db_column="assignedById",
    )
    assigned_at = models.DateTimeField(null=True, blank=True, db_column="assignedAt", db_default=models.functions.Now())

    class Meta:
        db_table = "AUTH_USER_ROLES"
        # CHANGEMENT : OneToOneField ci-dessus impose déjà l'unicité sur
        # `user` au niveau Django/DB (une seule ligne par utilisateur,
        # quel que soit le rôle). L'ancienne UniqueConstraint(user, role)
        # est supprimée : elle autorisait plusieurs rôles simultanés, ce
        # qui est exactement ce qu'on doit désormais interdire.
