from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('user', 'Користувач'),
        ('moderator', 'Модератор'),
        ('admin', 'Адміністратор'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='user')
    
    following = models.ManyToManyField(
        'self', 
        symmetrical=False, 
        related_name='followers',
        blank=True,
        verbose_name='Слідкує за'
    )

    class Meta:
        verbose_name = 'Користувач'
        verbose_name_plural = 'Користувачі'

    def __str__(self):
        return self.username
    
    @property
    def is_moderator(self):
        return self.role == 'moderator'
    
    @property
    def is_admin(self):
        return self.role == 'admin'

class Profile(models.Model):
    user = models.OneToOneField(
        CustomUser, 
        on_delete=models.CASCADE, 
        related_name='profile'
    )
    bio = models.TextField(max_length=500, blank=True, verbose_name='Біографія')
    avatar = models.ImageField(
        upload_to='avatars/',
        null=True,
        blank=True,
        verbose_name='Аватар'
    )
    phone = models.CharField(max_length=20, blank=True, verbose_name='Телефон')
    website = models.URLField(blank=True, verbose_name='Вебсайт')
    location = models.CharField(max_length=100, blank=True, verbose_name='Місцезнаходження')
    birth_date = models.DateField(null=True, blank=True, verbose_name='Дата народження')
    social_x = models.URLField(blank=True, verbose_name='X')
    social_telegram = models.CharField(max_length=100, blank=True, verbose_name='Telegram')
    social_discord = models.CharField(max_length=100, blank=True, verbose_name='Discord')
    email_notifications = models.BooleanField(default=True, verbose_name='Email сповіщення')
    email_subscriptions = models.BooleanField(default=True, verbose_name='Підписки на новини')

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата створення')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата оновлення')

    class Meta:
        verbose_name = 'Профіль'
        verbose_name_plural = 'Профілі'

    def __str__(self):
        return f'Профіль користувача {self.user.username}'
    
    @receiver(post_save, sender=CustomUser)
    def create_user_profile(sender, instance, created, **kwargs):
        if created:
            Profile.objects.create(user=instance)

    @receiver(post_save, sender=CustomUser)
    def save_user_profile(sender, instance, **kwargs):
        if hasattr(instance, 'profile'):
            instance.profile.save()