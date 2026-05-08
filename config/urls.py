from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path, re_path
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions

schema_view = get_schema_view(
    openapi.Info(
        title='Payvast API',
        default_version='v1',
        description='REST API documentation',
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('admin/users/', include('users.admin_urls')),
    path('api/v1/admin/users/', include('users.admin_urls')),
    path('admin/campaigns/', include('campaigns.admin_urls')),
    path('admin/donations/', include('donations.admin_urls')),
    path('admin/applications/', include('applications.admin_urls')),
    path('admin/', admin.site.urls),    
    re_path(
        r'^swagger(?P<format>\.json|\.yaml)$',
        schema_view.without_ui(cache_timeout=0),
        name='schema-json-yaml-root',
    ),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='swagger-ui-root'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='redoc-ui-root'),
    re_path(
        r'^api/swagger(?P<format>\.json|\.yaml)$',
        schema_view.without_ui(cache_timeout=0),
        name='schema-json-yaml',
    ),
    path('api/swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='swagger-ui'),
    path('api/redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='redoc'),
    path('api/auth/', include('auth_app.urls')),
    path('api/users/', include('users.urls')),
    path('api/campaigns/', include('campaigns.urls')),
    path('api/donations/', include('donations.urls')),
    path('api/fund-owner/', include('fund_owner.urls')),
    path('api/fund-applications/', include('myapp.urls')),
    path('api/applications/', include('applications.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
