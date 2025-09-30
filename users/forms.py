from django import forms
from .models import CustomUser, Profile

class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email']  # Видалити bio, avatar
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['bio', 'avatar', 'phone', 'website', 'location', 'birth_date', 
                 'social_facebook', 'social_x', 'social_instagram',
                 'email_notifications', 'email_subscriptions']
        widgets = {
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'website': forms.URLInput(attrs={'class': 'form-control'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'birth_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'social_facebook': forms.URLInput(attrs={'class': 'form-control'}),
            'social_x': forms.URLInput(attrs={'class': 'form-control'}),
            'social_instagram': forms.URLInput(attrs={'class': 'form-control'}),
        }

class UserRoleForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['role']
        widgets = {
            'role': forms.Select(attrs={'class': 'form-control'})
        }