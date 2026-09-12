from django.db.models import OuterRef, QuerySet, Subquery

from src.apps.users.models import User


def _annotate_rbac_role(queryset: QuerySet) -> QuerySet:
    """Annote chaque `User` avec `rbac_role_code`, le code du rôle RBAC
    actif (source unique de vérité). Une seule requête SQL avec sous-
    requête corrélée — pas de requête supplémentaire par utilisateur.

    NOTE : `AUTH_USER_ROLES` (`UserRole`) n'a pas de champ `deleted_at`
    (vérifié sur le modèle réel, pas supposé) — une seule ligne existe par
    utilisateur une fois la contrainte `auth_user_single_role` appliquée
    (voir authorization_patch/), donc pas de filtre de soft-delete à
    ajouter ici : l'existence de la ligne suffit.
    """
    from src.apps.authorization.models.user_role import UserRole

    active_role_code = UserRole.objects.filter(user_id=OuterRef("pk")).values("role__code")[:1]
    return queryset.annotate(rbac_role_code=Subquery(active_role_code))


def get_by_pubkey(pubkey: str) -> User | None:
    return _annotate_rbac_role(
        User.objects.filter(pubkey=pubkey, deleted_at__isnull=True)
    ).first()


def get_by_email(email: str) -> User | None:
    return User.objects.filter(email=email, deleted_at__isnull=True).first()


def list_all(is_active: bool | None = None) -> QuerySet:
    """Ne filtre plus jamais par rôle via une colonne `User` — le rôle
    n'appartient plus à ce modèle. Pour filtrer par rôle RBAC, voir
    `list_by_rbac_role_code`."""
    qs = User.objects.filter(deleted_at__isnull=True)
    if is_active is not None:
        qs = qs.filter(is_active=is_active)
    return _annotate_rbac_role(qs).order_by("email")


def list_by_rbac_role_code(role_code: str) -> QuerySet:
    """Filtre par rôle RBAC actif — une seule requête (jointure via
    `filter`, pas de boucle Python)."""
    from src.apps.authorization.models.user_role import UserRole

    user_ids = UserRole.objects.filter(role__code=role_code).values_list("user_id", flat=True)
    return _annotate_rbac_role(
        User.objects.filter(id__in=user_ids, deleted_at__isnull=True)
    ).order_by("email")
