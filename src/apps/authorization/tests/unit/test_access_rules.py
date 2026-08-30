from src.apps.authorization.domain.access_rules import DEFAULT_ROLE_PERMISSIONS
from src.apps.authorization.domain.permissions import PERMISSION_CATALOG
from src.apps.authorization.domain.roles import BASE_ROLES


def test_every_base_role_has_a_default_permission_set():
    for role_code in BASE_ROLES:
        assert role_code in DEFAULT_ROLE_PERMISSIONS


def test_admin_has_every_permission_in_the_catalog():
    all_codes = {definition.code for definition in PERMISSION_CATALOG}
    assert set(DEFAULT_ROLE_PERMISSIONS["ADMIN"]) == all_codes


def test_all_default_permission_codes_exist_in_catalog():
    catalog_codes = {definition.code for definition in PERMISSION_CATALOG}
    for role_code, codes in DEFAULT_ROLE_PERMISSIONS.items():
        for code in codes:
            assert code in catalog_codes, f"{code} référencé pour {role_code} mais absent du catalogue"
