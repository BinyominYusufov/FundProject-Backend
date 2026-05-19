from django.urls import path

from ambassadors.views_admin import (
    AdminAmbassadorApplicationApproveView,
    AdminAmbassadorApplicationDetailView,
    AdminAmbassadorApplicationListView,
    AdminAmbassadorApplicationRejectView,
)

urlpatterns = [
    path("", AdminAmbassadorApplicationListView.as_view(), name="admin-ambassador-application-list"),
    path("<int:pk>/", AdminAmbassadorApplicationDetailView.as_view(), name="admin-ambassador-application-detail"),
    path("<int:pk>/approve/", AdminAmbassadorApplicationApproveView.as_view(), name="admin-ambassador-application-approve"),
    path("<int:pk>/reject/", AdminAmbassadorApplicationRejectView.as_view(), name="admin-ambassador-application-reject"),
]
