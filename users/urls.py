# lavenderlayne/blog_app/blog_app-dev/users/urls.py (ВИПРАВЛЕНО)

from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static
from .views import CustomLoginView, register
from django.contrib.auth import views as auth_views

app_name = 'users'

urlpatterns = [
    # Аутентифікація
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'), 
    path('register/', register, name='register'),
    
    # Профілі користувачів
    path('my-profile/', views.my_profile, name='my_profile'),
    path('profile/edit/', views.ProfileUpdateView.as_view(), name='profile_update'),
    path('user/edit/', views.UserUpdateView.as_view(), name='user_update'),
    path('profile/<str:username>/', views.ProfileDetailView.as_view(), name='profile_detail'),
    path('profile/<str:username>/follow/', views.toggle_follow, name='toggle_follow'),
    
    # Адмін-функції
    path('', views.UserListView.as_view(), name='user_list'),
    path('search/', views.UserSearchView.as_view(), name='user_search'),
    path('statistics/', views.user_statistics, name='user_statistics'),
    path('<int:user_id>/change-role/', views.change_user_role, name='change_user_role'),
    path('<int:user_id>/toggle-status/', views.toggle_user_status, name='toggle_user_status'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)