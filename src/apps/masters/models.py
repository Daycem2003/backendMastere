from django.db import models

from src.shared.models import TimestampedSoftDeleteModel


class MasterStatus(models.TextChoices):
    OUVERT = "OUVERT", "Ouvert"
    FERME = "FERME", "Fermé"
    BROUILLON = "BROUILLON", "Brouillon"


class Master(TimestampedSoftDeleteModel):
    pubkey = models.TextField(unique=True)

    nom = models.TextField()
    universite = models.TextField()
    ville = models.TextField()
    domaine = models.TextField()
    discipline = models.TextField()
    specialite = models.TextField()
    nombre_places = models.IntegerField(db_column="nombrePlaces")
    date_debut = models.DateTimeField(db_column="dateDebut")
    date_fin = models.DateTimeField(db_column="dateFin")
    statut = models.CharField(max_length=16, choices=MasterStatus.choices, default=MasterStatus.BROUILLON)

    coordinateur = models.ForeignKey(
        "coordinator.Coordinateur", on_delete=models.PROTECT, related_name="masters", db_column="coordinateurId"
    )
    administrateur = models.ForeignKey(
        "administrator.Administrateur",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="masters",
        db_column="administrateurId",
    )

    # M2M "MasterTypeLicence" — TypeLicence vit dans candidate_profile.
    type_licences_acceptees = models.ManyToManyField(
        "candidate_profile.TypeLicence",
        related_name="masters",
        db_table="MST_MASTER_TYPE_LICENCES",
    )

    # Auto-relation M2M "MasterPasserelle" — asymétrique dans les deux sens
    # (Master A → Master B ne signifie pas B → A), donc `symmetrical=False`.
    passerelles_vers = models.ManyToManyField(
        "self",
        related_name="passerelles_depuis",
        symmetrical=False,
        db_table="MST_MASTER_PASSERELLES",
    )

    class Meta:
        managed = True
        db_table = "MST_MASTERS"