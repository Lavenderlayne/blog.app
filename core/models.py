from django.db import models
from django.conf import settings
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify

class Category(models.Model):
    """Модель категорії для постів/статей"""
    name = models.CharField(max_length=100, verbose_name="Назва категорії")
    slug = models.SlugField(max_length=100, unique=True, verbose_name="URL")
    description = models.TextField(blank=True, verbose_name="Опис")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Створено")
    
    class Meta:
        verbose_name = "Категорія"
        verbose_name_plural = "Категорії"
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('category_detail', kwargs={'slug': self.slug})


class Tag(models.Model):
    """Модель тегу для постів"""
    name = models.CharField(max_length=50, verbose_name="Назва тегу")
    slug = models.SlugField(max_length=50, unique=True, verbose_name="URL")
    
    class Meta:
        verbose_name = "Тег"
        verbose_name_plural = "Теги"
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('tag_detail', kwargs={'slug': self.slug})


class Post(models.Model):
    """Модель посту"""
    POST_TYPE_CHOICES = [
        ('article', 'Стаття'),
        ('news', 'Новина'),
        ('tutorial', 'Туторіал'),
        ('review', 'Огляд'),
    ]
    
    STATUS_CHOICES = [
        ('draft', 'Чернетка'),
        ('published', 'Опублікована'),
        ('archived', 'В архіві'),
    ]
    
    title = models.CharField(max_length=200, verbose_name="Заголовок")
    slug = models.SlugField(max_length=200, unique=True, verbose_name="URL")
    content = models.TextField(verbose_name="Зміст")
    excerpt = models.TextField(max_length=300, blank=True, verbose_name="Короткий опис")
    
    post_type = models.CharField(
        max_length=10,
        choices=POST_TYPE_CHOICES,
        default='article',
        verbose_name="Тип посту"
    )
    
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name="Автор"
    )
    
    category = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name="Категорія")
    tags = models.ManyToManyField(Tag, blank=True, verbose_name="Теги")
    
    status = models.CharField(
        max_length=10, 
        choices=STATUS_CHOICES, 
        default='draft',
        verbose_name="Статус"
    )
    
    featured_image = models.ImageField(
        upload_to='posts/%Y/%m/%d/', 
        blank=True, 
        verbose_name="Головне зображення"
    )
    
    meta_title = models.CharField(max_length=200, blank=True, verbose_name="Мета-заголовок")
    meta_description = models.TextField(max_length=300, blank=True, verbose_name="Мета-опис")
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Створено")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Оновлено")
    published_at = models.DateTimeField(
        null=True, 
        blank=True, 
        verbose_name="Дата публікації"
    )
    
    view_count = models.PositiveIntegerField(default=0, verbose_name="Перегляди")
    
    # --- ОНОВЛЕНО: 'like_count' замінено на 'vote_score' ---
    vote_score = models.IntegerField(default=0, verbose_name="Рахунок голосів")
    
    share_count = models.PositiveIntegerField(default=0, verbose_name="Поділіться")
    
    is_featured = models.BooleanField(default=False, verbose_name="В обраному")
    is_pinned = models.BooleanField(default=False, verbose_name="Закріплений")
    allow_comments = models.BooleanField(default=True, verbose_name="Дозволити коментарі")
    
    # --- ДОДАНО ПОЛЕ ВІДЕО ---
    video_url = models.URLField(blank=True, null=True, verbose_name="Посилання на відео (YouTube, etc.)")
    
    bookmarked_by = models.ManyToManyField(
        settings.AUTH_USER_MODEL, 
        related_name='bookmarked_posts', 
        blank=True, 
        verbose_name="Збережено користувачами"
    )
    
    class Meta:
        verbose_name = "Пост"
        verbose_name_plural = "Пости"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['slug', 'status']),
            models.Index(fields=['category', 'status']),
            models.Index(fields=['post_type', 'status']),
            models.Index(fields=['is_featured', 'status']),
        ]
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1
            while Post.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        
        if not self.meta_title:
            self.meta_title = self.title
        if not self.meta_description and self.excerpt:
            self.meta_description = self.excerpt[:300]
        
        if self.status == 'published' and not self.published_at:
            self.published_at = timezone.now()
        
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('core:post_detail', kwargs={'slug': self.slug})
    
    def get_meta_title(self):
        return self.meta_title or self.title
    
    def get_meta_description(self):
        return self.meta_description or self.excerpt or self.content[:300]
    
    def increment_view_count(self):
        """Збільшення лічильника переглядів"""
        self.view_count += 1
        self.save(update_fields=['view_count'])
    
    def increment_share_count(self):
        """Збільшення лічильника поділів"""
        self.share_count += 1
        self.save(update_fields=['share_count'])
    
    @property
    def reading_time(self):
        """Розрахунок часу читання посту"""
        words_per_minute = 200
        word_count = len(self.content.split())
        return max(1, round(word_count / words_per_minute))
    
    @classmethod
    def get_published_posts(cls):
        """Отримання опублікованих постів"""
        return cls.objects.filter(status='published')
    
    @classmethod
    def get_featured_posts(cls):
        """Отримання обраних постів"""
        return cls.get_published_posts().filter(is_featured=True)
    
    @classmethod
    def get_posts_by_category(cls, category_slug):
        """Отримання постів за категорією"""
        return cls.get_published_posts().filter(category__slug=category_slug)
    
    @classmethod
    def get_posts_by_tag(cls, tag_slug):
        """Отримання постів за тегом"""
        return cls.get_published_posts().filter(tags__slug=tag_slug)


class PostComment(models.Model):
    """Модель коментаря до посту"""
    post = models.ForeignKey(
        Post, 
        on_delete=models.CASCADE, 
        related_name='comments',
        verbose_name="Пост"
    )
    
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name="Автор"
    )
    
    content = models.TextField(verbose_name="Коментар")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Створено")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Оновлено")
    is_active = models.BooleanField(default=True, verbose_name="Активний")
    
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='replies',
        verbose_name="Відповідь на"
    )
    
    like_count = models.PositiveIntegerField(default=0, verbose_name="Лайки")
    
    class Meta:
        verbose_name = "Коментар до посту"
        verbose_name_plural = "Коментарі до постів"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Коментар від {self.author} до {self.post}"
    
    @property
    def is_reply(self):
        """Чи є коментар відповіддю"""
        return self.parent is not None


# --- ОНОВЛЕНО: 'PostLike' перейменовано на 'PostVote' і додано 'value' ---
class PostVote(models.Model):
    """Модель голосу (вгору/вниз) для посту"""
    post = models.ForeignKey(
        Post, 
        on_delete=models.CASCADE, 
        related_name='votes', # 'likes' змінено на 'votes'
        verbose_name="Пост"
    )
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name="Користувач"
    )
    
    # 1 для лайка, -1 для дизлайка
    value = models.SmallIntegerField(verbose_name="Значення")
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Створено")
    
    class Meta:
        verbose_name = "Голос за пост"
        verbose_name_plural = "Голоси за пости"
        unique_together = ['post', 'user'] # Залишається
    
    def __str__(self):
        return f"Голос {self.value} від {self.user} для {self.post}"


class CommentLike(models.Model):
    """Модель лайку для коментаря"""
    comment = models.ForeignKey(
        PostComment, 
        on_delete=models.CASCADE, 
        related_name='likes',
        verbose_name="Коментар"
    )
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name="Користувач"
    )
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Створено")
    
    class Meta:
        verbose_name = "Лайк коментаря"
        verbose_name_plural = "Лайки коментарів"
        unique_together = ['comment', 'user']
    
    def __str__(self):
        return f"Лайк від {self.user} для {self.comment_id}"


class Subscription(models.Model):
    """Модель підписки на новини"""
    email = models.EmailField(unique=True, verbose_name="Email")
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        verbose_name="Користувач"
    )
    
    is_active = models.BooleanField(default=True, verbose_name="Активна")
    subscribed_at = models.DateTimeField(auto_now_add=True, verbose_name="Підписано")
    
    class Meta:
        verbose_name = "Підписка"
        verbose_name_plural = "Підписки"
    
    def __str__(self):
        return self.email


class Advertisement(models.Model):
    """Модель оголошення"""
    title = models.CharField(max_length=200, verbose_name="Заголовок")
    slug = models.SlugField(max_length=200, unique=True, verbose_name="URL")
    content = models.TextField(verbose_name="Зміст")
    image = models.ImageField(
        upload_to='ads/%Y/%m/%d/', 
        blank=True, 
        verbose_name="Зображення"
    )
    link = models.URLField(blank=True, verbose_name="Посилання")
    is_active = models.BooleanField(default=True, verbose_name="Активне")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Створено")
    expires_at = models.DateTimeField(verbose_name="Дійсне до")
    
    class Meta:
        verbose_name = "Оголошення"
        verbose_name_plural = "Оголошення"
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)
    
    def is_valid(self):
        return self.is_active and timezone.now() < self.expires_at