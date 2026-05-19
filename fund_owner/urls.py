from django.urls import path

from .views import OrganizationDetailView, OrganizationListView, OrganizationProfileView

urlpatterns = [
    path("", OrganizationListView.as_view(), name="fund-owner-list"),
    path("profile/", OrganizationProfileView.as_view(), name="fund-owner-profile"),
    path("<int:pk>/", OrganizationDetailView.as_view(), name="fund-owner-detail"),
]
