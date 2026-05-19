"""Strict response envelope shared by every ambassador endpoint.

All ambassador responses are exactly one of:
    {"success": True,  "data": ...}
    {"success": False, "message": ...}

DRF's own auth/permission/validation/not-found exceptions are reshaped into the
failure envelope while preserving the right HTTP status. Validation errors
(DRF default 400) are surfaced as 422 to match the module's API contract.
"""

from __future__ import annotations

from typing import Any

from rest_framework.response import Response
from rest_framework.views import APIView


def ok(data: Any, *, status: int = 200) -> Response:
    return Response({"success": True, "data": data}, status=status)


def fail(message: Any, *, status: int = 400) -> Response:
    return Response({"success": False, "message": message}, status=status)


class EnvelopeAPIView(APIView):
    """APIView whose error responses also follow the strict envelope."""

    def handle_exception(self, exc: Exception) -> Response:
        response = super().handle_exception(exc)
        data = response.data
        if isinstance(data, dict) and set(data) == {"detail"}:
            message: Any = data["detail"]
        else:
            message = data
        if response.status_code == 400:
            response.status_code = 422
        response.data = {"success": False, "message": message}
        return response
