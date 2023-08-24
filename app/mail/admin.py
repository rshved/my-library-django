from django.contrib import admin

from mail import models


@admin.register(models.Mail)
class MailAdmin(admin.ModelAdmin):
    search_fields = ['user__email']
    list_display = ['user', 'email', 'is_send', 'created_at']
    list_filter = ['is_send']