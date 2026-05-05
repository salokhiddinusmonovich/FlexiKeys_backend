from django.contrib import admin
from django.urls import include, path

from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)



urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('apps.API.user.urls')),
    path('', include('apps.API.game.urls')),



    # Схема в формате YAML/JSON
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    
    # Красивый интерфейс Swagger (самый популярный)
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    
    # Альтернативный интерфейс Redoc
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    # Эндпоинт для логина (выдает токены)
    path('api/v1/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),

    # Эндпоинт для обновления токена (когда 30 минут прошли)
    path('api/v1/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
