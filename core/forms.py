# lavenderlayne/blog_app/blog_app-dev/core/forms.py

from django import forms
from .models import Post, PostComment, Subscription


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = [
            'title', 'content', 'excerpt', 'category', 'tags', 
            'post_type', 'status', 'featured_image', 
            'video_url',
            'is_featured',
            'is_pinned', 'allow_comments', 'meta_title', 'meta_description'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control form-control-lg bg-dark border-secondary text-light', 'placeholder': 'Введіть заголовок...'}),
            'content': forms.Textarea(attrs={'class': 'form-control bg-dark border-secondary text-light', 'rows': 20}),
            'excerpt': forms.Textarea(attrs={'class': 'form-control bg-dark border-secondary text-light', 'rows': 4}),
            'category': forms.Select(attrs={'class': 'form-select bg-dark border-secondary text-light'}),
            'tags': forms.SelectMultiple(attrs={'class': 'form-select bg-dark border-secondary text-light', 'rows': 5}),
            'post_type': forms.Select(attrs={'class': 'form-select bg-dark border-secondary text-light'}),
            'status': forms.Select(attrs={'class': 'form-select bg-dark border-secondary text-light'}),
            'video_url': forms.URLInput(attrs={'class': 'form-control bg-dark border-secondary text-light', 'placeholder': 'https://www.youtube.com/watch?v=...'}),
            'meta_title': forms.TextInput(attrs={'class': 'form-control bg-dark border-secondary text-light'}),
            'meta_description': forms.Textarea(attrs={'class': 'form-control bg-dark border-secondary text-light', 'rows': 3}),
            
            # Додамо класи до чекбоксів
            'is_featured': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_pinned': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'allow_comments': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = PostComment
        fields = ['content', 'parent']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control bg-dark border-secondary text-light', 
                'rows': 3,
                'placeholder': 'Залишити коментар...'
            }),
            'parent': forms.HiddenInput(),
        }


class SubscriptionForm(forms.ModelForm):
    class Meta:
        model = Subscription
        fields = ['email']
        widgets = {
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ваш email...'
            })
        }