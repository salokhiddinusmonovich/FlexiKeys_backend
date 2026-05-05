from drf_spectacular.utils import extend_schema, OpenApiParameter, inline_serializer
from rest_framework import serializers
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db.models import Avg
from django.db.models import Sum
from django.utils import timezone
from ..user.models import ChildProfile

from .models import Category, Letter, GameSession
from .serializer import *
from apps.service import GameEngineService

class CategoryListView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={200: CategorySerializer(many=True)}, 
        summary="Список миров",
        description="Возвращает список доступных категорий (миров) для текущего языка пользователя."
    )
    def get(self, request):
        categories = Category.objects.filter(alphabet__language=request.user.profile.language)
        serializer = CategorySerializer(categories, many=True)
        return Response(serializer.data)

class StartSessionView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        # ПАРАМЕТРЫ: Явно указываем category_id как обязательный в Query
        parameters=[
            OpenApiParameter("category_id", type=int, location=OpenApiParameter.QUERY, description="ID выбранного мира (категории)", required=True)
        ],
        responses={201: inline_serializer(
            name='StartSessionResponse',
            fields={'session_id': serializers.IntegerField()}
        )},
        summary="Начать новую сессию игры"
    )
    def post(self, request):
        category_id = request.query_params.get('category_id')
        category = get_object_or_404(Category, id=category_id)
        
        session = GameSession.objects.create(
            profile=request.user.profile,
            category=category
        )
        return Response({"session_id": session.id}, status=201)

class GetTaskView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        # ПАРАМЕТРЫ: category_id нужен, чтобы знать, из какого пула брать буквы
        parameters=[
            OpenApiParameter("category_id", type=int, location=OpenApiParameter.QUERY, description="ID мира", required=True)
        ],
        responses={200: TaskSerializer},
        summary="Получить задание (с параметрами масштаба)"
    )
    def get(self, request):
        category_id = request.query_params.get('category_id')
        task_data = GameEngineService.get_next_task(request.user.profile, category_id)
        return Response(task_data)

class SubmitAnswerView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        # Для POST с JSON-телом параметры подтянутся автоматически из AnswerRequestSerializer
        request=AnswerRequestSerializer,
        responses={200: AnswerResponseSerializer},
        summary="Отправить ответ (логика роста кнопок)"
    )
    def post(self, request):
        serializer = AnswerRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        
        result = GameEngineService.process_answer(
            profile=request.user.profile,
            session_id=data['session_id'],
            letter_id=data['letter_id'],
            answer=data['answer'],
            response_time=data['response_time'],
            current_scale=data['current_scale']
        )
        return Response(result)

class EndSessionView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=EndSessionRequestSerializer,
        responses={200: SessionResultResponseSerializer},
        summary="Завершить сессию и получить итоги"
    )
    def post(self, request):
        serializer = EndSessionRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        
        result = GameEngineService.finalize_session(
            session_id=data['session_id'],
            total_time=data['time_spent']
        )
        return Response(result)

class UnlockCategoryView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        # ПАРАМЕТРЫ: category_id берется из URL path
        parameters=[
            OpenApiParameter("category_id", type=int, location=OpenApiParameter.PATH, description="ID мира для покупки")
        ],
        summary="Купить мир за монеты",
        responses={200: inline_serializer(
            name='UnlockResponse',
            fields={'success': serializers.BooleanField(), 'new_balance': serializers.IntegerField()}
        )}
    )
    def post(self, request, category_id):
        profile = request.user.profile
        category = get_object_or_404(Category, id=category_id)
        
        if profile.coins >= category.price:
            profile.coins -= category.price
            # Здесь должна быть логика M2M или флага "куплено"
            category.is_locked = False 
            profile.save()
            category.save()
            return Response({"success": True, "new_balance": profile.coins})
        
        return Response({"error": "Not enough coins"}, status=400)
    


class DashboardStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile = request.user.profile
        today = timezone.now().date()
        
        # Все сессии пользователя
        all_sessions = profile.sessions.all()
        # Сессии только за сегодня
        today_sessions = all_sessions.filter(created_at__date=today)

        # Считаем агрегаты
        stats = all_sessions.aggregate(
            total_stars=Sum('stars_earned'),
            avg_accuracy=Avg('accuracy'),
            total_correct=Sum('correct_count'),
            total_mistakes=Sum('mistakes_count')
        )

        # Считаем время за сегодня (в минутах, как на скрине "5m")
        time_today_sec = today_sessions.aggregate(Sum('time_spent'))['time_spent__sum'] or 0
        time_today_min = round(time_today_sec / 60)

        # Лимит сессии (на скрине 5 / 20 min)
        daily_limit_max = 20 # Можно вынести в настройки профиля
        
        return Response({
            "stars": stats['total_stars'] or 0,
            "coins": profile.coins,
            "accuracy": round((stats['avg_accuracy'] or 0) * 100), # В процентах (0%)
            "time_today": f"{time_today_min}m", # Строка "5m"
            "correct_taps": stats['total_correct'] or 0,
            "mistakes": stats['total_mistakes'] or 0,
            "daily_limit": {
                "current": time_today_min,
                "max": daily_limit_max,
                "percentage": min(round((time_today_min / daily_limit_max) * 100), 100)
            }
        })
    


class LeaderboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Получаем всех учеников, сортируем по сумме звезд
        profiles = ChildProfile.objects.annotate(
            total_stars=Sum('sessions__stars_earned')
        ).order_by('-total_stars')[:100] # Топ-100

        data = []
        user_rank = None
        user_total_stars = 0

        for index, profile in enumerate(profiles):
            rank = index + 1
            is_me = (profile == request.user.profile)
            
            profile_data = {
                "rank": rank,
                "username": profile.user.first_name or profile.user.username,
                "avatar": profile.avatar.url if profile.avatar else None,
                "total_stars": profile.total_stars or 0,
                "is_me": is_me
            }
            data.append(profile_data)
            
            if is_me:
                user_rank = rank
                user_total_stars = profile.total_stars or 0

        # Если текущего пользователя нет в топ-100, находим его ранг отдельно
        if user_rank is None:
            # Логика поиска ранга вне топа...
            user_rank = "10+" 

        return Response({
            "user_rank": user_rank,
            "user_total_stars": user_total_stars,
            "top_3": data[:3], # Для подиума (Mia, Leo, Aiden)
            "full_list": data # Для списка ниже
        })
    


class ShopListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        category = request.query_params.get('category', 'theme')
        items = ShopItem.objects.filter(category=category)
        serializer = ShopItemSerializer(items, many=True, context={'request': request})
        return Response(serializer.data)

class BuyItemView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, item_id):
        profile = request.user.profile
        item = get_object_or_404(ShopItem, id=item_id)

        if profile.purchased_items.filter(id=item.id).exists():
            return Response({"error": "Уже куплено"}, status=400)

        if profile.coins < item.price:
            return Response({"error": "Недостаточно монет"}, status=400)

        profile.coins -= item.price
        profile.purchased_items.add(item)
        profile.save()

        return Response({"success": True, "new_balance": profile.coins})

class SetActiveItemView(APIView):
    """Смена текущей темы или звука"""
    permission_classes = [IsAuthenticated]

    def post(self, request, item_id):
        profile = request.user.profile
        item = get_object_or_404(ShopItem, id=item_id)

        if not profile.purchased_items.filter(id=item.id).exists():
            return Response({"error": "Сначала купите этот товар"}, status=400)

        if item.category == 'theme':
            profile.active_theme = item
        elif item.category == 'keyboard':
            profile.active_keyboard = item
        # и так далее...
        
        profile.save()
        return Response({"success": True})