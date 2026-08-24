# Corrections apportées au module `documents`

## 1. Bug bloquant : lookup par pubkey cassé
- `DocumentVersion` a maintenant son propre champ `pubkey` (unique).
- `selectors/document_selector.get_version_by_pubkey` filtre désormais sur
  `pubkey=...` au lieu de `document__pubkey=...` (qui échouait dès que le
  FK `document` legacy était `None`, soit la quasi-totalité des uploads).
- `services/document_service.create_version` génère ce pubkey.
- `serializers/document.DocumentVersionSerializer` l'expose au client
  (absent auparavant — le front n'avait aucun identifiant valide à
  renvoyer à `/approve`, `/reject`, `/{pubkey}`).
- Migration mise à jour (`migrations/0001_document_workflow.py`) avec la
  nouvelle colonne + index.

## 2. Upload de fichier réellement implémenté
- `serializers/document.DocumentUploadSerializer` accepte désormais un
  vrai `FileField` (`file`) au lieu de métadonnées déclaratives
  (`storage_key`, `mime_type`, `file_size`, `checksum` envoyés tels quels
  par le client).
- `services/document_service.store_uploaded_file` calcule ces métadonnées
  côté serveur (taille réelle, mime type, SHA-256) et appelle réellement
  `StorageBackend.upload()` (jusqu'ici `storage.py` n'était jamais appelé).
- Validation serveur : taille max (`MAX_UPLOAD_SIZE_BYTES`) et liste
  blanche de mime types (`ALLOWED_MIME_TYPES`) dans `constants.py`.
- `views/document_views.DocumentUploadView` utilise `MultiPartParser` et
  orchestre le tout ; `storage_key` brut n'est plus exposé publiquement,
  remplacé par `download_url` (URL signée).

## 3. Filet de sécurité `candidate_profile`
- Nouvelle exception `NoCandidateProfile` (403 propre) au lieu d'une
  `AttributeError` non gérée (500) quand un utilisateur authentifié sans
  profil candidat (coordinateur, admin) appelle `/me` ou `/upload`.

## 4. Schéma Prisma
- Ajout de `_PRISMA_SCHEMA_PATCH.prisma` décrivant `DocumentVersion` et
  `DocumentAuditEvent`, absent de la livraison précédente, pour rester
  cohérent avec la pratique déjà suivie sur le module `authorization`.

## 5. Tests
- Tests d'origine conservés (`test_document_service.py`).
- Nouveau fichier `test_document_upload_and_review.py` qui couvre
  précisément les deux régressions ci-dessus : lookup par le bon champ
  pubkey, et calcul serveur des métadonnées + appel réel du storage.
- ⚠️ Ces tests mockent l'ORM/le storage car le zip livré ne contenait pas
  de `conftest.py`/factories pour `User`/`CandidateProfile`. À compléter
  par de vrais tests d'intégration (APIClient + factories du projet).
