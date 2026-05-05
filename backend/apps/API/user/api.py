from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from rest_framework.permissions import AllowAny, IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiExample, inline_serializer
from django.utils import timezone

from .models import ChildProfile, Language
from .serializer import *

class RegisterView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        summary="Регистрация ребенка",
        request=RegisterRequestSerializer,
        responses={201: RegisterResponseSerializer}
    )
    @transaction.atomic
    def post(self, request):
        serializer = RegisterRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        # 1. Создаем системного пользователя (Django User)
        if User.objects.filter(email=data['email']).exists():
            return Response({"error": "Этот email уже занят"}, status=400)

        user = User.objects.create_user(
            username=data['email'],
            email=data['email'],
            password=data['password']
        )

        # 2. Ищем язык или берем по умолчанию
        lang = Language.objects.filter(lang_code=data['lang_code']).first()
        if not lang:
            return Response({"error": "Язык не поддерживается"}, status=400)

        # 3. Создаем игровой профиль
        profile = ChildProfile.objects.create(
            user=user,
            nickname=data['nickname'],
            age=data.get('age'),
            language=lang
        )

        refresh = RefreshToken.for_user(user)
        return Response({
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "nickname": profile.nickname,
            "profile_id": profile.id
        }, status=status.HTTP_201_CREATED)

class LoginView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        summary="Авторизация (Логин)",
        request=LoginRequestSerializer,
        responses={200: LoginResponseSerializer}
    )
    def post(self, request):
        serializer = LoginRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = authenticate(
            username=serializer.validated_data['email'], 
            password=serializer.validated_data['password']
        )
        
        if not user:
            return Response({"error": "Неверный email или пароль"}, status=401)

        refresh = RefreshToken.for_user(user)
        profile = user.profile

        # Возвращаем расширенные данные для старта игры
        return Response({
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "nickname": profile.nickname,
            "stars": profile.stars,
            "level": profile.current_level,
            "coins": profile.coins,
            "language_code": profile.language.lang_code,
            "initial_scale": profile.preferred_initial_scale  # Фронт сразу знает размер кнопок
        }, status=200)

class ProfileView(APIView):
    permission_classes = [IsAuthenticated]


    @extend_schema(
        summary="Обновить настройки доступности",
        description="PATCH запрос для изменения масштаба, режима фокуса и т.д. Можно присылать только измененные поля.",
        request=UpdateProfileSerializer, 
        responses={200: ProfileSerializer},
        tags=['Profile']
    )

    @extend_schema(responses={200: ProfileSerializer}, summary="Инфо и настройки профиля")
    def get(self, request):
        serializer = ProfileSerializer(request.user.profile)
        return Response(serializer.data)

    @extend_schema(
        request=UpdateProfileSerializer, 
        responses={200: ProfileSerializer}, 
        summary="Обновить настройки доступности и профиль"
    )
    def patch(self, request):
        profile = request.user.profile
        serializer = UpdateProfileSerializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        # Возвращаем обновленный профиль через основной сериализатор
        return Response(ProfileSerializer(profile).data)
    
class LeaderboardView(APIView):
    permission_classes = [IsAuthenticated]
    @extend_schema(
        summary="Топ игроков по звездам",
        responses={
            200: inline_serializer(
                name='LeaderboardResponse',
                many=True,
                fields={
                    'rank': serializers.IntegerField(),
                    'nickname': serializers.CharField(),
                    'stars': serializers.IntegerField(),
                    'level': serializers.IntegerField(),
                    'is_me': serializers.BooleanField(),
                }
            )
        },
        tags=['Social']
    )

    @extend_schema(summary="Топ игроков по звездам")
    def get(self, request):
        # Берем топ-10 детей, исключая пустые профили
        top_players = ChildProfile.objects.filter(stars__gt=0).order_by('-stars')[:10]
        
        data = []
        for i, p in enumerate(top_players, 1):
            data.append({
                "rank": i,
                "nickname": p.nickname,
                "stars": p.stars,
                "level": p.current_level,
                "is_me": p.user == request.user # Чтобы ребенок видел себя в списке
            })
        return Response(data)
    
class DailyRewardView(APIView):
    permission_classes = [IsAuthenticated]
    @extend_schema(
        summary="Забрать ежедневный бонус",
        responses={
            200: inline_serializer(
                name='DailyRewardResponse',
                fields={
                    'success': serializers.BooleanField(),
                    'reward': serializers.IntegerField(),
                    'new_balance': serializers.IntegerField()
                }
            ),
            400: inline_serializer(
                name='DailyRewardError',
                fields={'error': serializers.CharField()}
            )
        },
        tags=['Social']
    )

    @extend_schema(summary="Забрать ежедневный бонус")
    def post(self, request):
        profile = request.user.profile
        today = timezone.now().date()
        
        # Проверяем, забирал ли уже (можно добавить поле last_login_reward в модель)
        if profile.last_reward_date == today:
            return Response({"error": "Сегодня ты уже получил подарок!"}, status=400)
            
        profile.coins += 50
        profile.last_reward_date = today
        profile.save()
        
        return Response({
            "success": True, 
            "reward": 50, 
            "new_balance": profile.coins
        })
    

class LanguageListView(APIView):
    permission_classes = [AllowAny] # Разрешаем всем, даже неавторизованным

    @extend_schema(
        summary="Список доступных языков",
        description="Используется на самом первом экране приложения для выбора локализации.",
        responses={200: LanguageSerializer(many=True)},
        tags=['Content']
    )
    def get(self, request):
        languages = Language.objects.all()
        serializer = LanguageSerializer(languages, many=True)
        return Response(serializer.data)