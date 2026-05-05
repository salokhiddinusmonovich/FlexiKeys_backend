from django.urls import path
from .api import (
    CategoryListView, 
    UnlockCategoryView, 
    GetTaskView, 
    SubmitAnswerView,
    StartSessionView, 
    EndSessionView, 
    DashboardStatsView,
    LeaderboardView,    
    ShopListView,       
    BuyItemView,        
    SetActiveItemView   
)

app_name = 'game'

urlpatterns = [
    # --- Миры и Категории ---
    path('categories/', CategoryListView.as_view(), name='category-list'),
    path('categories/<int:category_id>/unlock/', UnlockCategoryView.as_view(), name='category-unlock'),
    
    # --- Игровой процесс (Core) ---
    path('session/start/', StartSessionView.as_view(), name='session-start'),
    path('task/', GetTaskView.as_view(), name='get-task'),
    path('answer/', SubmitAnswerView.as_view(), name='submit-answer'),
    path('session/end/', EndSessionView.as_view(), name='session-end'),
    
    # --- Статистика и Рейтинг ---
    # Основной дашборд прогресса
    path('dashboard/', DashboardStatsView.as_view(), name='dashboard-main'),
    # Глобальный рейтинг учеников (Топ-100)
    path('leaderboard/', LeaderboardView.as_view(), name='leaderboard'),

    # --- Магазин и Кастомизация ---
    # Список товаров (темы, клавиатуры и т.д.)
    path('shop/', ShopListView.as_view(), name='shop-list'),
    # Покупка нового предмета
    path('shop/buy/<int:item_id>/', BuyItemView.as_view(), name='shop-buy'),
    # Активация/смена текущего оформления
    path('shop/active/<int:item_id>/', SetActiveItemView.as_view(), name='shop-set-active'),
]