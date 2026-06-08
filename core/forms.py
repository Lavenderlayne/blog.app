from django import forms
from .models import Post, PostComment, Subscription, Tag
from django_ckeditor_5.widgets import CKEditor5Widget

class TagForm(forms.ModelForm):
    class Meta:
        model = Tag
        fields = ['name', 'slug']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control bg-dark border-secondary text-light'}),
            'slug': forms.TextInput(attrs={'class': 'form-control bg-dark border-secondary text-light', 'placeholder': 'Залиште порожнім для авто-генерації'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['slug'].required = False

class PostForm(forms.ModelForm):
    tags = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control bg-dark border-secondary text-light',
            'placeholder': 'Створіть тег'
        }),
        label="Теги"
    )

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
            'content': CKEditor5Widget(attrs={"class": "django_ckeditor_5"},config_name="default"),
            'excerpt': forms.Textarea(attrs={'class': 'form-control bg-dark border-secondary text-light', 'rows': 4}),
            'category': forms.Select(attrs={'class': 'form-select bg-dark border-secondary text-light'}),

            'post_type': forms.Select(attrs={'class': 'form-select bg-dark border-secondary text-light'}),
            'status': forms.Select(attrs={'class': 'form-select bg-dark border-secondary text-light'}),
            'video_url': forms.URLInput(attrs={'class': 'form-control bg-dark border-secondary text-light', 'placeholder': 'https://www.youtube.com/watch?v=...'}),
            'meta_title': forms.TextInput(attrs={'class': 'form-control bg-dark border-secondary text-light'}),
            'meta_description': forms.Textarea(attrs={'class': 'form-control bg-dark border-secondary text-light', 'rows': 3}),
            
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