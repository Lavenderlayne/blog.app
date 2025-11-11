from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Profile
from django.db.models import Count

@admin.action(description='Заблокувати обраних користувачів')
def ban_users(modeladmin, request, queryset):
    queryset.update(is_active=False)

@admin.action(description='Активувати обраних користувачів')
def activate_users(modeladmin, request, queryset):
    queryset.update(is_active=True)

class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'Профіль'
    fields = ('bio', 'avatar', 'location', 'website')
    readonly_fields = ('avatar',) 

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'role', 'is_active', 'date_joined', 'get_post_count')
    list_filter = ('role', 'is_active', 'is_staff')
    list_editable = ('role', 'is_active')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    
    fieldsets = UserAdmin.fieldsets + (
        ('Роль та Слідкування', {'fields': ('role', 'following')}),
    )
    
    inlines = (ProfileInline,)
    actions = [ban_users, activate_users]
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(post_count=Count('post'))
    
    @admin.display(description='Постів', ordering='post_count')
    def get_post_count(self, obj):
        return obj.post_count

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'location', 'website')
    search_fields = ('user__username', 'location')