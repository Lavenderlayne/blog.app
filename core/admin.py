from django.contrib import admin
from .models import Category, Tag, Post, PostComment, PostVote, Subscription, Advertisement

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    # 2. Виправлено: 'like_count' замінено на 'vote_score'
    list_display = ('title', 'author', 'category', 'post_type', 'status', 'created_at', 'view_count', 'is_featured', 'vote_score')
    list_filter = ('status', 'post_type', 'category', 'created_at', 'is_featured')
    search_fields = ('title', 'content', 'excerpt')
    list_editable = ('status', 'is_featured')
    prepopulated_fields = {'slug': ('title',)}
    # 3. Виправлено: 'like_count' замінено на 'vote_score'
    readonly_fields = ('view_count', 'vote_score', 'share_count', 'created_at', 'updated_at')
    fieldsets = (
        ('Основна інформація', {
            'fields': ('title', 'slug', 'content', 'excerpt', 'author', 'category', 'tags')
        }),
        ('Налаштування', {
            'fields': ('post_type', 'status', 'featured_image', 'is_featured', 'is_pinned', 'allow_comments')
        }),
        ('SEO', {
            'fields': ('meta_title', 'meta_description'),
            'classes': ('collapse',)
        }),
        ('Статистика', {
            # 4. Виправлено: 'like_count' замінено на 'vote_score'
            'fields': ('view_count', 'vote_score', 'share_count', 'created_at', 'updated_at', 'published_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(PostComment)
class PostCommentAdmin(admin.ModelAdmin):
    list_display = ('author', 'post', 'created_at', 'is_active')
    list_filter = ('is_active', 'created_at')
    search_fields = ('content', 'author__username', 'post__title')
    list_editable = ('is_active',)
    readonly_fields = ('created_at', 'updated_at')

# 5. Виправлено: 'PostLike' замінено на 'PostVote'
@admin.register(PostVote)
class PostVoteAdmin(admin.ModelAdmin):
    # 6. Додано 'value' для відображення лайка/дизлайка
    list_display = ('user', 'post', 'value', 'created_at')
    list_filter = ('created_at', 'value')
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