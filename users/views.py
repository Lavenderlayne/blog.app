from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import DetailView, UpdateView, ListView
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models import Q
from .models import CustomUser, Profile
from .forms import ProfileUpdateForm, UserUpdateForm

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
    
    return redirect('user-list')

@login_required
@user_passes_test(is_moderator)
def toggle_user_status(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    
    if request.method == 'POST':
        user.is_active = not user.is_active
        user.save()
        
        status = "активовано" if user.is_active else "заблоковано"
        messages.success(request, f'Користувача {user.username} {status}')
    
    return redirect('user-list')

@login_required
def my_profile(request):
    return redirect('users:profile_detail', username=request.user.username)

@login_required
@user_passes_test(is_admin)
def user_statistics(request):
    total_users = CustomUser.objects.count()
    active_users = CustomUser.objects.filter(is_active=True).count()
    authors_count = CustomUser.objects.filter(role='author').count()
    moderators_count = CustomUser.objects.filter(role='moderator').count()
    admins_count = CustomUser.objects.filter(role='admin').count()
    
    recent_users = CustomUser.objects.order_by('-date_joined')[:10]
    
    context = {
        'total_users': total_users,
        'active_users': active_users,
        'moderators_count': moderators_count,
        'admins_count': admins_count,
        'recent_users': recent_users,
    }
    
    return render(request, 'users/statistics.html', context)

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