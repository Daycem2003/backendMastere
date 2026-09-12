from types import SimpleNamespace
from unittest.mock import patch

import pytest

from src.apps.users.dto.user import CreateUserIdentityDTO, SetActiveStatusDTO
from src.apps.users.exceptions.user_exceptions import (
    CannotDeactivateSelf,
    UserAlreadyActive,
    UserAlreadyExists,
    UserAlreadyInactive,
)
from src.apps.users.models import User
from src.apps.users.services.user_service import UserService


def _user(pk=1, is_active=True):
    return SimpleNamespace(pk=pk, is_active=is_active, save=lambda update_fields: None)


def test_user_model_has_no_role_field():
    """Garde-fou explicite demandé : le modèle User ne doit plus exposer
    de champ `role` du tout — la surface Django ne doit rien avoir à
    désactiver ou ignorer, elle doit simplement ne pas l'avoir."""
    field_names = {f.name for f in User._meta.get_fields()}
    assert "role" not in field_names


@patch("src.apps.users.services.user_service.get_by_email")
def test_create_identity_raises_if_email_already_used(mock_get_by_email):
    mock_get_by_email.return_value = SimpleNamespace(pk=1)
    with pytest.raises(UserAlreadyExists):
        UserService.create_identity(CreateUserIdentityDTO(email="x@example.com", password_hash="h"))


@patch("src.apps.users.services.user_service.User")
@patch("src.apps.users.services.user_service.get_by_email")
def test_create_identity_never_sets_a_role(mock_get_by_email, mock_model_cls):
    """Le coeur de la contrainte : create_identity ne doit jamais passer
    de kwarg `role=` à User.objects.create."""
    mock_get_by_email.return_value = None
    mock_model_cls.objects.create.return_value = SimpleNamespace(pk=1)

    UserService.create_identity(CreateUserIdentityDTO(email="x@example.com", password_hash="h"))

    call_kwargs = mock_model_cls.objects.create.call_args.kwargs
    assert "role" not in call_kwargs
    assert call_kwargs["email"] == "x@example.com"
    assert call_kwargs["password"] == "h"


def test_cannot_deactivate_self():
    user = _user(pk=1, is_active=True)
    with pytest.raises(CannotDeactivateSelf):
        UserService.set_active_status(user, SetActiveStatusDTO(is_active=False), actor=user)


def test_cannot_deactivate_already_inactive_user():
    target = _user(pk=2, is_active=False)
    actor = _user(pk=1)
    with pytest.raises(UserAlreadyInactive):
        UserService.set_active_status(target, SetActiveStatusDTO(is_active=False), actor=actor)


def test_cannot_activate_already_active_user():
    target = _user(pk=2, is_active=True)
    actor = _user(pk=1)
    with pytest.raises(UserAlreadyActive):
        UserService.set_active_status(target, SetActiveStatusDTO(is_active=True), actor=actor)
