from django.contrib import admin
from django.db import models
from django.forms import widgets

from arthur.models import Player, Worker


admin.site.register(Player)


class WorkerAdmin(admin.ModelAdmin):
    readonly_fields = ['first_checkin', 'last_checkin']
    fields = ['hostname', 'first_checkin', 'last_checkin']
    formfield_overrides = {
        models.TextField: {'widget': widgets.TextInput},
    }
admin.site.register(Worker, WorkerAdmin)
