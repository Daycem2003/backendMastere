"""Règles de validation appliquées côté serveur lors de l'upload de documents.

Ces limites ne doivent JAMAIS être contournables par des valeurs envoyées par
le client (voir services/document_service.py et views/document_views.py) :
c'est le serveur qui mesure/valide le fichier reçu, jamais le client qui les
déclare.
"""

MAX_UPLOAD_SIZE_BYTES = 10 * 1024 * 1024  # 10 Mo

ALLOWED_MIME_TYPES = {
    "application/pdf",
    "image/png",
    "image/jpeg",
}
