from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from .models import Post, Category # Імпортуємо Post та Category

# Немає потреби імпортувати Subscription, якщо ми не робимо загальну розсилку

@receiver(post_save, sender=Post)
def send_notification_on_publish(sender, instance, created, **kwargs):
    """
    Надсилає email-сповіщення, коли пост вперше публікується.
    Сповіщення надсилаються:
    1. Підписникам автора посту.
    2. Підписникам спільноти (категорії), де опубліковано пост.
    """
    
    # Перевіряємо, чи пост має статус 'published'
    if instance.status == 'published':
        was_published_before = False
        
        if not created:
            try:
                # Отримуємо попередній стан об'єкта з бази даних
                old_instance = Post.objects.get(pk=instance.pk)
                if old_instance.status == 'published':
                    was_published_before = True # Пост вже був опублікований
            except Post.DoesNotExist:
                pass # Об'єкт ще не в базі, це 'created' випадок
        
        # === ПОЧАТОК НОВОЇ ЛОГІКИ ===
        # Ми надсилаємо email, ТІЛЬКИ ЯКЩО пост вперше публікується
        if not was_published_before:
            
            # 1. Отримуємо підписників автора
            # (Звертаємось до 'followers', як визначено у CustomUser.following)
            author_followers = instance.author.followers.all()
            
            # 2. Отримуємо підписників спільноти
            # (Звертаємось до 'followers', як визначено у Category.followers)
            category_followers = instance.category.followers.all()
            
            # 3. Об'єднуємо два QuerySet'и в один, без дублікатів
            all_recipients = author_followers | category_followers
            
            # 4. Отримуємо список унікальних email-адрес
            #   - Вони мають бути активні
            #   - Вони не мають бути порожніми
            #   - Вони не мають належати автору посту (щоб не писати самому собі)
            subscriber_emails = all_recipients.filter(
                is_active=True, email__isnull=False
            ).exclude(
                email=''
            ).exclude(
                id=instance.author.id # Виключаємо автора посту
            ).values_list('email', flat=True).distinct()
            
            # Конвертуємо QuerySet у звичайний список
            email_list = list(subscriber_emails)
            
            if email_list:
                subject = f"Новий пост у /r/{instance.category.name}: {instance.title}"
                
                # Створюємо повне посилання, використовуючи SITE_URL
                post_url = settings.SITE_URL + instance.get_absolute_url() 
                
                message = (
                    f"Привіт!\n\n"
                    f"Користувач @{instance.author.username} або спільнота /r/{instance.category.name} (за якими ви слідкуєте) має новий пост:\n\n"
                    f"'{instance.title}'\n\n"
                    f"{instance.excerpt}\n\n"
                    f"Перегляньте його на нашому сайті: {post_url}\n\n"
                    f"Дякуємо, що ви з нами!\n"
                )
                
                try:
                    send_mail(
                        subject,
                        message,
                        settings.DEFAULT_FROM_EMAIL,
                        email_list,
                        fail_silently=False, 
                    )
                    print(f"Successfully sent notification for post '{instance.title}' to {len(email_list)} followers.")
                except Exception as e:
                    print(f"Помилка при відправці email: {e}")