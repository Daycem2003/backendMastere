from django.http import JsonResponse
from django.views import View

from .models import ReferenceData


class ReferenceDataListView(View):

    def get(self, request, category):
        valid_categories = {
            ReferenceData.Category.CITY,
            ReferenceData.Category.UNIVERSITY,
            ReferenceData.Category.DOMAIN,
            ReferenceData.Category.NATIONALITY,
            ReferenceData.Category.TYPE_LICENCE,
        }

        if category not in valid_categories:
            return JsonResponse(
                {
                    "detail": "Invalid reference data category."
                },
                status=400,
            )

        data = ReferenceData.objects.filter(
            category=category,
            is_active=True,
        ).values(
            "pubkey",
            "value",
        )

        return JsonResponse(
            {
                "category": category,
                "results": list(data),
            }
        )