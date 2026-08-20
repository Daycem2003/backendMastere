# Mastere Backend

Backend de la plateforme de gestion des candidatures aux masters.

## Stack

- Python 3.11
- Django 5.2
- Django REST Framework
- PostgreSQL
- Poetry
- JWT
- Pydantic DTOs
- pytest / pytest-django
- Redis prévu pour les composants asynchrones

## Milestone livré

### Migration ORM

- Les modèles métier `MST_*` sont mappés avec Django ORM et restent `managed = False` lorsqu'ils représentent des tables legacy.
- Django ORM est utilisé pour les accès applicatifs courants.
- Prisma reste conservé comme artefact de référence pendant la migration, mais n'est plus utilisé par le code runtime Django.

### Authentication

- Endpoints DRF pour register, login, OTP, reset password, refresh token et profil.
- Authentification JWT DRF via `JWTAuthentication`.
- Le modèle utilisateur custom reste compatible avec `MST_USERS`.
- Aucun champ Django Auth supplémentaire n'est imposé à `MST_USERS`.

### Authorization / RBAC

- Modèles Django gérés pour `AUTH_ROLES`, `AUTH_PERMISSIONS`, `AUTH_ROLE_PERMISSIONS` et `AUTH_USER_ROLES`.
- `AUTH_*` est la source de vérité des autorisations.
- `MST_USERS.role` est conservé uniquement pour compatibilité legacy.
- Permissions DRF composables : rôles, permissions, permissions multiples et ownership.
- Protection des rôles système et blocage de l'auto-attribution du rôle `ADMIN`.
- Seed RBAC préparé dans `authorization/0002_seed_rbac`.

### Documents

- `MST_DOCUMENTS` reste inchangée et `managed = False`.
- Le workflow documentaire est porté par des tables Django séparées :
  - `DOCUMENT_VERSIONS`
  - `DOCUMENT_AUDIT_EVENTS`
- Statuts : `PENDING_REVIEW`, `APPROVED`, `REJECTED`.
- Historique des remplacements, reviewer, date de revue, motif de rejet et audit.
- Migration préparée dans `documents/0001_document_workflow`.
- Aucun contenu binaire n'est stocké dans PostgreSQL ; le modèle conserve une référence `storage_key`.

## Prérequis

- Python 3.11+
- Poetry
- PostgreSQL accessible
- Git

Pour utiliser PostgreSQL avec Docker, Docker Desktop doit être installé.

## Installation locale

Depuis la racine du projet :

```powershell
poetry install --with dev --no-root
Copy-Item .env.example .env
```

Modifiez ensuite `.env` avec les identifiants PostgreSQL adaptés à votre environnement.

Variables importantes :

```dotenv
DEBUG=True
SECRET_KEY=change-me
DATABASE_URL=postgresql://postgres:password@localhost:5432/mastere_backend_db
DJANGO_SETTINGS_MODULE=src.config.settings.development
JWT_SECRET_KEY=change-me
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7
```

Ne commitez jamais `.env`. Utilisez `.env.example` comme modèle sans secret.

## Vérifications sans modification de base

Ces commandes ne modifient pas PostgreSQL :

```powershell
poetry run python manage.py check
poetry run python -m compileall -q src manage.py
poetry run pytest -q
poetry run python manage.py showmigrations
```

## Lancer le serveur Django

```powershell
poetry run python manage.py runserver 127.0.0.1:8000
```

API principale :

```text
http://127.0.0.1:8000/api/v1/
```

Health check applicatif à ajouter selon le module concerné. Les routes actuellement déclarées peuvent être inspectées avec le resolver Django si `show_urls` n'est pas installé.

## Routes principales

### Authentication

```text
POST /api/v1/auth/register
POST /api/v1/auth/login
POST /api/v1/auth/login/id-number
POST /api/v1/auth/login/phone
POST /api/v1/auth/otp/verify
POST /api/v1/auth/token/refresh
POST /api/v1/auth/password/forgot
POST /api/v1/auth/password/reset
GET  /api/v1/auth/me
PATCH /api/v1/auth/me
```

### Authorization

```text
GET    /api/v1/authorization/permissions
GET    /api/v1/authorization/roles
POST   /api/v1/authorization/roles
GET    /api/v1/authorization/roles/{pubkey}
PATCH  /api/v1/authorization/roles/{pubkey}
DELETE /api/v1/authorization/roles/{pubkey}
POST   /api/v1/authorization/users/roles
DELETE /api/v1/authorization/users/{user_pubkey}/roles/{role_code}
```

### Documents

```text
GET  /api/v1/documents/me
POST /api/v1/documents/upload
GET  /api/v1/documents/review/pending
GET  /api/v1/documents/{pubkey}
POST /api/v1/documents/{pubkey}/approve
POST /api/v1/documents/{pubkey}/reject
```

## Migrations

Les migrations Django sont la seule voie prévue pour créer les nouvelles tables Django.

État connu du milestone :

```text
authorization 0001_initial       appliquée dans l'environnement contrôlé
authorization 0002_seed_rbac    préparée, application à valider
documents 0001_document_workflow préparée, application à valider
```

Dans un environnement neuf, après vérification de la base et autorisation explicite :

```powershell
poetry run python manage.py migrate
```

Cette commande peut créer les tables Django managées. Elle ne doit pas être exécutée contre une base de production sans plan de migration validé.

Pendant la phase contrôlée actuelle, ne lancez pas automatiquement `migrate`, `migrate --fake`, `migrate --fake-initial`, `prisma migrate` ou `prisma db push`.

Les tables legacy `MST_*` ne doivent pas être recréées, renommées ou supprimées.

## Docker

Le fichier `docker-compose.yml` fournit PostgreSQL et Redis.

```powershell
docker compose up db redis
```

Le service backend Docker contient encore des commandes Prisma historiques dans son `command`, et le `Dockerfile` contient encore `prisma generate`. Cette configuration est un artefact de transition et ne doit pas être considérée comme le runner Django final tant que le nettoyage Docker/Prisma n'est pas validé.

Pour lancer le backend Django de manière contrôlée avec les dépendances locales :

```powershell
poetry run python manage.py runserver 0.0.0.0:8000
```

## Tests

Suite complète :

```powershell
poetry run pytest -q
```

Tests ciblés :

```powershell
poetry run pytest src/apps/authentication/tests -q
poetry run pytest src/apps/authorization/tests -q
poetry run pytest src/apps/documents/tests -q
```

Les tests d'intégration nécessitant une base PostgreSQL dédiée peuvent rester désactivés tant que leur environnement de test n'est pas provisionné.

## Stockage documentaire

Le service de stockage expose une abstraction afin de permettre :

- stockage local en développement ;
- S3 ou MinIO en production ;
- génération d'URL temporaires ;
- suppression logique sans supprimer l'historique métier.

Ne stockez pas les fichiers binaires dans PostgreSQL.

## Sécurité

- Les secrets doivent venir de l'environnement.
- Les mots de passe ne sont jamais retournés dans les réponses API.
- Les JWT complets, OTP et mots de passe ne doivent jamais être écrits dans les logs.
- Les permissions doivent être vérifiées côté backend.
- `User.role` ne doit pas être utilisé comme moteur RBAC.
- Les accès candidats doivent être limités à leurs propres documents.
- Les reviews documentaires sont réservées aux rôles RBAC autorisés.

## Limites connues

- Le module `notifications` ne fournit pas encore de provider persistant complet pour les rejets documentaires.
- OTP et tokens de reset utilisent encore un stockage temporaire en mémoire.
- Le stockage S3/MinIO doit encore être branché en production.
- Le nettoyage final des commandes Prisma dans Docker est une étape séparée.
- Les migrations préparées ne signifient pas qu'elles ont été appliquées à la base courante.

## Commande de démarrage recommandée

Pour le milestone actuel :

```powershell
poetry install --with dev --no-root
poetry run python manage.py check
poetry run pytest -q
poetry run python manage.py runserver 127.0.0.1:8000
```
