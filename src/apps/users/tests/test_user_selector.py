from unittest.mock import MagicMock, patch

from src.apps.users.selectors.user_selector import list_all, list_by_rbac_role_code


@patch("src.apps.authorization.models.user_role.UserRole")
def test_list_all_annotates_rbac_role_via_single_subquery(mock_user_role_cls):
    """Vérifie qu'une seule sous-requête corrélée est utilisée pour
    annoter le rôle RBAC — pas de boucle Python déclenchant une requête
    par utilisateur (N+1)."""
    mock_user_role_cls.objects.filter.return_value.values.return_value = MagicMock()

    with patch("src.apps.users.selectors.user_selector.User") as mock_user_cls:
        mock_qs = MagicMock()
        mock_user_cls.objects.filter.return_value = mock_qs
        mock_qs.annotate.return_value = mock_qs
        mock_qs.order_by.return_value = mock_qs

        list_all()

        mock_qs.annotate.assert_called_once()
        annotate_kwargs = mock_qs.annotate.call_args.kwargs
        assert "rbac_role_code" in annotate_kwargs


@patch("src.apps.authorization.models.user_role.UserRole")
def test_list_by_rbac_role_code_filters_via_user_role_join(mock_user_role_cls):
    mock_user_role_cls.objects.filter.return_value.values_list.return_value = [1, 2]

    with patch("src.apps.users.selectors.user_selector.User") as mock_user_cls:
        mock_qs = MagicMock()
        mock_user_cls.objects.filter.return_value = mock_qs
        mock_qs.annotate.return_value = mock_qs
        mock_qs.order_by.return_value = mock_qs

        list_by_rbac_role_code("ADMIN")

        assert any(
            c.kwargs.get("role__code") == "ADMIN"
            for c in mock_user_role_cls.objects.filter.call_args_list
        )
