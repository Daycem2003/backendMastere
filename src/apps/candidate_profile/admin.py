from django.contrib import admin

from .models import (
    CandidateProfile,
    Diplome,
    LicenceYear,
    Master1Year,
    Redoublement,
    RedoublementYear,
    TypeLicence,
)


@admin.register(CandidateProfile)
class CandidateProfileAdmin(admin.ModelAdmin):
    list_display = ("id", "pubkey", "nom", "prenom", "cin", "statut")
    list_filter = ("statut",)
    search_fields = ("pubkey", "cin", "email", "nom", "prenom")


@admin.register(TypeLicence)
class TypeLicenceAdmin(admin.ModelAdmin):
    list_display = ("id", "pubkey", "intitule", "domaine", "est_eligible")
    list_filter = ("est_eligible", "domaine")


@admin.register(LicenceYear)
class LicenceYearAdmin(admin.ModelAdmin):
    list_display = ("id", "candidate_profile", "annee", "moyenne")


@admin.register(Diplome)
class DiplomeAdmin(admin.ModelAdmin):
    list_display = ("id", "candidate_profile", "type_licence", "universite")


@admin.register(Master1Year)
class Master1YearAdmin(admin.ModelAdmin):
    list_display = ("id", "candidate_profile", "etablissement", "master", "moyenne")
    list_filter = ("master",)


@admin.register(Redoublement)
class RedoublementAdmin(admin.ModelAdmin):
    list_display = ("id", "candidate_profile", "a_redouble")


@admin.register(RedoublementYear)
class RedoublementYearAdmin(admin.ModelAdmin):
    list_display = ("id", "redoublement", "annee")
