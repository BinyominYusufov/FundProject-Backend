from __future__ import annotations

from rest_framework.throttling import AnonRateThrottle, UserRateThrottle


class ChangePasswordThrottle(UserRateThrottle):
    scope = "change_password"


class LoginThrottle(UserRateThrottle):
    scope = "login"


class RegisterThrottle(AnonRateThrottle):
    scope = "register"
