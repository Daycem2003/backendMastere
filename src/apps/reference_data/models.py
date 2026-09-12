from django.db import models


class ReferenceData(models.Model):
    class Category(models.TextChoices):
        CITY = "CITY", "Ville"
        UNIVERSITY = "UNIVERSITY", "Université"
        DOMAIN = "DOMAIN", "Domaine"
        NATIONALITY = "NATIONALITY", "Nationalité"
        TYPE_LICENCE = "TYPE_LICENCE", "Type de licence"   # ← ajout

    pubkey = models.CharField(max_length=100, unique=True)
    category = models.CharField(
        max_length=30,
        choices=Category.choices,
    )
    value = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    display_order = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "MST_REFERENCE_DATA"
        ordering = ["category", "display_order", "value"]
        constraints = [
            models.UniqueConstraint(
                fields=["category", "value"],
                name="unique_reference_data_category_value",
            )
        ]

    def __str__(self):
        return f"{self.category}: {self.value}"