from django.db import models

from src.shared.models import TimestampedSoftDeleteModel


class EligibilityCriteria(TimestampedSoftDeleteModel):
    pubkey = models.TextField(unique=True)
    master = models.ForeignKey("masters.Master", on_delete=models.CASCADE, related_name="eligibility_criteria", db_column="masterId")
    type = models.TextField()
    valeur = models.TextField()
    obligatoire = models.BooleanField(default=True)

    class Meta:
        managed = False
        db_table = "MST_ELIGIBILITY_CRITERIA"
