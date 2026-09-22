from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import Direction, Service, User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    fieldsets = DjangoUserAdmin.fieldsets + (
        (
            "Informations agent",
            {"fields": ("matricule", "must_change_password", "role_hierarchique", "service")},
        ),
    )
    list_display = (
        "username",
        "matricule",
        "first_name",
        "last_name",
        "role_hierarchique",
        "service",
        "is_staff",
    )
    list_filter = ("role_hierarchique", "service")
    search_fields = ("username", "matricule", "first_name", "last_name", "email")


@admin.register(Direction)
class DirectionAdmin(admin.ModelAdmin):
    list_display = ("nom", "directeur")


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ("nom", "direction", "chef_service")
    list_filter = ("direction",)
