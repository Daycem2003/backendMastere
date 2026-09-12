from django.urls import path
from .views import ReferenceDataListView

urlpatterns = [
    path("<str:category>/", ReferenceDataListView.as_view(), name="reference-data"),
]