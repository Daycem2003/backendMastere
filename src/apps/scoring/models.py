from django.db import models

from src.shared.models import TimestampedSoftDeleteModel


class ScoreFormula(TimestampedSoftDeleteModel):
    pubkey = models.TextField(unique=True)
    master = models.OneToOneField("masters.Master", on_delete=models.CASCADE, related_name="score_formula", db_column="masterId")

    class Meta:
        managed = True
        db_table = "MST_SCORE_FORMULAS"


class ScoreCriterion(TimestampedSoftDeleteModel):
    pubkey = models.TextField(unique=True)
    score_formula = models.ForeignKey(ScoreFormula, on_delete=models.CASCADE, related_name="criteria", db_column="scoreFormulaId")
    critere = models.TextField()
    poids = models.FloatField()

    class Meta:
        managed = True
        db_table = "MST_SCORE_CRITERIA"
