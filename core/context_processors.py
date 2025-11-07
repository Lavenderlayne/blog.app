# lavenderlayne/blog_app/blog_app-dev/core/context_processors.py

from .models import Category
from django.db.models import Count

def global_context(request):
    """
    Додає загальні змінні контексту, потрібні в base.html,
    зокрема список категорій.
    """
    categories = Category.objects.annotate(post_count=Count('post')).order_by('name')
    return {
        'categories': categories,
    }