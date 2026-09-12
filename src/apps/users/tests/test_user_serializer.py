from types import SimpleNamespace

from src.apps.users.serializers.user import UserSerializer


def test_role_comes_from_rbac_annotation_not_a_model_field():
    user = SimpleNamespace(
        pubkey="usr_1",
        email="x@example.com",
        is_active=True,
        created_at="2026-01-01T00:00:00Z",
        rbac_role_code="COORDINATOR",
    )
    data = UserSerializer(user).data
    assert data["role"] == "COORDINATOR"


def test_role_is_none_when_no_rbac_annotation_present():
    """Si un appelant oublie d'annoter (bug d'intégration), le serializer
    ne doit pas planter ni halluciner un rôle — il retombe sur None,
    signal explicite qu'il manque une annotation plutôt qu'une valeur
    fausse silencieuse."""
    user = SimpleNamespace(
        pubkey="usr_1", email="x@example.com", is_active=True, created_at="2026-01-01T00:00:00Z"
    )
    data = UserSerializer(user).data
    assert data["role"] is None


def test_password_never_serialized():
    user = SimpleNamespace(
        pubkey="usr_1",
        email="x@example.com",
        is_active=True,
        created_at="2026-01-01T00:00:00Z",
        rbac_role_code="ADMIN",
        password="should-never-appear",
    )
    data = UserSerializer(user).data
    assert "password" not in data
