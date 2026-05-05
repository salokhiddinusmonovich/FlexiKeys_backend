from rest_framework import serializers
from .models import ChildProfile, Language

class RegisterRequestSerializer(serializers.Serializer):
    email = serializers.EmailField(help_text="Email родителя")
    password = serializers.CharField(write_only=True, min_length=8)
    nickname = serializers.CharField(max_length=100)
    age = serializers.IntegerField(required=False, min_value=1, max_value=18)
    lang_code = serializers.CharField(max_length=5, help_text="Код языка: 'uz', 'ru' или 'en'")

class RegisterResponseSerializer(serializers.Serializer):
    access = serializers.CharField()
    refresh = serializers.CharField()
    nickname = serializers.CharField()
    # Добавил ID профиля, может пригодиться фронту
    profile_id = serializers.IntegerField()

class LoginRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})

class LoginResponseSerializer(serializers.Serializer):
    access = serializers.CharField()
    refresh = serializers.CharField()
    nickname = serializers.CharField()
    stars = serializers.IntegerField()
    level = serializers.IntegerField(source='current_level')
    coins = serializers.IntegerField()
    language_code = serializers.CharField(source='language.lang_code')
    
    # ВАЖНО: передаем базовый масштаб при логине
    initial_scale = serializers.FloatField(source='preferred_initial_scale')

class ProfileSerializer(serializers.ModelSerializer):
    """Полные данные профиля для экрана настроек"""
    lang_name = serializers.CharField(source='language.name', read_only=True)
    
    class Meta:
        model = ChildProfile
        fields = [
            'nickname', 'age', 'language', 'lang_name',
            'current_level', 'coins', 'stars', 'exp',
            'high_focus_mode', 'spoken_feedback', 
            'preferred_initial_scale', 'difficulty_factor'
        ]
        read_only_fields = ['current_level', 'coins', 'stars', 'exp']

class UpdateProfileSerializer(serializers.ModelSerializer):
    """Для изменения настроек родителя или данных ребенка"""
    class Meta:
        model = ChildProfile
        fields = [
            'nickname', 'age', 'language', 
            'high_focus_mode', 'spoken_feedback', 
            'preferred_initial_scale', 'difficulty_factor'
        ]

class LanguageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Language
        fields = ['id', 'lang_code', 'name', 'flag_icon']