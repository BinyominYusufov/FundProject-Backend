from django.urls import path

from ambassadors.views_admin import (
    AdminAmbassadorDetailView,
    AdminAmbassadorListCreateView,
    AdminAmbassadorToggleActiveView,
    AdminAmbassadorToggleFeaturedView,
)

urlpatterns = [
    path("", AdminAmbassadorListCreateView.as_view(), name="admin-ambassador-list-create"),
    path("<int:pk>/", AdminAmbassadorDetailView.as_view(), name="admin-ambassador-detail"),
    path("<int:pk>/toggle-active/", AdminAmbassadorToggleActiveView.as_view(), name="admin-ambassador-toggle-active"),
    path("<int:pk>/toggle-featured/", AdminAmbassadorToggleFeaturedView.as_view(), name="admin-ambassador-toggle-featured"),
]
