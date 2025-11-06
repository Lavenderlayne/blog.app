from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse_lazy
from django.db.models import Q, Count, Exists, OuterRef, Sum, Subquery, Value, IntegerField
from django.http import JsonResponse, HttpResponseBadRequest
from django.core.paginator import Paginator
from django.utils import timezone
from .models import Post, Category, Tag, PostComment, PostVote, Subscription, CommentLike, Advertisement
# --- ОНОВЛЕНО: Додано TagForm та slugify ---
from .forms import PostForm, CommentForm, SubscriptionForm, TagForm
from django.utils.text import slugify
# ---
from django.contrib.auth import get_user_model

User = get_user_model()


def annotate_post_queryset(queryset, user):
    """Додає анотації is_bookmarked та user_vote до queryset"""
    if user.is_authenticated:
        bookmarked_subquery = Exists(
            user.bookmarked_posts.filter(pk=OuterRef('pk'))
        )
        vote_subquery = Subquery(
            PostVote.objects.filter(
                post=OuterRef('pk'), 
                user=user
            ).values('value')[:1],
            output_field=IntegerField() 
        )
        return queryset.annotate(
            is_bookmarked=bookmarked_subquery,
            user_vote=vote_subquery
        )
    
    return queryset.annotate(
        is_bookmarked=Value(False),
        user_vote=Value(0, output_field=IntegerField())
    )


# --- ЛОГІКА ОБРОБКИ ТЕГІВ ---
def handle_tags(post_object, tag_string):
    """Допоміжна функція для очищення та додавання тегів до посту."""
    post_object.tags.clear()
    tag_names = [name.strip() for name in tag_string.split(',') if name.strip()]
    for name in tag_names:
        # Використовуємо iexact для уникнення дублікатів (Python, python)
        # Створюємо слаг під час створення
        tag, created = Tag.objects.get_or_create(
            name__iexact=name, 
            defaults={'name': name, 'slug': slugify(name)}
        )
        post_object.tags.add(tag)
# --- КІНЕЦЬ ---


class PostListView(ListView):
    model = Post
    template_name = 'core/post_list.html'
    context_object_name = 'posts'
    paginate_by = 10
    
    def get_queryset(self):
        queryset = Post.objects.filter(status='published').select_related(
            'author', 'category'
        ).prefetch_related('tags', 'votes')
        
        queryset = annotate_post_queryset(queryset, self.request.user)
        
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
        
        sort = self.request.GET.get('sort', 'newest')
        if sort == 'popular':
            queryset = queryset.order_by('-view_count')
        elif sort == 'top': 
            queryset = queryset.order_by('-vote_score')
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
        context['active_ads'] = Advertisement.objects.filter(
            is_active=True, 
            expires_at__gte=timezone.now()
        ).order_by('?')[:2]
        return context


class PostDetailView(DetailView):
    model = Post
    template_name = 'core/post_detail.html'
    context_object_name = 'post'
    
    def get_queryset(self):
        return Post.objects.filter(
            Q(status='published') | 
            Q(author=self.request.user) if self.request.user.is_authenticated else Q(status='published')
        ).select_related('author', 'category').prefetch_related('tags', 'comments', 'comments__author', 'bookmarked_by', 'votes')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        post = self.get_object()
        
        if post.status == 'published':
            post.increment_view_count()
        
        comments = post.comments.filter(is_active=True, parent=None).select_related('author')
        context['comments'] = comments
        context['comment_form'] = CommentForm()
        context['comment_count'] = post.comments.filter(is_active=True).count()
        
        user_vote = 0
        if self.request.user.is_authenticated:
            vote_obj = post.votes.filter(user=self.request.user).first()
            if vote_obj:
                user_vote = vote_obj.value
            context['user_bookmarked'] = post.bookmarked_by.filter(id=self.request.user.id).exists()
        else:
            context['user_bookmarked'] = False
        
        context['user_vote'] = user_vote
        
        context['related_posts'] = Post.get_published_posts().filter(
            category=post.category
        ).exclude(id=post.id)[:3]
        
        context['active_ads'] = Advertisement.objects.filter(
            is_active=True, 
            expires_at__gte=timezone.now()
        ).order_by('?')[:2]
        
        return context


class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    form_class = PostForm
    template_name = 'core/post_form.html'
    
    # --- ОНОВЛЕНО: Додано form_valid для обробки тегів ---
    def form_valid(self, form):
        form.instance.author = self.request.user
        # Зберігаємо пост, щоб отримати ID
        self.object = form.save() 
        
        # Отримуємо рядок тегів з форми
        tag_string = form.cleaned_data.get('tags', '')
        handle_tags(self.object, tag_string)
        
        messages.success(self.request, 'Пост успішно створено!')
        return redirect(self.get_success_url()) # Викликаємо redirect замість super().form_valid

    def get_success_url(self):
        return reverse_lazy('core:post_detail', kwargs={'slug': self.object.slug})


class PostUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Post
    form_class = PostForm
    template_name = 'core/post_form.html'
    
    # --- ДОДАНО: Заповнюємо поле тегів початковими даними ---
    def get_initial(self):
        initial = super().get_initial()
        if self.object.tags.exists():
            initial['tags'] = ', '.join(tag.name for tag in self.object.tags.all())
        return initial
    
    # --- ОНОВЛЕНО: Додано form_valid для обробки тегів ---
    def form_valid(self, form):
        # Зберігаємо пост
        self.object = form.save() 
        
        # Отримуємо рядок тегів з форми
        tag_string = form.cleaned_data.get('tags', '')
        handle_tags(self.object, tag_string)
        
        messages.success(self.request, 'Пост успішно оновлено!')
        return redirect(self.get_success_url()) # Викликаємо redirect замість super().form_valid
    
    def test_func(self):
        post = self.get_object()
        return self.request.user == post.author or self.request.user.is_staff
    
    def get_success_url(self):
        return reverse_lazy('core:post_detail', kwargs={'slug': self.object.slug})


class PostDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
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
    model = Post
    template_name = 'core/user_posts.html'
    context_object_name = 'posts'
    paginate_by = 10
    
    def get_queryset(self):
        username = self.kwargs.get('username')
        queryset = Post.objects.filter(
            author__username=username, 
            status='published'
        ).order_by('-created_at')
        queryset = annotate_post_queryset(queryset, self.request.user)
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['author'] = get_object_or_404(User, username=self.kwargs.get('username'))
        return context


class CategoryListView(ListView):
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
    model = Category
    template_name = 'core/category_detail.html'
    context_object_name = 'category'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        category = self.get_object()
        posts_qs = Post.get_published_posts().filter(category=category)
        posts = annotate_post_queryset(posts_qs, self.request.user)
        
        one_month_ago = timezone.now() - timezone.timedelta(days=30)
        context['active_users'] = User.objects.filter(is_active=True).count()
        context['monthly_posts'] = posts.filter(created_at__gte=one_month_ago).count()
        context['total_views'] = posts.aggregate(total=Sum('view_count'))['total'] or 0
        
        paginator = Paginator(posts, 10)
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        context['posts'] = page_obj
        context['post_count'] = posts_qs.count()
        context['categories'] = Category.objects.annotate(post_count=Count('post'))
        return context


class CategoryCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Category
    fields = ['name', 'description']
    template_name = 'core/category_form.html' # Будемо використовувати спільний шаблон
    success_url = reverse_lazy('core:category_list')
    def test_func(self): return self.request.user.is_admin
    def form_valid(self, form):
        messages.success(self.request, 'Спільноту успішно створено!')
        return super().form_valid(form)


class CategoryUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Category
    fields = ['name', 'description']
    template_name = 'core/category_form.html'
    success_url = reverse_lazy('core:category_list')
    def test_func(self): return self.request.user.is_admin
    def form_valid(self, form):
        messages.success(self.request, 'Спільноту успішно оновлено!')
        return super().form_valid(form)


class CategoryDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Category
    template_name = 'core/category_confirm_delete.html' # Спільний шаблон
    success_url = reverse_lazy('core:category_list')
    def test_func(self): return self.request.user.is_admin
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Спільноту успішно видалено!')
        return super().delete(request, *args, **kwargs)


class TagListView(ListView):
    model = Tag
    template_name = 'core/tag_list.html'
    context_object_name = 'tags'
    
    def get_queryset(self):
        return Tag.objects.annotate(
            post_count=Count('post')
        ).order_by('name')


class TagDetailView(DetailView):
    model = Tag
    template_name = 'core/tag_detail.html'
    context_object_name = 'tag'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tag = self.get_object()
        
        posts_qs = Post.get_published_posts().filter(tags=tag)
        posts = annotate_post_queryset(posts_qs, self.request.user)
        
        paginator = Paginator(posts, 10)
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        context['posts'] = page_obj
        context['post_count'] = posts_qs.count()
        return context

# ---
# --- ДОДАНО НОВІ VIEWS ДЛЯ КЕРУВАННЯ ТЕГАМИ (ДЛЯ АДМІНІВ) ---
# ---
class TagCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Tag
    form_class = TagForm
    template_name = 'core/tag_form.html'
    success_url = reverse_lazy('core:tag_list')
    
    def test_func(self):
        return self.request.user.is_admin
        
    def form_valid(self, form):
        messages.success(self.request, 'Тег успішно створено!')
        return super().form_valid(form)

class TagUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Tag
    form_class = TagForm
    template_name = 'core/tag_form.html'
    success_url = reverse_lazy('core:tag_list')
    
    def test_func(self):
        return self.request.user.is_admin
        
    def form_valid(self, form):
        messages.success(self.request, 'Тег успішно оновлено!')
        return super().form_valid(form)

class TagDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Tag
    template_name = 'core/tag_confirm_delete.html'
    success_url = reverse_lazy('core:tag_list')
    
    def test_func(self):
        return self.request.user.is_admin
        
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Тег успішно видалено!')
        return super().delete(request, *args, **kwargs)
# --- КІНЕЦЬ НОВИХ VIEWS ---


@login_required
def add_comment(request, slug):
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
    comment = get_object_or_404(PostComment, pk=pk)
    if request.user == comment.author or request.user == comment.post.author or request.user.is_staff:
        comment.delete()
        messages.success(request, 'Коментар успішно видалено!')
    else:
        messages.error(request, 'У вас немає прав для видалення цього коментаря!')
    return redirect('core:post_detail', slug=comment.post.slug)


@login_required
def post_vote(request, slug, direction):
    if request.method != 'POST' or request.headers.get('x-requested-with') != 'XMLHttpRequest':
        return HttpResponseBadRequest("Invalid request")

    post = get_object_or_404(Post, slug=slug, status='published')
    user = request.user
    
    new_vote_value = 1 if direction == 'up' else -1
    
    try:
        vote = PostVote.objects.get(post=post, user=user)
        if vote.value == new_vote_value:
            vote.delete()
            user_vote_status = 0
        else:
            vote.value = new_vote_value
            vote.save()
            user_vote_status = new_vote_value
    except PostVote.DoesNotExist:
        PostVote.objects.create(post=post, user=user, value=new_vote_value)
        user_vote_status = new_vote_value
    
    new_score_data = post.votes.aggregate(score=Sum('value'))
    new_score = new_score_data.get('score') or 0
    
    post.vote_score = new_score
    post.save(update_fields=['vote_score'])
    
    return JsonResponse({
        'vote_score': new_score,
        'user_vote': user_vote_status
    })

@login_required
def toggle_comment_like(request, pk):
    comment = get_object_or_404(PostComment, pk=pk)
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        like, created = CommentLike.objects.get_or_create(comment=comment, user=request.user)
        
        if not created:
            like.delete()
            liked = False
            comment.like_count = max(0, comment.like_count - 1)
        else:
            liked = True
            comment.like_count += 1
        
        comment.save(update_fields=['like_count'])
        
        return JsonResponse({
            'liked': liked,
            'like_count': comment.like_count
        })
    return redirect('core:post_detail', slug=comment.post.slug)


@login_required
def toggle_bookmark(request, slug):
    post = get_object_or_404(Post, slug=slug, status='published')
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        user = request.user
        bookmarked = False
        if post.bookmarked_by.filter(id=user.id).exists():
            post.bookmarked_by.remove(user)
            bookmarked = False
        else:
            post.bookmarked_by.add(user)
            bookmarked = True
        return JsonResponse({'bookmarked': bookmarked})
    return redirect('core:post_detail', slug=slug)


def subscribe(request):
    if request.method == 'POST':
        form = SubscriptionForm(request.POST)
        if form.is_valid():
            subscription, created = Subscription.objects.get_or_create(
                email=form.cleaned_data['email'],
                defaults={'is_active': True}
            )
            if created: messages.success(request, 'Ви успішно підписались на розсилку!')
            else:
                if not subscription.is_active:
                    subscription.is_active = True
                    subscription.save()
                    messages.success(request, 'Вашу підписку відновлено!')
                else: messages.info(request, 'Ви вже підписані на нашу розсилку!')
            return redirect('core:post_list') # Змінено з post_list
    else: form = SubscriptionForm()
    return render(request, 'core/subscribe.html', {'form': form})


def unsubscribe(request, email):
    subscription = get_object_or_404(Subscription, email=email)
    subscription.is_active = False
    subscription.save()
    messages.success(request, 'Ви успішно відписались від розсилки.')
    return redirect('core:post_list') # Змінено з post_list


def home(request):
    latest_posts_qs = Post.get_published_posts().select_related(
        'author', 'category'
    ).prefetch_related('tags')[:6]
    latest_posts = annotate_post_queryset(latest_posts_qs, request.user)
    
    featured_posts = Post.get_featured_posts()[:3]
    popular_posts = Post.get_published_posts().order_by('-view_count')[:5]
    
    categories = Category.objects.annotate(
        post_count=Count('post')
    ).order_by('-post_count')[:8]
    
    total_posts = Post.get_published_posts().count()
    total_categories = Category.objects.count()
    total_users = User.objects.count()
    active_users = User.objects.filter(is_active=True).count()
    
    active_ads = Advertisement.objects.filter(
        is_active=True, 
        expires_at__gte=timezone.now()
    ).order_by('?')[:2]

    context = {
        'latest_posts': latest_posts,
        'featured_posts': featured_posts,
        'popular_posts': popular_posts,
        'categories': categories,
        'total_posts': total_posts,
        'total_categories': total_categories,
        'total_users': total_users,
        'active_users': active_users,
        'active_ads': active_ads,
    }
    return render(request, 'core/home.html', context)


def api_posts(request):
    posts = Post.get_published_posts().values(
        'id', 'title', 'slug', 'excerpt', 'created_at', 'view_count', 'author__username'
    )[:10]
    return JsonResponse(list(posts), safe=False)


def api_post_detail(request, slug):
    post = get_object_or_404(Post, slug=slug, status='published')
    data = {
        'id': post.id,
        'title': post.title,
        'content': post.content,
        'author': post.author.username,
        'created_at': post.created_at.isoformat(),
        'view_count': post.view_count,
        'like_count': post.vote_score,
        'reading_time': post.reading_time,
    }
    return JsonResponse(data)


def search(request):
    query = request.GET.get('q', '')
    posts = []
    
    if query:
        posts_qs = Post.get_published_posts().filter(
            Q(title__icontains=query) |
            Q(content__icontains=query) |
            Q(excerpt__icontains=query) |
            Q(tags__name__icontains=query)
        ).distinct().order_by('-created_at')
        posts = annotate_post_queryset(posts_qs, request.user)
    
    popular_tags = Tag.objects.annotate(
        post_count=Count('post')
    ).order_by('-post_count')[:15]
    
    categories = Category.objects.annotate(
        post_count=Count('post')
    ).order_by('-post_count')[:10]
    
    context = {
        'query': query,
        'posts': posts,
        'results_count': len(posts),
        'popular_tags': popular_tags,
        'categories': categories,
    }
    return render(request, 'core/search.html', context)