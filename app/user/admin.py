from django.contrib import admin

from user import models


@admin.register(models.User)
class UserAdmin(admin.ModelAdmin):
    readonly_fields = [
        'uid', 'created_at', 'last_login',
    ]
    search_fields = ['email', 'uid', ]
    list_display = (
        'email', 'name', 'surname', 'is_email_verified', 'is_phone_verified', 'created_at',
    )
    fields = [
        'email', 'name', 'phone', 'avatar',
        'is_staff', 'is_email_verified', 'is_phone_verified', 'password',
        'push_id', 'device_id', 'is_active',
        'created_at', 'last_login',
    ]
    def has_delete_permission(self, request, obj=None):
        return obj != request.user
    
    # on save if password is not encrypted encrypt it
    def save_model(self, request, obj, form, change):
        if not obj.password:
            obj.save()
        if obj.password and not obj.password.startswith('pbkdf2_sha256'):
            obj.set_password(obj.password)
        obj.save()