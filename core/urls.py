from django.contrib import admin
from django.urls import include, path

from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView




urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('apps.API.user.urls')),


    # Схема в формате YAML/JSON
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    
    # Красивый интерфейс Swagger (самый популярный)
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    
    # Альтернативный интерфейс Redoc
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]
