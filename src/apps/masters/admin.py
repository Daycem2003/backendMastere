from django.contrib import admin

from .models import Master
from src.apps.administrator.models import Administrateur
from src.apps.coordinator.models import Coordinateur
from src.apps.documents.models import RequiredDocument
from src.apps.scoring.models import ScoreFormula, ScoreCriterion


@admin.register(Master)
class MasterAdmin(admin.ModelAdmin):
    list_display = ("id", "pubkey", "nom", "universite", "statut", "nombre_places")
    list_filter = ("statut", "domaine")
    search_fields = ("pubkey", "nom", "universite")
    filter_horizontal = ("type_licences_acceptees", "passerelles_vers")


@admin.register(RequiredDocument)
class RequiredDocumentAdmin(admin.ModelAdmin):
    list_display = ("id", "master", "type")


@admin.register(ScoreFormula)
class ScoreFormulaAdmin(admin.ModelAdmin):
    list_display = ("id", "master")


@admin.register(ScoreCriterion)
class ScoreCriterionAdmin(admin.ModelAdmin):
    list_display = ("id", "score_formula", "critere", "poids")


@admin.register(Coordinateur)
class CoordinateurAdmin(admin.ModelAdmin):
    list_display = ("id", "pubkey", "nom", "email")


@admin.register(Administrateur)
class AdministrateurAdmin(admin.ModelAdmin):
    list_display = ("id", "pubkey", "nom", "email")
