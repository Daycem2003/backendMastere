from typing import Protocol, runtime_checkable, Any


@runtime_checkable
class Policy(Protocol):
    """
    Contrat minimal qu'une policy concrète (candidate_policy.py,
    master_policy.py, ...) doit respecter. Une policy encapsule des règles
    métier de type "qui a le droit de faire quoi sur CETTE entité précise" —
    typiquement de l'ownership (le coordinateur d'un master, le propriétaire
    d'un profil) combinée au rôle de base.

    Les policies ne font AUCUN accès direct à la base — elles reçoivent déjà
    les objets chargés (user, resource) et raisonnent dessus en mémoire.
    Le chargement des données reste la responsabilité des selectors/services
    appelants.
    """

    def can_view(self, user: Any, resource: Any) -> bool: ...

    def can_update(self, user: Any, resource: Any) -> bool: ...

    def can_delete(self, user: Any, resource: Any) -> bool: ...
