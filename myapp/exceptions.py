from __future__ import annotations


class EmailDeliveryError(Exception):
    """Raised when outbound email (SMTP) fails so callers can handle HTTP responses."""

    def __init__(self, message: str = "Email delivery failed.") -> None:
        self.message = message
        super().__init__(message)
