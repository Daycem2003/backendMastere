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
