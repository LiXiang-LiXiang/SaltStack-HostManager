from django.contrib import admin

# Register your models here.
from Arya import models


class HostAdmin(admin.ModelAdmin):
    list_display = ('hostname', 'os_type', 'status')


admin.site.register(models.Host, HostAdmin)
admin.site.register(models.HostGroup)