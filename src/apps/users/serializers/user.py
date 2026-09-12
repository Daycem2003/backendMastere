from rest_framework import serializers

from src.apps.users.models import User


class UserSerializer(serializers.ModelSerializer):
    """`role` est lu depuis `rbac_role_code`, une annotation posée par les
    selectors (`_annotate_rbac_role`) — jamais depuis une colonne du
    modèle `User` lui-même, qui n'en expose aucune. Si l'appelant utilise
    un queryset non annoté (bug d'intégration), `role` retombe sur `None`
    plutôt que de lever une exception random — mais ça ne doit jamais
    arriver en pratique puisque tous les selectors annotent
    systématiquement.

    `password` reste absent des `fields` : jamais sérialisé.
    """

    role = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ("pubkey", "email", "role", "is_active", "created_at")
        read_only_fields = fields

    def get_role(self, obj) -> str | None:
        return getattr(obj, "rbac_role_code", None)


class SetActiveStatusSerializer(serializers.Serializer):
    is_active = serializers.BooleanField()
    reason = serializers.CharField(max_length=500, required=False, allow_blank=True)
