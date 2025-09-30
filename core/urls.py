from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('posts/', views.PostListView.as_view(), name='post_list'),
    path('posts/<slug:slug>/', views.PostDetailView.as_view(), name='post_detail'),
    path('posts/create/', views.PostCreateView.as_view(), name='post_create'),
    path('posts/<slug:slug>/update/', views.PostUpdateView.as_view(), name='post_update'),
    path('posts/<slug:slug>/delete/', views.PostDeleteView.as_view(), name='post_delete'),
    path('categories/', views.CategoryListView.as_view(), name='category_list'),
    path('categories/<slug:slug>/', views.CategoryDetailView.as_view(), name='category_detail'),
    path('tags/', views.TagListView.as_view(), name='tag_list'),
    path('tags/<slug:slug>/', views.TagDetailView.as_view(), name='tag_detail'),
    path('search/', views.search, name='search'),
    path('subscribe/', views.subscribe, name='subscribe'),
    path('comment/<int:pk>/delete/', views.delete_comment, name='delete_comment'),
    path('like/<slug:slug>/', views.toggle_like, name='toggle_like'),
]