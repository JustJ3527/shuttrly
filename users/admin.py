from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser
from django.utils.translation import gettext_lazy as _

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    model = CustomUser

    # Les champs à afficher dans la liste
    list_display = ('email', 'username', 'first_name', 'last_name', 'is_staff', 'is_active', 'is_online')

    # Champs utilisables pour filtrer
    list_filter = ('is_staff', 'is_active', 'is_online')

    # Champs affichés dans le formulaire d'édition
    fieldsets = (
        (None, {'fields': ('email', 'username', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'date_of_birth', 'bio', 'profile_picture')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions', 'is_online')}),
        (_('Important dates'), {'fields': ('last_login_date', 'date_joined')}),
        (_('Tracking'), {'fields': ('ip_address', 'last_login_ip')}),
    )

    # Champs à utiliser lors de la création
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'first_name', 'last_name', 'password1', 'password2', 'is_active', 'is_staff')}
        ),
    )

    search_fields = ('email', 'username')
    ordering = ('email',)