from __future__ import annotations

from rest_framework.pagination import PageNumberPagination
from rest_framework.settings import api_settings

_DEFAULT_PAGE = int(getattr(api_settings, "PAGE_SIZE", 10) or 10)


class AdminUserPagination(PageNumberPagination):
    page_size = _DEFAULT_PAGE
    page_query_param = "page"
    page_size_query_param = "limit"
    max_page_size = 100
