from django.urls import path
from . import views,ai
urlpatterns=[path('plans/',views.plans),path('subscription/',views.subscription),path('webhook/',views.webhook),path('owner/session/',views.owner_session),path('owner/console/',views.owner_console),path('owner/report/',views.owner_report),path('ai/',ai.prepare),path('ai/<str:proposal_id>/review/',ai.review),path('ai/<str:proposal_id>/confirm/',ai.confirm),path('ai/<str:proposal_id>/source/',ai.source)]
