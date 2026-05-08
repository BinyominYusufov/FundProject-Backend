from django.urls import path

from .views import UserListView, UserProfileView

urlpatterns = [
    path('me/', UserProfileView.as_view(), name='user-profile'),
    path('', UserListView.as_view(), name='user-list'),
]
