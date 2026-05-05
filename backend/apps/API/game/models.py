from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from apps.API.user.models import ChildProfile, Language 


class Alphabet(models.Model):
    language = models.OneToOneField(Language, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    
    def __str__(self): return self.title

class Category(models.Model):
    """Миры (Fruits, Animals), которые открываются за монеты"""
    alphabet = models.ForeignKey(Alphabet, on_delete=models.CASCADE)
    name = models.CharField(max_length=100) 
    image = models.ImageField(upload_to='categories/icons/')
    is_locked = models.BooleanField(default=True)
    price = models.IntegerField(default=500) 

    def __str__(self): return self.name

class Letter(models.Model):
    """Целевой символ, который нужно нажать"""
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='letters')
    char = models.CharField(max_length=5)
    audio = models.FileField(upload_to='letters/audio/', null=True, blank=True)
    image = models.ImageField(upload_to='letters/visuals/', null=True, blank=True) 
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self): return f"{self.char} ({self.category.name})"

class GameSession(models.Model):
    """Сессия игры для анализа прогресса моторики"""
    profile = models.ForeignKey(ChildProfile, on_delete=models.CASCADE, related_name='sessions')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    
    # Статистика попаданий
    correct_count = models.IntegerField(default=0)
    mistakes_count = models.IntegerField(default=0)
    
    # Инклюзивные метрики (Accessibility)
    # Показывает, насколько сильно пришлось увеличивать клавиатуру в среднем
    average_keyboard_scale = models.FloatField(default=1.0, help_text="Средний масштаб кнопок за сессию")
    
    # Итоги
    time_spent = models.IntegerField(help_text="в секундах", null=True, blank=True)
    stars_earned = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(3)], 
        null=True, blank=True
    )
    accuracy = models.FloatField(null=True, blank=True) 
    average_reaction_time = models.FloatField(default=0.0) 
    
    created_at = models.DateTimeField(auto_now_add=True)

class UserAction(models.Model):
    """Лог каждого нажатия — сердце нашей адаптивной системы"""
    session = models.ForeignKey(GameSession, on_delete=models.CASCADE, related_name='actions')
    letter = models.ForeignKey(Letter, on_delete=models.CASCADE)
    is_correct = models.BooleanField()
    
    # ГЛАВНОЕ: Сохраняем, какой был размер кнопки в момент этого действия
    # Это поможет понять: "Ребенок не может попасть при 1.0, но попадает при 1.5"
    current_scale = models.FloatField(default=1.0, help_text="Масштаб интерфейса в момент нажатия")
    
    reaction_time = models.FloatField(help_text="Время реакции в секундах") 
    timestamp = models.DateTimeField(auto_now_add=True)




class ShopItem(models.Model):
    CATEGORY_CHOICES = [
        ('theme', 'Темы'),
        ('keyboard', 'Клавиатуры'),
        ('accessory', 'Аксессуары'),
        ('sound', 'Звуки'),
    ]
    
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    title = models.CharField(max_length=100)
    description = models.CharField(max_length=255, help_text="Подзаголовок (например, 'Cool blue ocean vibes')")
    image = models.ImageField(upload_to='shop/icons/')
    price = models.IntegerField(default=50)

    def __str__(self):
        return f"[{self.get_category_display()}] {self.title}"