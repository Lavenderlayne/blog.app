from django.urls import path
from . import views

urlpatterns = [
    path('profile/<str:username>/', views.ProfileDetailView.as_view(), name='profile-detail'),
    path('profile/edit/', views.ProfileUpdateView.as_view(), name='profile-update'),
    path('user/edit/', views.UserUpdateView.as_view(), name='user-update'),
    path('', views.UserListView.as_view(), name='user-list'),
    path('search/', views.UserSearchView.as_view(), name='user-search'),
    path('statistics/', views.user_statistics, name='user-statistics'),
    path('<int:user_id>/change-role/', views.change_user_role, name='change-user-role'),
    path('<int:user_id>/toggle-status/', views.toggle_user_status, name='toggle-user-status'),
    path('my-profile/', views.my_profile, name='my-profile'),
]