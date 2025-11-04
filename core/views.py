from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse_lazy
from django.db.models import Q, Count, Exists, OuterRef
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.utils import timezone
# --- ОНОВЛЕНО: Додано CommentLike ---
from .models import Post, Category, Tag, PostComment, PostLike, Subscription, CommentLike
from .forms import PostForm, CommentForm, SubscriptionForm
from django.contrib.auth import get_user_model

User = get_user_model()


class PostListView(ListView):
    """Список всіх опублікованих постів"""
    model = Post
    template_name = 'core/post_list.html'
    context_object_name = 'posts'
    paginate_by = 10
    
    def get_queryset(self):
        queryset = Post.objects.filter(status='published').select_related(
            'author', 'category'
        ).prefetch_related('tags')
        
        # --- ОНОВЛЕНО: Додано анотацію для закладок ---
        if self.request.user.is_authenticated:
            bookmarked_subquery = Exists(
                self.request.user.bookmarked_posts.filter(pk=OuterRef('pk'))
            )
            queryset = queryset.annotate(is_bookmarked=bookmarked_subquery)
        
        category_slug = self.kwargs.get('category_slug')
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)
        
        tag_slug = self.kwargs.get('tag_slug')
        if tag_slug:
            queryset = queryset.filter(tags__slug=tag_slug)
        
        search_query = self.request.GET.get('q')
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) |
                Q(content__icontains=search_query) |
                Q(excerpt__icontains=search_query)
            )
        
        # --- ОНОВЛЕНО: Додано логіку сортування за закладками ---
        sort = self.request.GET.get('sort', 'newest')
        if sort == 'popular':
            queryset = queryset.order_by('-view_count')
        elif sort == 'featured':
            queryset = queryset.filter(is_featured=True).order_by('-created_at')
        elif sort == 'bookmarked' and self.request.user.is_authenticated:
            queryset = queryset.filter(bookmarked_by=self.request.user).order_by('-created_at')
        else:
            queryset = queryset.order_by('-created_at')
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        context['popular_tags'] = Tag.objects.annotate(
            post_count=Count('post')
        ).order_by('-post_count')[:10]
        context['featured_posts'] = Post.get_featured_posts()[:5]
        return context


class PostDetailView(DetailView):
    """Детальний перегляд посту"""
    model = Post
    template_name = 'core/post_detail.html'
    context_object_name = 'post'
    
    def get_queryset(self):
        return Post.objects.filter(
            Q(status='published') | 
            Q(author=self.request.user) if self.request.user.is_authenticated else Q(status='published')
        ).select_related('author', 'category').prefetch_related('tags', 'comments', 'comments__author', 'bookmarked_by')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        post = self.get_object()
        
        if post.status == 'published':
            post.increment_view_count()
        
        # --- ОНОВЛЕНО: Оптимізовано для вкладених коментарів ---
        comments = post.comments.filter(is_active=True, parent=None).select_related('author')
        context['comments'] = comments
        context['comment_form'] = CommentForm()
        context['comment_count'] = post.comments.filter(is_active=True).count()
        
        # --- ОНОВЛЕНО: Додано перевірку закладок ---
        if self.request.user.is_authenticated:
            context['user_liked'] = PostLike.objects.filter(
                post=post, user=self.request.user
            ).exists()
            context['user_bookmarked'] = post.bookmarked_by.filter(id=self.request.user.id).exists()
        else:
            context['user_liked'] = False
            context['user_bookmarked'] = False
        
        context['related_posts'] = Post.get_published_posts().filter(
            category=post.category
        ).exclude(id=post.id)[:3]
        
        return context


class PostCreateView(LoginRequiredMixin, CreateView):
    """Створення нового посту"""
    model = Post
    form_class = PostForm
    template_name = 'core/post_form.html'
    
    def form_valid(self, form):
        form.instance.author = self.request.user
        messages.success(self.request, 'Пост успішно створено!')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('core:post_detail', kwargs={'slug': self.object.slug})


class PostUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Редагування посту"""
    model = Post
    form_class = PostForm
    template_name = 'core/post_form.html'
    
    def form_valid(self, form):
        messages.success(self.request, 'Пост успішно оновлено!')
        return super().form_valid(form)
    
    def test_func(self):
        post = self.get_object()
        return self.request.user == post.author or self.request.user.is_staff
    
    def get_success_url(self):
        return reverse_lazy('core:post_detail', kwargs={'slug': self.object.slug})  # Додано core:


class PostDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """Видалення посту"""
    model = Post
    template_name = 'core/post_confirm_delete.html'
    success_url = reverse_lazy('post_list')
    
    def test_func(self):
        post = self.get_object()
        return self.request.user == post.author or self.request.user.is_staff
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Пост успішно видалено!')
        return super().delete(request, *args, **kwargs)


class UserPostListView(ListView):
    """Список постів конкретного автора"""
    model = Post
    template_name = 'core/user_posts.html'
    context_object_name = 'posts'
    paginate_by = 10
    
    def get_queryset(self):
        username = self.kwargs.get('username')
        return Post.objects.filter(
            author__username=username, 
            status='published'
        ).order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['author'] = get_object_or_404(User, username=self.kwargs.get('username'))
        return context


class CategoryListView(ListView):
    """Список всіх категорій"""
    model = Category
    template_name = 'core/category_list.html'
    context_object_name = 'categories'
    
    def get_queryset(self):
        return Category.objects.annotate(
            post_count=Count('post')
        ).order_by('name')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        categories = self.get_queryset()
        
        # Статистика
        total_posts = sum(category.post_count for category in categories)
        avg_posts_per_category = round(total_posts / len(categories)) if categories else 0
        most_popular_category = categories.order_by('-post_count').first() if categories else None
        popular_categories = categories.order_by('-post_count')[:5]
        
        context.update({
            'total_posts': total_posts,
            'avg_posts_per_category': avg_posts_per_category,
            'most_popular_category': most_popular_category,
            'popular_categories': popular_categories,
        })
        return context


class CategoryDetailView(DetailView):
    """Детальний перегляд категорії з постами"""
    model = Category
    template_name = 'core/category_detail.html'
    context_object_name = 'category'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        category = self.get_object()
        
        posts = Post.get_published_posts().filter(category=category)
        
        # --- ОНОВЛЕНО: Додано анотацію для закладок ---
        if self.request.user.is_authenticated:
            bookmarked_subquery = Exists(
                self.request.user.bookmarked_posts.filter(pk=OuterRef('pk'))
            )
            posts = posts.annotate(is_bookmarked=bookmarked_subquery)
        
        paginator = Paginator(posts, 10)
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        context['posts'] = page_obj
        context['post_count'] = posts.count()
        context['categories'] = Category.objects.annotate(post_count=Count('post'))
        return context


class CategoryCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """Створення нової категорії"""
    model = Category
    fields = ['name', 'description']
    template_name = 'core/category_form.html'
    success_url = reverse_lazy('category_list')
    
    def test_func(self):
        return self.request.user.is_admin
    
    def form_valid(self, form):
        messages.success(self.request, 'Категорію успішно створено!')
        return super().form_valid(form)


class CategoryUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Редагування категорії"""
    model = Category
    fields = ['name', 'description']
    template_name = 'core/category_form.html'
    success_url = reverse_lazy('category_list')
    
    def test_func(self):
        return self.request.user.is_admin
    
    def form_valid(self, form):
        messages.success(self.request, 'Категорію успішно оновлено!')
        return super().form_valid(form)


class CategoryDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """Видалення категорії"""
    model = Category
    template_name = 'core/category_confirm_delete.html'
    success_url = reverse_lazy('category_list')
    
    def test_func(self):
        return self.request.user.is_admin
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Категорію успішно видалено!')
        return super().delete(request, *args, **kwargs)


class TagListView(ListView):
    """Список всіх тегів"""
    model = Tag
    template_name = 'core/tag_list.html'
    context_object_name = 'tags'
    
    def get_queryset(self):
        return Tag.objects.annotate(
            post_count=Count('post')
        ).order_by('name')


class TagDetailView(DetailView):
    """Детальний перегляд тегу з постами"""
    model = Tag
    template_name = 'core/tag_detail.html'
    context_object_name = 'tag'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tag = self.get_object()
        
        posts = Post.get_published_posts().filter(tags=tag)
        
        paginator = Paginator(posts, 10)
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        context['posts'] = page_obj
        context['post_count'] = posts.count()
        return context


@login_required
def add_comment(request, slug):
    """Додавання коментаря до посту"""
    post = get_object_or_404(Post, slug=slug, status='published')
    
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.author = request.user
            comment.save()
            messages.success(request, 'Коментар успішно додано!')
    
    return redirect('core:post_detail', slug=slug)

@login_required
def delete_comment(request, pk):
    """Видалення коментаря"""
    comment = get_object_or_404(PostComment, pk=pk)
    
    if request.user == comment.author or request.user == comment.post.author or request.user.is_staff:
        comment.delete()
        messages.success(request, 'Коментар успішно видалено!')
    else:
        messages.error(request, 'У вас немає прав для видалення цього коментаря!')
    
    # --- ОНОВЛЕНО: Виправлено NoReverseMatch ---
    return redirect('core:post_detail', slug=comment.post.slug)


@login_required
def toggle_like(request, slug):
    """Додавання/видалення лайку"""
    post = get_object_or_404(Post, slug=slug, status='published')
    
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        like, created = PostLike.objects.get_or_create(post=post, user=request.user)
        
        if not created:
            like.delete()
            liked = False
            post.like_count = max(0, post.like_count - 1)
        else:
            liked = True
            post.like_count += 1
        
        post.save(update_fields=['like_count'])
        
        return JsonResponse({
            'liked': liked,
            'like_count': post.like_count
        })
    
    return redirect('core:post_detail', slug=slug) # --- Оновлено: додано 'core:' ---


# --- ДОДАНО: Нова функція для лайків коментарів ---
@login_required
def toggle_comment_like(request, pk):
    """Додавання/видалення лайку для коментаря (AJAX)"""
    # Знаходимо коментар за його ID (pk)
    comment = get_object_or_404(PostComment, pk=pk)
    
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        # Спробуємо знайти лайк, або створити його
        like, created = CommentLike.objects.get_or_create(comment=comment, user=request.user)
        
        if not created:
            # Якщо лайк вже існував (created == False), ми його видаляємо
            like.delete()
            liked = False
            comment.like_count = max(0, comment.like_count - 1)
        else:
            # Якщо лайк був щойно створений (created == True)
            liked = True
            comment.like_count += 1
        
        # Зберігаємо оновлену кількість лайків у моделі коментаря
        comment.save(update_fields=['like_count'])
        
        return JsonResponse({
            'liked': liked,
            'like_count': comment.like_count
        })
    
    # Якщо це не AJAX, просто перенаправляємо на пост
    return redirect('core:post_detail', slug=comment.post.slug)


# --- ДОДАНО НОВУ ФУНКЦІЮ ---
@login_required
def toggle_bookmark(request, slug):
    """Додавання/видалення посту з закладок"""
    post = get_object_or_404(Post, slug=slug, status='published')
    
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        user = request.user
        bookmarked = False
        if post.bookmarked_by.filter(id=user.id).exists():
            # Видалити з закладок
            post.bookmarked_by.remove(user)
            bookmarked = False
        else:
            # Додати в закладки
            post.bookmarked_by.add(user)
            bookmarked = True
        
        return JsonResponse({
            'bookmarked': bookmarked,
        })
    
    return redirect('core:post_detail', slug=slug) # Fallback


def subscribe(request):
    """Підписка на розсилку"""
    if request.method == 'POST':
        form = SubscriptionForm(request.POST)
        if form.is_valid():
            subscription, created = Subscription.objects.get_or_create(
                email=form.cleaned_data['email'],
                defaults={'is_active': True}
            )
            
            if created:
                messages.success(request, 'Ви успішно підписались на розсилку!')
            else:
                if not subscription.is_active:
                    subscription.is_active = True
                    subscription.save()
                    messages.success(request, 'Вашу підписку відновлено!')
                else:
                    messages.info(request, 'Ви вже підписані на нашу розсилку!')
            
            return redirect('post_list')
    else:
        form = SubscriptionForm()
    
    return render(request, 'core/subscribe.html', {'form': form})


def unsubscribe(request, email):
    """Відписка від розсилки"""
    subscription = get_object_or_404(Subscription, email=email)
    subscription.is_active = False
    subscription.save()
    messages.success(request, 'Ви успішно відписались від розсилки.')
    return redirect('post_list')


def home(request):
    """Головна сторінка блогу"""
    latest_posts = Post.get_published_posts().select_related(
        'author', 'category'
    ).prefetch_related('tags')[:6]
    
    # --- ОНОВЛЕНО: Додано анотацію для закладок ---
    if request.user.is_authenticated:
        bookmarked_subquery = Exists(
            request.user.bookmarked_posts.filter(pk=OuterRef('pk'))
        )
        latest_posts = latest_posts.annotate(is_bookmarked=bookmarked_subquery)
    
    featured_posts = Post.get_featured_posts()[:3]
    popular_posts = Post.get_published_posts().order_by('-view_count')[:5]
    
    categories = Category.objects.annotate(
        post_count=Count('post')
    ).order_by('-post_count')[:8]
    
    context = {
        'latest_posts': latest_posts,
        'featured_posts': featured_posts,
        'popular_posts': popular_posts,
        'categories': categories,
    }
    
    return render(request, 'core/home.html', context)


def api_posts(request):
    """API для отримання постів (для AJAX)"""
    posts = Post.get_published_posts().values(
        'id', 'title', 'slug', 'excerpt', 'created_at', 'view_count', 'author__username'
    )[:10]
    
    return JsonResponse(list(posts), safe=False)


def api_post_detail(request, slug):
    """API для отримання деталей посту"""
    post = get_object_or_404(Post, slug=slug, status='published')
    
    data = {
        'id': post.id,
        'title': post.title,
        'content': post.content,
        'author': post.author.username,
        'created_at': post.created_at.isoformat(),
        'view_count': post.view_count,
        'like_count': post.like_count,
        'reading_time': post.reading_time,
    }
    
    return JsonResponse(data)


def search(request):
    """Сторінка пошуку"""
    query = request.GET.get('q', '')
    posts = []
    
    if query:
        posts = Post.get_published_posts().filter(
            Q(title__icontains=query) |
            Q(content__icontains=query) |
            Q(excerpt__icontains=query) |
            Q(tags__name__icontains=query)
        ).distinct().order_by('-created_at')
        
        if request.user.is_authenticated:
            bookmarked_subquery = Exists(
                request.user.bookmarked_posts.filter(pk=OuterRef('pk'))
            )
            posts = posts.annotate(is_bookmarked=bookmarked_subquery)
    
    context = {
        'query': query,
        'posts': posts,
        'results_count': len(posts),
    }
    
    return render(request, 'core/search.html', context)