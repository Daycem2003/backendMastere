from django.urls import path

from src.apps.knowledge.views.knowledge_views import KnowledgeAskView

urlpatterns = [
     path("ask/", KnowledgeAskView.as_view()),
]
