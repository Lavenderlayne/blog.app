from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

app_name = 'core'

urlpatterns = [
    path('', views.home, name='home'),
    path('posts/', views.PostListView.as_view(), name='post_list'),
    path('posts/create/', views.PostCreateView.as_view(), name='post_create'),
    path('posts/<slug:slug>/update/', views.PostUpdateView.as_view(), name='post_update'),
    path('posts/<slug:slug>/delete/', views.PostDeleteView.as_view(), name='post_delete'),
    path('posts/<slug:slug>/', views.PostDetailView.as_view(), name='post_detail'),
    
    # Додайте цей маршрут для коментарів
    path('posts/<slug:slug>/comment/', views.add_comment, name='add_comment'),
    
    path('categories/', views.CategoryListView.as_view(), name='category_list'),
    path('categories/create/', views.CategoryCreateView.as_view(), name='category_create'),
    path('categories/<slug:slug>/update/', views.CategoryUpdateView.as_view(), name='category_update'),
    path('categories/<slug:slug>/delete/', views.CategoryDeleteView.as_view(), name='category_delete'),
    path('categories/<slug:slug>/', views.CategoryDetailView.as_view(), name='category_detail'),
    path('tags/', views.TagListView.as_view(), name='tag_list'),
    path('tags/<slug:slug>/', views.TagDetailView.as_view(), name='tag_detail'),
    path('search/', views.search, name='search'),
    path('subscribe/', views.subscribe, name='subscribe'),
    path('comment/<int:pk>/delete/', views.delete_comment, name='delete_comment'),
    path('like/<slug:slug>/', views.toggle_like, name='toggle_like'),
    path('user/<str:username>/posts/', views.UserPostListView.as_view(), name='user_posts'),
    path('api/posts/', views.api_posts, name='api_posts'),
    path('api/posts/<slug:slug>/', views.api_post_detail, name='api_post_detail'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)