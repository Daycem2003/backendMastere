import logging
import uuid

from django.db import transaction

from src.apps.masters.dto.master import (
    CreateEligibilityCriteriaDTO,
    CreateRequiredDocumentDTO,
    SetPasserellesDTO,
    SetScoreFormulaDTO,
)
from src.apps.eligibility.models import EligibilityCriteria
from src.apps.masters.models import Master
from src.apps.documents.models import RequiredDocument
from src.apps.scoring.models import ScoreCriterion, ScoreFormula

logger = logging.getLogger(__name__)


class EligibilityCriteriaService:
    @staticmethod
    def add_criteria(master: Master, dto: CreateEligibilityCriteriaDTO) -> EligibilityCriteria:
        return EligibilityCriteria.objects.create(
            pubkey=f"elig_{uuid.uuid4().hex[:24]}",
            master=master,
            type=dto.type,
            valeur=dto.valeur,
            obligatoire=dto.obligatoire,
        )

    @staticmethod
    @transaction.atomic
    def set_score_formula(master: Master, dto: SetScoreFormulaDTO) -> ScoreFormula:
        formula, _ = ScoreFormula.objects.get_or_create(
            master=master, defaults={"pubkey": f"scf_{uuid.uuid4().hex[:24]}"}
        )
        formula.criteria.all().delete()
        ScoreCriterion.objects.bulk_create(
            [
                ScoreCriterion(
                    pubkey=f"scc_{uuid.uuid4().hex[:24]}",
                    score_formula=formula,
                    critere=c.critere,
                    poids=c.poids,
                )
                for c in dto.criteria
            ]
        )
        return formula

    @staticmethod
    def add_required_document(master: Master, dto: CreateRequiredDocumentDTO) -> RequiredDocument:
        return RequiredDocument.objects.create(
            pubkey=f"rdoc_{uuid.uuid4().hex[:24]}", master=master, type=dto.type
        )

    @staticmethod
    def set_passerelles(master: Master, dto: SetPasserellesDTO) -> Master:
        """Déclare les masters M2 vers lesquels CE master (M1) accepte une
        passerelle. Voir `EligibilityService` (module `candidate_profile`)
        pour la consommation de cette relation."""
        cibles = list(Master.objects.filter(pubkey__in=dto.master_pubkeys, deleted_at__isnull=True))
        master.passerelles_vers.set(cibles)
        return master
