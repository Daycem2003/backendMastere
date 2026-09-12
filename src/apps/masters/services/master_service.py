import logging
import uuid

from django.db import transaction

from src.apps.masters.dto.master import (
    CreateMasterDTO,
    SetAcceptedLicenceTypesDTO,
    SetPasserellesDTO,
    UpdateMasterDTO,
)
from src.apps.masters.exceptions.master_exceptions import (
    InvalidPasserelleTarget,
    MasterNotEditable,
    TypeLicenceNotFound,
)
from src.apps.masters.models import Master, MasterStatus

logger = logging.getLogger(__name__)

UNIVERSITE_PAR_DEFAUT = "Université de Sousse"
VILLE_PAR_DEFAUT = "Sousse"


class MasterService:
    @staticmethod
    @transaction.atomic
    def create(dto: CreateMasterDTO, coordinateur) -> Master:
        from src.apps.candidate_profile.models import TypeLicence

        master = Master.objects.create(
            pubkey=f"mst_{uuid.uuid4().hex[:24]}",
            nom=dto.nom,
            universite=UNIVERSITE_PAR_DEFAUT,
            ville=VILLE_PAR_DEFAUT,
            domaine=dto.domaine,
            discipline=dto.discipline,
            specialite=dto.specialite,
            nombre_places=dto.nombre_places,
            date_debut=dto.date_debut,
            date_fin=dto.date_fin,
            coordinateur=coordinateur,
        )
        if dto.type_licence_pubkeys:
            types = TypeLicence.objects.filter(pubkey__in=dto.type_licence_pubkeys, deleted_at__isnull=True)
            if types.count() != len(set(dto.type_licence_pubkeys)):
                raise TypeLicenceNotFound()
            master.type_licences_acceptees.set(types)

        logger.info("master_created", extra={"master_id": master.pk, "coordinateur_id": coordinateur.id})
        return master

    @staticmethod
    def update(master: Master, dto: UpdateMasterDTO) -> Master:
        if master.statut == MasterStatus.OUVERT:
            raise MasterNotEditable()

        fields = []
        for field in ("nom", "ville", "nombre_places", "date_debut", "date_fin"):
            value = getattr(dto, field)
            if value is not None:
                setattr(master, field, value)
                fields.append(field)
        if fields:
            master.save(update_fields=fields)
        return master

    @staticmethod
    def set_accepted_licence_types(master: Master, dto: SetAcceptedLicenceTypesDTO) -> Master:
        from src.apps.candidate_profile.models import TypeLicence

        types = TypeLicence.objects.filter(pubkey__in=dto.type_licence_pubkeys, deleted_at__isnull=True)
        if types.count() != len(set(dto.type_licence_pubkeys)):
            raise TypeLicenceNotFound()
        master.type_licences_acceptees.set(types)
        return master

    @staticmethod
    def set_passerelles(master: Master, dto: SetPasserellesDTO) -> Master:
        """`from_master_pubkeys` = les masters M1 depuis lesquels une
        passerelle vers CE master est ouverte (`passerelles_depuis`)."""
        if master.pubkey in dto.from_master_pubkeys:
            raise InvalidPasserelleTarget()

        origins = Master.objects.filter(pubkey__in=dto.from_master_pubkeys, deleted_at__isnull=True)
        if origins.count() != len(set(dto.from_master_pubkeys)):
            raise MasterNotEditable()  # réutilisé par simplicité — un pubkey inconnu
        master.passerelles_depuis.set(origins)
        return master

    @staticmethod
    def publish(master: Master) -> Master:
        master.statut = MasterStatus.OUVERT
        master.save(update_fields=["statut"])
        logger.info("master_published", extra={"master_id": master.pk})
        return master

    @staticmethod
    def close(master: Master) -> Master:
        master.statut = MasterStatus.FERME
        master.save(update_fields=["statut"])
        return master