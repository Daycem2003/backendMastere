from rest_framework.exceptions import APIException, NotFound, PermissionDenied


class CandidateProfileNotFound(NotFound):
    default_detail = "Profil candidat introuvable."


class ApplicationNotFound(NotFound):
    default_detail = "Candidature introuvable."


class ApplicationDoesNotBelongToCandidate(APIException):
    status_code = 400
    default_detail = "Cette candidature n'appartient pas au candidat indiqué."


class NotificationNotFound(NotFound):
    default_detail = "Notification introuvable."


class NotificationAccessForbidden(PermissionDenied):
    default_detail = "Vous n'êtes pas autorisé à accéder à cette notification."
