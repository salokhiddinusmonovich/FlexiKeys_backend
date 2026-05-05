import random
from django.db.models import Avg
from apps.API.game.models import Letter, GameSession, UserAction, Category
from apps.API.user.models import ChildProfile

class GameEngineService:
    @staticmethod
    def get_next_task(profile: ChildProfile, category_id: int):
        """
        Генерация задания с учетом адаптивного размера кнопок
        """
        letters_pool = Letter.objects.filter(category_id=category_id)
        if not letters_pool.exists():
            return {"error": "Category is empty"}

        # 1. Адаптивность по уровню (как и раньше)
        max_range = min(profile.current_level * 5, letters_pool.count())
        available_letters = list(letters_pool[:max_range])
        target_letter = random.choice(available_letters)

        # 2. Подготовка вариантов (options)
        options = [target_letter.char]
        all_chars = list(letters_pool.values_list('char', flat=True))
        
        # Для детей с проблемами моторики лучше держать 3-4 крупных варианта
        while len(options) < 4:
            wrong_char = random.choice(all_chars)
            if wrong_char not in options:
                options.append(wrong_char)
        random.shuffle(options)

        # 3. Начальный масштаб (берем из профиля или 1.0)
        # Если ребенок в прошлой сессии сильно мучился, можем начать сразу с 1.2
        initial_scale = getattr(profile, 'preferred_initial_size', 1.0)

        return {
            "letter_id": target_letter.id,
            "target": target_letter.char,
            "audio_url": target_letter.audio.url if target_letter.audio else None,
            "image_url": target_letter.image.url if target_letter.image else None,
            "options": options,
            "initial_scale": initial_scale,
            "growth_step": 0.2  # Те самые "+2 см" (условно 20% от размера)
        }

    @staticmethod
    def process_answer(profile: ChildProfile, session_id: int, letter_id: int, 
                       is_correct: bool, response_time: float, current_scale: float):
        """
        Логика роста клавиатуры и фиксации прогресса моторики
        """
        session = GameSession.objects.get(id=session_id)
        letter = Letter.objects.get(id=letter_id)

        # 1. ЛОГИКА РОСТА (Твоя фишка)
        if is_correct:
            # Если попал — уменьшаем кнопки к норме, но плавно (на 0.1)
            next_scale = max(1.0, current_scale - 0.1)
            reward = 10
            session.correct_count += 1
        else:
            # ОШИБКА — РАСТИМ КНОПКИ (Помогаем ребенку перебороть барьер)
            next_scale = current_scale + 0.2 
            reward = 0
            session.mistakes_count += 1

        # 2. Сохраняем действие (UserAction) для аналитики
        UserAction.objects.create(
            session=session,
            letter=letter,
            is_correct=is_correct,
            current_scale=current_scale, # Важно: на каком размере был тап
            reaction_time=response_time
        )
        
        session.save()
        profile.coins += reward
        profile.save()

        return {
            "is_correct": is_correct, 
            "next_scale": round(next_scale, 2), 
            "earned_coins": reward, 
            "new_balance": profile.coins,
            "feedback": "Great job!" if is_correct else "Don't worry, let's make it easier!"
        }

    @staticmethod
    def finalize_session(session_id: int, total_time: int):
        """
        Завершение сессии и расчет 'моторного прогресса'
        """
        session = GameSession.objects.get(id=session_id)
        
        # 1. Расчет точности (Accuracy)
        total_actions = session.correct_count + session.mistakes_count
        accuracy = (session.correct_count / total_actions) if total_actions > 0 else 0
        
        # 2. Расчет среднего масштаба (Насколько сильна была поддержка)
        # Чем ближе к 1.0, тем лучше моторика ребенка
        avg_scale = session.actions.aggregate(Avg('current_scale'))['current_scale__avg'] or 1.0

        # 3. Звезды по ТЗ 2.4
        if accuracy >= 0.9:
            stars = 3
        elif accuracy >= 0.7:
            stars = 2
        else:
            stars = 1

        # Обновляем сессию
        session.accuracy = accuracy
        session.stars_earned = stars
        session.time_spent = total_time
        session.average_keyboard_scale = round(avg_scale, 2)
        session.save()

        # Награждаем профиль
        profile = session.profile
        profile.stars += stars
        profile.save()

        return {
            "stars_earned": stars,
            "accuracy": round(accuracy * 100, 1),
            "avg_motor_support": session.average_keyboard_scale,
            "new_balance": profile.coins
        }