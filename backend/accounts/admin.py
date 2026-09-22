from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    fieldsets = DjangoUserAdmin.fieldsets + (
        ("Informations agent", {"fields": ("matricule", "must_change_password")}),
    )
    list_display = ("username", "matricule", "first_name", "last_name", "email", "is_staff")
    search_fields = ("username", "matricule", "first_name", "last_name", "email")
