from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator


class Language(models.Model):
    lang_code = models.CharField(max_length=5, unique=True) # uz, ru, en
    name = models.CharField(max_length=50)
    flag_icon = models.ImageField(upload_to='languages/', null=True)

    def __str__(self): return self.name

class ChildProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    nickname = models.CharField(max_length=100)
    age = models.IntegerField(null=True)
    language = models.ForeignKey(Language, on_delete=models.PROTECT)
    
    # Игровой баланс и прогресс (ТЗ 2.1)
    current_level = models.PositiveIntegerField(default=1)
    coins = models.PositiveIntegerField(default=0)
    stars = models.PositiveIntegerField(default=0)
    
    # Настройки из дизайна (Accessibility)
    high_focus_mode = models.BooleanField(default=False)
    larger_touch_targets = models.BooleanField(default=False)
    spoken_feedback = models.BooleanField(default=True)
    
    # Адаптивность: текущий множитель сложности (2, 3 или 4 варианта ответа)
    difficulty_factor = models.IntegerField(default=3)
    preferred_initial_scale = models.FloatField(default=1.0)
    exp = models.PositiveIntegerField(default=0, help_text="Опыт ребенка")
    last_reward_date = models.DateField(null=True, blank=True, help_text="Дата последнего бонуса")

    purchased_items = models.ManyToManyField("game.ShopItem", blank=True, related_name='owners')
    active_theme = models.ForeignKey("game.ShopItem", on_delete=models.SET_NULL, null=True, related_name='active_in_themes')
    active_keyboard = models.ForeignKey("game.ShopItem", on_delete=models.SET_NULL, null=True, related_name='active_in_keyboards')

    def __str__(self): return self.nickname