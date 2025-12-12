from django import forms
from .models import CustomUser, Profile
from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser

class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password1', 'password2']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-control bg-dark border-secondary text-light'})

class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

class ProfileUpdateForm(forms.ModelForm):
    # --- Додаємо поля з моделі User ---
    username = forms.CharField(
        label="Нікнейм",
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    first_name = forms.CharField(
        label="Ім'я",
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    last_name = forms.CharField(
        label="Прізвище",
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    email = forms.EmailField(
        label="Email",
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = Profile
        # Поля самої моделі Profile
        fields = ['bio', 'avatar', 'phone', 'website', 'location', 'birth_date', 
                 'social_x', 'social_telegram', 'social_discord',
                 'email_notifications', 'email_subscriptions']
        widgets = {
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'website': forms.URLInput(attrs={'class': 'form-control'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'birth_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'social_x': forms.URLInput(attrs={'class': 'form-control'}),
            'social_telegram': forms.TextInput(attrs={'class': 'form-control'}),
            'social_discord': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # При завантаженні форми підставляємо поточні дані користувача
        if self.instance and self.instance.user:
            self.fields['username'].initial = self.instance.user.username
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
            self.fields['email'].initial = self.instance.user.email

    def save(self, commit=True):
        # 1. Зберігаємо дані профілю
        profile = super().save(commit=commit)
        
        # 2. Оновлюємо дані користувача (User)
        user = profile.user
        user.username = self.cleaned_data['username']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']
        
        if commit:
            user.save()
            
        return profile

class UserRoleForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['role']
        widgets = {
            'role': forms.Select(attrs={'class': 'form-control'})
        }