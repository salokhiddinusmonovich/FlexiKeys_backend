from rest_framework import serializers
from .models import Category, Letter, GameSession

from .models import ShopItem

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'image', 'is_locked', 'price']

class TaskSerializer(serializers.Serializer):
    """Данные для экрана реабилитации (ТЗ 2.2 + Адаптивность)"""
    letter_id = serializers.IntegerField()
    target = serializers.CharField(help_text="Слово или буква, которую нужно набрать")
    audio_url = serializers.URLField(allow_null=True)
    image_url = serializers.URLField(allow_null=True)
    options = serializers.ListField(child=serializers.CharField())
    
    # ПАРАМЕТРЫ РОСТА:
    initial_scale = serializers.FloatField(default=1.0, help_text="Стартовый масштаб для этого ребенка")
    growth_step = serializers.FloatField(default=0.2, help_text="Шаг увеличения при ошибке (например, +20%)")

class AnswerRequestSerializer(serializers.Serializer):
    """Запрос от фронтенда при нажатии на вариант"""
    session_id = serializers.IntegerField(help_text="ID текущей сессии")
    letter_id = serializers.IntegerField()
    answer = serializers.CharField()
    response_time = serializers.FloatField(help_text="Время ответа в секундах")
    
    # Текущий масштаб, чтобы замерить точность на данном размере
    current_scale = serializers.FloatField(default=1.0)

class AnswerResponseSerializer(serializers.Serializer):
    """Вердикт бэкенда и команда на изменение размера"""
    is_correct = serializers.BooleanField()
    
    # КОМАНДА ФРОНТЕНДУ:
    next_scale = serializers.FloatField(help_text="Новый масштаб кнопок (увеличенный при ошибке или нормальный при успехе)")
    
    earned_coins = serializers.IntegerField()
    new_balance = serializers.IntegerField()
    streak = serializers.IntegerField()
    feedback_message = serializers.CharField(allow_null=True) # Например: "Почти! Давай попробуем с кнопками побольше"

class SessionResultResponseSerializer(serializers.Serializer):
    """Итоги сессии для экрана Result"""
    stars_earned = serializers.IntegerField()
    accuracy = serializers.FloatField()
    
    # Метрика моторики: насколько ребенку в среднем был нужен большой масштаб
    avg_motor_support = serializers.FloatField(help_text="Средний уровень поддержки (масштаба)")
    
    coins_total = serializers.IntegerField()
    new_level = serializers.IntegerField()
    
class StatsResponseSerializer(serializers.Serializer):
    stars = serializers.IntegerField()
    coins = serializers.IntegerField()
    accuracy = serializers.IntegerField()
    time_today = serializers.CharField()
    correct_taps = serializers.IntegerField()
    mistakes = serializers.IntegerField()
    daily_limit = serializers.DictField()


class EndSessionRequestSerializer(serializers.Serializer):
    """Данные для завершения сессии"""
    session_id = serializers.IntegerField()
    time_spent = serializers.IntegerField(help_text="Общее время игры в секундах")




class ShopItemSerializer(serializers.ModelSerializer):
    is_purchased = serializers.SerializerMethodField()
    is_active = serializers.SerializerMethodField()

    class Meta:
        model = ShopItem
        fields = ['id', 'category', 'title', 'description', 'image', 'price', 'is_purchased', 'is_active']

    def get_is_purchased(self, obj):
        user = self.context['request'].user
        return user.profile.purchased_items.filter(id=obj.id).exists()

    def get_is_active(self, obj):
        profile = self.context['request'].user.profile
        return profile.active_theme_id == obj.id or profile.active_keyboard_id == obj.id

class RatingSerializer(serializers.Serializer):
    rank = serializers.IntegerField()
    username = serializers.CharField(source='user.username')
    avatar = serializers.ImageField(source='avatar') # Если есть в профиле
    total_stars = serializers.IntegerField()
    is_me = serializers.BooleanField(default=False)