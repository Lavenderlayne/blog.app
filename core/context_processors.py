from .models import Category, Tag
from django.db.models import Count, Q

def global_context(request):
    """
    Додає загальні змінні контексту: категорії та популярні теги.
    """
    categories = Category.objects.annotate(post_count=Count('post')).order_by('name') 
    
    popular_tags = Tag.objects.annotate(
        post_count=Count('post', filter=Q(post__status='published')) 
    ).exclude(slug='').order_by('-post_count')[:10]

    return {
        'categories': categories,
        'popular_tags': popular_tags,
    }