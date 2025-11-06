from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import DetailView, UpdateView, ListView
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models import Q
from .models import CustomUser, Profile
from .forms import ProfileUpdateForm, UserUpdateForm, UserRegistrationForm
from django.contrib.auth.views import LoginView
from django.contrib.auth import login
from django.http import JsonResponse, HttpResponseBadRequest

# --- ДОДАНО ІМПОРТИ ДЛЯ ПОСТІВ, КОМЕНТАРІВ ТА ЧАСУ ---
from core.models import Post, PostComment
from django.utils import timezone
from datetime import timedelta
# ---

def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Реєстрація успішна! Ласкаво просимо!')
            return redirect('core:home')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'users/register.html', {'form': form})

class CustomLoginView(LoginView):
    template_name = 'users/login.html'
    redirect_authenticated_user = True
    
    def get_success_url(self):
        return reverse_lazy('core:home')

def is_moderator(user):
    return user.is_authenticated and (user.role == 'moderator' or user.is_superuser)

def is_admin(user):
    return user.is_authenticated and (user.role == 'admin' or user.is_superuser)

class ProfileDetailView(LoginRequiredMixin, DetailView):
    model = CustomUser
    template_name = 'users/profile_detail.html'
    context_object_name = 'profile_user'
    
    def get_object(self):
        user = get_object_or_404(CustomUser, username=self.kwargs['username'])
        if not hasattr(user, 'profile'):
            Profile.objects.create(user=user)
        return user
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile_user = self.get_object()
        request_user = self.request.user
        
        context['user_posts'] = Post.objects.filter(
            author=profile_user, status='published'
        ).order_by('-created_at')
        
        context['user_comments'] = PostComment.objects.filter(
            author=profile_user, is_active=True
        ).select_related('post').order_by('-created_at')[:15]
        
        if request_user == profile_user:
            context['bookmarked_posts'] = profile_user.bookmarked_posts.all().order_by('-created_at')

        context['post_count'] = context['user_posts'].count()
        context['comment_count'] = context['user_comments'].count()
        context['followers_count'] = profile_user.followers.count()
        context['following_count'] = profile_user.following.count()
        
        context['is_following'] = False
        if request_user.is_authenticated:
            context['is_following'] = profile_user.followers.filter(id=request_user.id).exists()
            
        return context

class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = Profile
    form_class = ProfileUpdateForm
    template_name = 'users/profile_form.html'
    
    def get_object(self):
        if not hasattr(self.request.user, 'profile'):
            Profile.objects.create(user=self.request.user)
        return self.request.user.profile
    
    def get_success_url(self):
        return reverse_lazy('users:profile_detail', kwargs={'username': self.request.user.username})
    
    def form_valid(self, form):
        messages.success(self.request, 'Профіль успішно оновлено!')
        return super().form_valid(form)

class UserUpdateView(LoginRequiredMixin, UpdateView):
    model = CustomUser
    form_class = UserUpdateForm
    template_name = 'users/user_form.html'
    
    def get_object(self):
        return self.request.user
    
    def get_success_url(self):
        return reverse_lazy('users:profile_detail', kwargs={'username': self.request.user.username})
    
    def form_valid(self, form):
        messages.success(self.request, 'Дані користувача успішно оновлено!')
        return super().form_valid(form)

class UserListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = CustomUser
    template_name = 'users/user_list.html'
    context_object_name = 'users'
    paginate_by = 20
    
    def test_func(self):
        return is_moderator(self.request.user)
    
    def get_queryset(self):
        return CustomUser.objects.all().order_by('-date_joined')

@login_required
@user_passes_test(is_admin)
def change_user_role(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    
    if request.method == 'POST':
        new_role = request.POST.get('role')
        if new_role in ['user', 'moderator', 'admin']:
            user.role = new_role
            user.save()
            messages.success(request, f'Роль користувача {user.username} змінено на {new_role}')
        else:
            messages.error(request, 'Невірна роль')
    
    return redirect('users:user_list')

@login_required
@user_passes_test(is_moderator)
def toggle_user_status(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    
    if request.method == 'POST':
        user.is_active = not user.is_active
        user.save()
        
        status = "активовано" if user.is_active else "заблоковано"
        messages.success(request, f'Користувача {user.username} {status}')
    
    return redirect('users:user_list')

@login_required
def my_profile(request):
    return redirect('users:profile_detail', username=request.user.username)

# ---
# --- ПОВНІСТЮ ЗАМІНІТЬ ЦЮ ФУНКЦІЮ ---
# ---
@login_required
@user_passes_test(is_admin)
def user_statistics(request):
    total_users = CustomUser.objects.count()
    active_users = CustomUser.objects.filter(is_active=True).count()
    moderators_count = CustomUser.objects.filter(role='moderator').count()
    admins_count = CustomUser.objects.filter(role='admin').count()
    
    recent_users = CustomUser.objects.order_by('-date_joined')[:10]
    
    # --- ДОДАНО ОБЧИСЛЕННЯ ---
    # 1. Обчислюємо реєстрації за останній місяць
    one_month_ago = timezone.now() - timedelta(days=30)
    monthly_registrations = CustomUser.objects.filter(date_joined__gte=one_month_ago).count()
    
    # 2. Обчислюємо відсоток активності (з перевіркою ділення на нуль)
    active_percentage = 0
    if total_users > 0:
        active_percentage = round((active_users / total_users) * 100)
    # --- КІНЕЦЬ ДОДАНОГО КОДУ ---
    
    context = {
        'total_users': total_users,
        'active_users': active_users,
        'moderators_count': moderators_count,
        'admins_count': admins_count,
        'recent_users': recent_users,
        
        # --- ДОДАНО ДО КОНТЕКСТУ ---
        'monthly_registrations': monthly_registrations,
        'active_percentage': active_percentage,
    }
    
    return render(request, 'users/statistics.html', context)
# ---
# --- КІНЕЦЬ ЗАМІНИ ---
# ---

class UserSearchView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = CustomUser
    template_name = 'users/user_search.html'
    context_object_name = 'users'
    paginate_by = 20
    
    def test_func(self):
        return is_moderator(self.request.user)
    
    def get_queryset(self):
        query = self.request.GET.get('q')
        if query:
            return CustomUser.objects.filter(
                Q(username__icontains=query) | 
                Q(email__icontains=query) |
                Q(first_name__icontains=query) |
                Q(last_name__icontains=query)
            ).order_by('username')
        return CustomUser.objects.none()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['query'] = self.request.GET.get('q', '')
        return context

@login_required
def toggle_follow(request, username):
    if request.method != 'POST' or request.headers.get('x-requested-with') != 'XMLHttpRequest':
        return HttpResponseBadRequest("Invalid request")

    user_to_follow = get_object_or_404(CustomUser, username=username)
    request_user = request.user

    if user_to_follow == request_user:
        return JsonResponse({'error': 'Ви не можете підписатись на себе'}, status=400)

    is_following = False
    if user_to_follow.followers.filter(id=request_user.id).exists():
        # Вже підписаний, відписуємось
        user_to_follow.followers.remove(request_user)
        is_following = False
    else:
        # Не підписаний, підписуємось
        user_to_follow.followers.add(request_user)
        is_following = True

    return JsonResponse({
        'is_following': is_following,
        'followers_count': user_to_follow.followers.count()
    })