from rest_framework import permissions


class CanReviewDocuments(permissions.BasePermission):
    """Rôle coordinateur ou administrateur.

    RÈGLE MÉTIER VALIDÉE : accès GLOBAL, sans périmètre par Master. Un
    coordinateur voit et traite les documents de TOUS les candidats, quel
    que soit le Master concerné — il n'existe pas de notion de "mes
    candidats" pour un coordinateur dans ce module.

    Ne PAS réintroduire un filtrage par `master.coordinateur` ici sans
    revalidation explicite de cette règle : ce serait une régression
    fonctionnelle, pas un fix de sécurité.

    Hypothèse de nommage (cf. commentaire de module) : `user.coordinateur`
    / `user.administrateur` en reverse OneToOne, sinon adapter ici.
    """

    def has_permission(self, request, view):
        user = request.user
        if not (user and user.is_authenticated):
            return False
        return bool(
            getattr(user, "coordinateur", None) is not None
            or getattr(user, "administrateur", None) is not None
        )


class IsDocumentOwnerOrReviewer(permissions.BasePermission):
    """Object-level : le candidat propriétaire du document, OU tout
    coordinateur/administrateur (accès global, cf. CanReviewDocuments).

    Le has_permission() ne fait que vérifier l'authentification ; le vrai
    contrôle se fait dans has_object_permission(), appelé explicitement par
    la vue via check_object_permissions() une fois l'objet chargé.
    """

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        is_owner = obj.slot.candidate_profile.user_id == request.user.pk
        return is_owner or CanReviewDocuments().has_permission(request, view)