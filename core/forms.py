from django import forms
from .models import Post, PostComment, Subscription


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = [
            'title', 'content', 'excerpt', 'category', 'tags', 
            'post_type', 'status', 'featured_image', 'is_featured',
            'is_pinned', 'allow_comments', 'meta_title', 'meta_description'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 10}),
            'excerpt': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'tags': forms.SelectMultiple(attrs={'class': 'form-control'}),
            'post_type': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'meta_title': forms.TextInput(attrs={'class': 'form-control'}),
            'meta_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
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