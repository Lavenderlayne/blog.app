from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from .models import Post, Subscription

@receiver(post_save, sender=Post)
def send_notification_on_publish(sender, instance, created, **kwargs):
    """
    Надсилає email-сповіщення, коли пост вперше публікується.
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
        
        if not was_published_before:
            
            subscribers = Subscription.objects.filter(is_active=True)
            subscriber_emails = [s.email for s in subscribers]
            
            if subscriber_emails:
                subject = f"Новий пост у блозі: {instance.title}"
                
                post_url = instance.get_absolute_url() 
                
                message = (
                    f"Привіт!\n\n"
                    f"У нашому блозі з'явився новий пост: '{instance.title}'.\n\n"
                    f"{instance.excerpt}\n\n"
                    f"Перегляньте його на нашому сайті (шлях): {post_url}\n\n"
                    f"Дякуємо, що ви з нами!\n"
                )
                
                try:
                    send_mail(
                        subject,
                        message,
                        settings.DEFAULT_FROM_EMAIL,
                        subscriber_emails,
                        fail_silently=False, 
                    )
                    print(f"Successfully sent notification for post '{instance.title}' to {len(subscriber_emails)} subscribers.")
                except Exception as e:
                    # У робочому проекті тут має бути логування помилок
                    print(f"Помилка при відправці email: {e}")