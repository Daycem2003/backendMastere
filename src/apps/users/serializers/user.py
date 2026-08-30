from rest_framework import serializers

from src.apps.users.models import User


class UserSerializer(serializers.ModelSerializer):
    profile_type = serializers.CharField(read_only=True)
    is_deleted = serializers.BooleanField(read_only=True)

    class Meta:
        model = User
        fields = (
            "id",
            "pubkey",
            "email",
            "role",
            "is_active",
            "is_deleted",
            "profile_type",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "pubkey",
            "role",
            "is_active",
            "is_deleted",
            "profile_type",
            "created_at",
            "updated_at",
        )


class CreateUserSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(min_length=8, max_length=128, write_only=True)
    role = serializers.CharField(required=False, default="CANDIDATE")
    is_active = serializers.BooleanField(required=False, default=True)


class UpdateUserSerializer(serializers.Serializer):
    email = serializers.EmailField(required=False)


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(min_length=1, write_only=True)
    new_password = serializers.CharField(min_length=8, max_length=128, write_only=True)

    def validate(self, attrs):
        if attrs["old_password"] == attrs["new_password"]:
            raise serializers.ValidationError(
                {"new_password": "Le nouveau mot de passe doit être différent de l'ancien."}
            )
        return attrs


class UserActionReasonSerializer(serializers.Serializer):
    reason = serializers.CharField(required=False, allow_blank=True, default=None)
