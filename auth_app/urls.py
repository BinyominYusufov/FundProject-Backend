from django.urls import path

from .views import (
    ChangePasswordView,
    CustomTokenObtainPairView,
    LoginView,
    LogoutView,
    RegisterView,
    TokenRefreshView,
)

urlpatterns = [
    path("token/", CustomTokenObtainPairView.as_view(), name="token-obtain-pair"),
    path("change-password/", ChangePasswordView.as_view(), name="auth-change-password"),
    path("register/", RegisterView.as_view(), name="auth-register"),
    path("login/", LoginView.as_view(), name="auth-login"),
    path("logout/", LogoutView.as_view(), name="auth-logout"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
]
