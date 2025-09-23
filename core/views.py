# from django.shortcuts import render,get_object_or_404, redirect
# from django.contrib.auth.decorators
# import login_required, user_passes_test
# from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
# from django.views.generic import
# ListView, DetailView, CreateView, UpdateView, DeleteView
# from django.urls import reverse_lazy
# from djaango.db.models import Q, Avg, Count
# from django.core.paginator import Paginator
# from .models import Post, Category, Tag, Comment, Rating, AbstractUser, CustomUser
# from .forms import CommentForm, PostForm, RatingForm
# # Create your views here.

# def is_author(user):
#     return user.is_authenticated and (user.role == 'author' or user.is_superuser)

# def is_moderator(user):
#     return user.is_authenticated and (user.role == 'moderator' or user.is_superuser)

# def is_admin(user):
#     return user.is_authenticated and (user.role == 'admin' or user.is_superuser)

#     # Головна сторінка
# class PostListView(ListView):
#     model = Post
#     template_name = 'users/post_list.html'
#     context_object_name = 'posts'