import logging
import uuid

from django.db import transaction

from src.apps.candidate_profile.dto.candidate_profile import (
    CreateDiplomeDTO,
    CreateLicenceYearDTO,
    CreateMaster1YearDTO,
    SetRedoublementDTO,
)
from src.apps.candidate_profile.exceptions.candidate_profile_exceptions import (
    MasterOriginNotFound,
    TypeLicenceNotEligible,
    TypeLicenceNotFound,
)
from src.apps.candidate_profile.models import (
    CandidateProfile,
    Diplome,
    LicenceYear,
    Master1Year,
    Redoublement,
    RedoublementYear,
    TypeLicence,
)

logger = logging.getLogger(__name__)


class AcademicRecordService:
    @staticmethod
    def add_licence_year(
        profile: CandidateProfile,
        dto: CreateLicenceYearDTO,
    ) -> LicenceYear:
        type_licence = TypeLicence.objects.filter(
            pubkey=dto.type_licence_pubkey,
            deleted_at__isnull=True,
        ).first()

        if not type_licence:
            raise TypeLicenceNotFound()

        if not type_licence.est_eligible:
            raise TypeLicenceNotEligible()

        return LicenceYear.objects.create(
            pubkey=f"licy_{uuid.uuid4().hex[:24]}",
            candidate_profile=profile,
            type_licence=type_licence,
            annee=dto.annee,
            annee_universitaire=dto.annee_universitaire,
            moyenne=dto.moyenne,
        )

    @staticmethod
    @transaction.atomic
    def set_diplome(
        profile: CandidateProfile,
        dto: CreateDiplomeDTO,
    ) -> Diplome:
        type_licence = TypeLicence.objects.filter(
            pubkey=dto.type_licence_pubkey,
            deleted_at__isnull=True,
        ).first()

        if not type_licence:
            raise TypeLicenceNotFound()

        if not type_licence.est_eligible:
            raise TypeLicenceNotEligible()

        return Diplome.objects.create(
            pubkey=f"dipl_{uuid.uuid4().hex[:24]}",
            candidate_profile=profile,
            type_licence=type_licence,
            annee_obtention=dto.annee_obtention,
            universite=dto.universite,
        )

    @staticmethod
    def set_master1_year(
        profile: CandidateProfile,
        dto: CreateMaster1YearDTO,
    ) -> Master1Year:
        """Si `master_pubkey` est fourni (le M1 a été fait sur un master de
        la plateforme), le lien formel est enregistré — condition
        nécessaire pour que `EligibilityService` puisse vérifier
        automatiquement une éligibilité en passerelle M1 -> M2.
        """
        from src.apps.masters.models import Master

        master = None

        if dto.master_pubkey:
            master = Master.objects.filter(
                pubkey=dto.master_pubkey,
                deleted_at__isnull=True,
            ).first()

            if not master:
                raise MasterOriginNotFound()

        existing = Master1Year.objects.filter(
            candidate_profile=profile,
            deleted_at__isnull=True,
        ).first()

        if existing:
            existing.annee_universitaire = dto.annee_universitaire
            existing.moyenne = dto.moyenne
            existing.etablissement = dto.etablissement
            existing.master = master
            existing.save(
                update_fields=[
                    "annee_universitaire",
                    "moyenne",
                    "etablissement",
                    "master",
                ]
            )
            return existing

        return Master1Year.objects.create(
            pubkey=f"m1y_{uuid.uuid4().hex[:24]}",
            candidate_profile=profile,
            master=master,
            annee_universitaire=dto.annee_universitaire,
            moyenne=dto.moyenne,
            etablissement=dto.etablissement,
        )

    @staticmethod
    @transaction.atomic
    def set_redoublement(
        profile: CandidateProfile,
        dto: SetRedoublementDTO,
    ) -> Redoublement:
        redoublement, _ = Redoublement.objects.get_or_create(
            candidate_profile=profile,
            defaults={"pubkey": f"redb_{uuid.uuid4().hex[:24]}"},
        )

        redoublement.a_redouble = dto.a_redouble
        redoublement.save(update_fields=["a_redouble"])

        redoublement.redoublement_years.all().delete()

        RedoublementYear.objects.bulk_create(
            [
                RedoublementYear(
                    pubkey=f"redy_{uuid.uuid4().hex[:24]}",
                    redoublement=redoublement,
                    annee=annee,
                )
                for annee in dto.annees
            ]
        )

        return redoublement

