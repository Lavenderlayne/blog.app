from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from .models import Post, Category

@receiver(post_save, sender=Post)
def send_notification_on_publish(sender, instance, created, **kwargs):
    if instance.status == 'published':
        was_published_before = False
        
        if not created:
            try:
                old_instance = Post.objects.get(pk=instance.pk)
                if old_instance.status == 'published':
                    was_published_before = True
            except Post.DoesNotExist:
                pass
        
        if not was_published_before:
            author_followers = instance.author.followers.all()
            category_followers = instance.category.followers.all()
            all_recipients = author_followers | category_followers
            subscriber_emails = all_recipients.filter(
                is_active=True, email__isnull=False
            ).exclude(
                email=''
            ).exclude(
                id=instance.author.id
            ).values_list('email', flat=True).distinct()
            email_list = list(subscriber_emails)
            
            if email_list:
                subject = f"Новий пост у /r/{instance.category.name}: {instance.title}"
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