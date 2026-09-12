from django.db import models

from src.apps.eligibility.domain.rule_value import RuleValueData
from src.shared.models import TimestampedSoftDeleteModel


class EligibilityCriteria(TimestampedSoftDeleteModel):


    pubkey = models.TextField(unique=True)

    master = models.ForeignKey(
        "masters.Master", on_delete=models.CASCADE, related_name="eligibility_criteria", db_column="masterId"
    )

    criterion = models.TextField(db_column="type")  # ex: "average", "repeated_years", "nationality"
    valeur = models.TextField()  # JSON sérialisé d'un RuleValueData
    obligatoire = models.BooleanField(default=True)

    class Meta:
        managed = True
        db_table = "MST_ELIGIBILITY_CRITERIA"

    @property
    def rule_value(self) -> RuleValueData:
        return RuleValueData.from_json(self.valeur)

    @rule_value.setter
    def rule_value(self, data: RuleValueData) -> None:
        self.valeur = data.to_json()
