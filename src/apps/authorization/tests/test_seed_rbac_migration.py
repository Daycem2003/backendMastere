from contextlib import nullcontext
from importlib import import_module
from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase

migration = import_module("src.apps.authorization.migrations.0002_seed_rbac")


class FakeQuerySet(list):
    def first(self):
        return self[0] if self else None

    def values_list(self, field_name, flat=False):
        values = [getattr(item, field_name) for item in self]
        return values if flat else [(value,) for value in values]

    def delete(self):
        for item in list(self):
            item._manager.items.remove(item)
        return len(self), {}


class FakeManager:
    def __init__(self, model):
        self.model = model
        self.items = []

    def filter(self, **filters):
        def matches(item):
            for field, expected in filters.items():
                if field.endswith("__in"):
                    value = getattr(item, field[:-4])
                    if value not in expected:
                        return False
                else:
                    if getattr(item, field) != expected:
                        return False
            return True

        return FakeQuerySet(item for item in self.items if matches(item))

    def create(self, **values):
        item = self.model(**values)
        item.pk = len(self.items) + 1
        item._manager = self
        self.items.append(item)
        return item

    def get_or_create(self, **filters):
        existing = self.filter(**filters).first()
        return (existing, False) if existing else (self.create(**filters), True)


class FakeModel:
    def __init__(self, **values):
        self.__dict__.update(values)


class FakeRolePermissionManager(FakeManager):
    def get_or_create(self, **filters):
        existing = self.filter(**filters).first()
        if existing:
            return existing, False
        return self.create(**filters), True


class FakeApps:
    def __init__(self):
        self.models = {}
        for name in ("Role", "Permission"):
            model = type(name, (FakeModel,), {})
            model.objects = FakeManager(model)
            self.models[("authorization", name)] = model
        model = type("RolePermission", (FakeModel,), {})
        model.objects = FakeRolePermissionManager(model)
        self.models[("authorization", "RolePermission")] = model

    def get_model(self, app_label, model_name):
        return self.models[(app_label, model_name)]


class SeedRbacMigrationTests(SimpleTestCase):
    def setUp(self):
        self.apps = FakeApps()
        self.schema_editor = SimpleNamespace(connection=SimpleNamespace(alias="default"))
        self.atomic = patch.object(migration.transaction, "atomic", lambda **kwargs: nullcontext())
        self.atomic.start()
        self.addCleanup(self.atomic.stop)

    def _seed(self):
        migration.seed_rbac(self.apps, self.schema_editor)

    def test_roles_permissions_and_least_privilege_assignments(self):
        self._seed()
        Role = self.apps.get_model("authorization", "Role")
        Permission = self.apps.get_model("authorization", "Permission")
        RolePermission = self.apps.get_model("authorization", "RolePermission")

        self.assertEqual({role.code for role in Role.objects.items}, {"CANDIDATE", "COORDINATOR", "ADMIN"})
        self.assertEqual(len(Permission.objects.items), len(migration.PERMISSION_SEEDS))
        candidate = Role.objects.filter(code="CANDIDATE").first()
        candidate_links = [
            link.permission_id
            for link in RolePermission.objects.items
            if link.role_id == candidate.pk
        ]
        expected = {
            Permission.objects.filter(code=code).first().pk
            for code in migration.ROLE_PERMISSION_CODES["CANDIDATE"]
        }
        self.assertEqual(set(candidate_links), expected)

    def test_seed_is_idempotent_and_candidate_is_available(self):
        self._seed()
        Role = self.apps.get_model("authorization", "Role")
        Permission = self.apps.get_model("authorization", "Permission")
        RolePermission = self.apps.get_model("authorization", "RolePermission")
        counts = (len(Role.objects.items), len(Permission.objects.items), len(RolePermission.objects.items))

        self._seed()

        self.assertEqual(counts, (len(Role.objects.items), len(Permission.objects.items), len(RolePermission.objects.items)))
        self.assertEqual(Role.objects.filter(code="CANDIDATE").first().pubkey, "role_candidate")

    def test_reverse_removes_seed_records_and_forward_recreates_them(self):
        self._seed()
        migration.unseed_rbac(self.apps, self.schema_editor)
        Role = self.apps.get_model("authorization", "Role")
        Permission = self.apps.get_model("authorization", "Permission")
        self.assertFalse(Role.objects.filter(code="CANDIDATE").first())
        self.assertFalse(Permission.objects.filter(code="master:view").first())

        self._seed()
        self.assertTrue(Role.objects.filter(code="CANDIDATE").first())
        self.assertTrue(Permission.objects.filter(code="master:view").first())
