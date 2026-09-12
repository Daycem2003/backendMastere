import logging
import uuid

from django.db import transaction

from src.apps.eligibility.dto.eligibility_rule import (
    CreateEligibilityRuleDTO,
    UpdateEligibilityRuleDTO,
)
from src.apps.eligibility.models import EligibilityCriteria

logger = logging.getLogger(__name__)


class EligibilityRuleService:
    @staticmethod
    @transaction.atomic
    def create(dto: CreateEligibilityRuleDTO, master) -> EligibilityCriteria:
        # La validation de cohérence (min<=max, opérateur compatible avec
        # le type, format de date...) est déjà appliquée par
        # `RuleValueData` au moment de sa construction (Pydantic) — un DTO
        # invalide ne peut pas atteindre ce service.
        criteria = EligibilityCriteria.objects.create(
            pubkey=f"elrl_{uuid.uuid4().hex[:24]}",
            master=master,
            criterion=dto.criterion,
            obligatoire=dto.obligatoire,
            valeur=dto.rule_value.to_json(),
        )
        logger.info(
            "eligibility_rule_created",
            extra={"rule_id": criteria.pk, "master_id": master.pk, "criterion": dto.criterion},
        )
        return criteria

    @staticmethod
    def update(criteria: EligibilityCriteria, dto: UpdateEligibilityRuleDTO) -> EligibilityCriteria:
        fields = []
        if dto.obligatoire is not None:
            criteria.obligatoire = dto.obligatoire
            fields.append("obligatoire")
        if dto.rule_value is not None:
            criteria.valeur = dto.rule_value.to_json()
            fields.append("valeur")
        if fields:
            criteria.save(update_fields=fields)
        return criteria

    @staticmethod
    def delete(criteria: EligibilityCriteria) -> None:
        from django.utils import timezone

        criteria.deleted_at = timezone.now()
        criteria.save(update_fields=["deleted_at"])
