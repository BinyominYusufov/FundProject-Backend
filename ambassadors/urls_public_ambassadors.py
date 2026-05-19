from django.urls import path

from ambassadors.views_public import AmbassadorDetailView, AmbassadorListView

urlpatterns = [
    path("", AmbassadorListView.as_view(), name="ambassador-list"),
    path("<int:pk>/", AmbassadorDetailView.as_view(), name="ambassador-detail"),
]
