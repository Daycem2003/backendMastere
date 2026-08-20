"""
Pas de Django admin actif dans ce projet (voir apps.py pour le contexte).
La gestion des rôles/permissions/assignations se fait exclusivement via les
endpoints REST protégés de views/role_view.py, views/permission_view.py et
views/role_assignment_view.py, réservés au rôle ADMIN.

Si une interface d'administration visuelle est nécessaire un jour, préférer
un outil dédié consommant l'API REST (ex: Retool, ou un back-office React
maison) plutôt que de réintroduire Django admin sur un schéma géré par
Prisma.
"""
