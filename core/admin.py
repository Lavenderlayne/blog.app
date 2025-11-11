from django.contrib import admin
from django.utils import timezone
from django.db.models import Count
from .models import Category, Tag, Post, PostComment, PostVote, Subscription, Advertisement
from django.contrib.auth.models import Group

@admin.action(description='Опублікувати обрані пости')
def make_published(modeladmin, request, queryset):
    queryset.update(status='published', published_at=timezone.now())

@admin.action(description='Перемістити пости в архів')
def make_archived(modeladmin, request, queryset):
    queryset.update(status='archived')

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'get_post_count')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(post_count=Count('post'))
    
    @admin.display(description='Постів', ordering='post_count')
    def get_post_count(self, obj):
        return obj.post_count

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'get_post_count')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(post_count=Count('post'))
    
    @admin.display(description='Постів', ordering='post_count')
    def get_post_count(self, obj):
        return obj.post_count

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'category', 'status', 'created_at', 'vote_score', 'is_featured')
    list_filter = ('status', 'category', 'created_at', 'is_featured')
    list_editable = ('status', 'is_featured')
    search_fields = ('title', 'content', 'author__username')
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ('view_count', 'vote_score', 'share_count', 'created_at', 'updated_at', 'published_at')
    
    actions = [make_published, make_archived]
    
    fieldsets = (
        ('Основна інформація', {
            'fields': ('title', 'slug', 'author', 'category', 'status')
        }),
        ('Вміст', {
            'fields': ('content', 'excerpt', 'featured_image', 'video_url', 'tags')
        }),
        ('Налаштування', {
            'fields': ('is_featured', 'is_pinned', 'allow_comments')
        }),
        ('SEO', {
            'fields': ('meta_title', 'meta_description'),
            'classes': ('collapse',)
        }),
        ('Статистика (Тільки для читання)', {
            'fields': ('view_count', 'vote_score', 'share_count', 'created_at', 'updated_at', 'published_at'),
            'classes': ('collapse',)
        }),
    )

@admin.action(description='Схвалити обрані коментарі')
def approve_comments(modeladmin, request, queryset):
    queryset.update(is_active=True)

@admin.action(description='Приховати (видалити) обрані коментарі')
def hide_comments(modeladmin, request, queryset):
    queryset.update(is_active=False)

@admin.register(PostComment)
class PostCommentAdmin(admin.ModelAdmin):
    list_display = ('author', 'post', 'content_snippet', 'created_at', 'is_active')
    list_filter = ('is_active', 'created_at')
    search_fields = ('content', 'author__username', 'post__title')
    list_editable = ('is_active',)
    readonly_fields = ('created_at', 'updated_at')
    actions = [approve_comments, hide_comments]
    
    @admin.display(description='Коментар')
    def content_snippet(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content

@admin.register(PostVote)
class PostVoteAdmin(admin.ModelAdmin):
    list_display = ('user', 'post', 'value', 'created_at')
    list_filter = ('value', 'created_at')
    search_fields = ('user__username', 'post__title')

@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('email', 'user', 'is_active', 'subscribed_at')
    list_filter = ('is_active', 'subscribed_at')
    search_fields = ('email', 'user__username')
    list_editable = ('is_active',)

@admin.register(Advertisement)
class AdvertisementAdmin(admin.ModelAdmin):
    list_display = ('title', 'is_active', 'created_at', 'expires_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('title', 'content')
    list_editable = ('is_active',)
    prepopulated_fields = {'slug': ('title',)}

admin.site.unregister(Group)