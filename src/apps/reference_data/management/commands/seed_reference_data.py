import secrets

from django.core.management.base import BaseCommand
from django.db import transaction

from src.apps.reference_data.models import ReferenceData
from src.apps.reference_data.constants import (
    CITIES,
    UNIVERSITIES,
    DOMAINS,
    NATIONALITIES,
)


class Command(BaseCommand):
    help = "Seed reference data"

    @transaction.atomic
    def handle(self, *args, **options):

        self.stdout.write("Seeding reference data...")

        self._seed_category(
            category=ReferenceData.Category.CITY,
            values=CITIES,
        )

        self._seed_category(
            category=ReferenceData.Category.UNIVERSITY,
            values=UNIVERSITIES,
        )

        self._seed_category(
            category=ReferenceData.Category.DOMAIN,
            values=DOMAINS,
        )

        self._seed_category(
            category=ReferenceData.Category.NATIONALITY,
            values=NATIONALITIES,
        )

        self.stdout.write(
            self.style.SUCCESS(
                "Reference data seeded successfully."
            )
        )

    def _seed_category(self, category, values):

        for index, value in enumerate(values):

            ReferenceData.objects.get_or_create(
                category=category,
                value=value,
                defaults={
                    "pubkey": (
                        f"ref_{category.lower()}_"
                        f"{secrets.token_urlsafe(12)}"
                    ),
                    "is_active": True,
                    "display_order": index,
                },
            )