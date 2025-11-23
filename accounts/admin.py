from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Reader

class ReaderInline(admin.StackedInline):
    model = Reader
    can_delete = False
    verbose_name_plural = "Reader info"

class CustomUserAdmin(BaseUserAdmin):
    model = User

    list_display = ("email", "role", "is_staff", "is_active")
    list_filter = ("role", "is_staff", "is_active")
    ordering = ("email",)
    search_fields = ("email",)

    fieldsets = (
        (None, {"fields": ("email", "password", "role")}),
        ("Permissions", {"fields": ("is_staff", "is_active", "is_superuser", "groups", "user_permissions")}),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "password1", "password2", "role", "is_staff", "is_active"),
        }),
    )

    def get_inline_instances(self, request, obj=None):
        inlines = []
        if obj and obj.role == "reader":
            inlines.append(ReaderInline(self.model, self.admin_site))
        return inlines


admin.site.register(User, CustomUserAdmin)