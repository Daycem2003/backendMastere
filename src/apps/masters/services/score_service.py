import logging
import uuid

from django.db import transaction

from src.apps.masters.dto.master import AddRequiredDocumentDTO, SetScoreFormulaDTO
from src.apps.masters.exceptions.master_exceptions import ScoreFormulaAlreadyExists
from src.apps.masters.models import Master
from src.apps.documents.models import RequiredDocument
from src.apps.scoring.models import ScoreCriterion, ScoreFormula

logger = logging.getLogger(__name__)


class RequiredDocumentService:
    @staticmethod
    def add(master: Master, dto: AddRequiredDocumentDTO) -> RequiredDocument:
        existing = master.required_documents.filter(type=dto.type, deleted_at__isnull=True).first()
        if existing:
            return existing
        return RequiredDocument.objects.create(
            pubkey=f"reqd_{uuid.uuid4().hex[:24]}", master=master, type=dto.type
        )

    @staticmethod
    def remove(required_document: RequiredDocument) -> None:
        from django.utils import timezone

        required_document.deleted_at = timezone.now()
        required_document.save(update_fields=["deleted_at"])


class ScoreService:
    """Calcul de score — distinct de l'éligibilité (module `eligibility`) :
    un candidat non éligible n'est jamais scoré (filtré en amont), le score
    ne fait que classer les candidats déjà éligibles entre eux."""

    @staticmethod
    @transaction.atomic
    def set_formula(master: Master, dto: SetScoreFormulaDTO) -> ScoreFormula:
        formula, created = ScoreFormula.objects.get_or_create(
            master=master, defaults={"pubkey": f"scfm_{uuid.uuid4().hex[:24]}"}
        )
        if not created:
            formula.criteria.all().delete()

        ScoreCriterion.objects.bulk_create(
            [
                ScoreCriterion(
                    pubkey=f"scct_{uuid.uuid4().hex[:24]}",
                    score_formula=formula,
                    critere=c.critere,
                    poids=c.poids,
                )
                for c in dto.criteria
            ]
        )
        return formula

    @staticmethod
    def compute_score(candidate_metrics: dict[str, float], master: Master) -> float | None:
        """`candidate_metrics` : mapping {critere: valeur_numerique} déjà
        résolu par l'appelant (ex: `applications`) — ce service ne connaît
        pas le détail d'un candidat, seulement comment pondérer des
        métriques nommées. Retourne None si la formule est absente ou si
        une métrique requise manque (score non calculable plutôt que
        faussé par une valeur par défaut arbitraire)."""
        formula = getattr(master, "score_formula", None)
        if not formula:
            return None

        total = 0.0
        total_weight = 0.0
        for criterion in formula.criteria.all():
            if criterion.critere not in candidate_metrics:
                return None
            total += candidate_metrics[criterion.critere] * criterion.poids
            total_weight += criterion.poids

        return total / total_weight if total_weight else None
