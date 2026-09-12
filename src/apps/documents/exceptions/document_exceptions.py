from rest_framework.exceptions import APIException, PermissionDenied, ValidationError


class DocumentVersionNotFound(APIException):
    status_code = 404
    default_detail = "Document introuvable."


class InvalidDocumentTransition(ValidationError):
    default_detail = "Transition de statut documentaire invalide."


class RejectionReasonRequired(ValidationError):
    default_detail = "Un motif est obligatoire pour rejeter un document."


class DocumentAlreadyReviewed(ValidationError):
    default_detail = "Ce document a déjà été examiné."


class DocumentReviewForbidden(PermissionDenied):
    default_detail = "Vous n'êtes pas autorisé à examiner ce document."


class NoCandidateProfile(PermissionDenied):
    default_detail = "Cette action est réservée aux candidats disposant d'un profil."


class FileTooLarge(ValidationError):
    default_detail = "Le fichier dépasse la taille maximale autorisée."

class StorageQuotaExceeded(ValidationError):
    default_detail = "Le quota de stockage ou d'opérations R2 a été atteint."
class UnsupportedFileType(ValidationError):
    default_detail = "Type de fichier non autorisé."
class InvalidSlotType(ValidationError):
    default_detail = "Type de slot documentaire invalide."