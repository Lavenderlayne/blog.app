# Файл: lavenderlayne/blog_app/blog_app-dev/core/context_processors.py

from .models import Category, Tag #
from django.db.models import Count, Q

def global_context(request):
    """
    Додає загальні змінні контексту: категорії та популярні теги.
    """

    categories = Category.objects.annotate(post_count=Count('post')).order_by('name') #
    published_post_filter = Q(post__status='published') 
    popular_tags = Tag.objects.filter(
        published_post_filter 
    ).annotate(
        post_count=Count('post', filter=published_post_filter)
    ).order_by('-post_count')[:10]

    return {
        'categories': categories,
        'popular_tags': popular_tags,
    }