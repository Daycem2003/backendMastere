from django.contrib import admin

from .models import EligibilityCriteria


@admin.register(EligibilityCriteria)
class EligibilityCriteriaAdmin(admin.ModelAdmin):
    list_display = ("id", "pubkey", "master", "criterion", "obligatoire")
    list_filter = ("obligatoire",)
    search_fields = ("pubkey", "criterion", "master__pubkey")
