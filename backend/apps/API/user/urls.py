from django.urls import path
from .views import index_page
from .api import (
    RegisterView, 
    LoginView, 
    ProfileView, 
    LeaderboardView, 
    DailyRewardView,
    LanguageListView
)

urlpatterns = [
    # --- Основные страницы (HTML/Web) ---
    path('', index_page, name='home'), 

    # --- Авторизация (Auth) ---
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),

    # --- Профиль и Настройки (Child Profile) ---
    # GET: получить инфо, PATCH: обновить настройки (масштаб, фокус и т.д.)
    path('me/', ProfileView.as_view(), name='profile-detail'),
    
    # --- Игровая социалка и бонусы ---
    # Топ игроков по звездам
    path('leaderboard/', LeaderboardView.as_view(), name='leaderboard'),
    
    # Забрать ежедневные монеты
    path('daily-reward/', DailyRewardView.as_view(), name='daily-reward'),

    # --- Контентные справочники ---
    # Список доступных языков (RU, UZ, EN) с флагами для экрана выбора
    path('languages/', LanguageListView.as_view(), name='languages-list'),
]