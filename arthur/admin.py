from django.contrib import admin
from django.db import models
from django.forms import widgets

from .models import *


admin.site.register(Game)


admin.site.register(GameLog)


admin.site.register(GamePlayer)


class PlayerAdmin(admin.ModelAdmin):
    formfield_overrides = {
        models.TextField: {"widget": widgets.TextInput},
    }


admin.site.register(Player, PlayerAdmin)


admin.site.register(Request)


class WorkerAdmin(admin.ModelAdmin):
    readonly_fields = ["first_checkin", "last_checkin"]
    fields = ["name", "first_checkin", "last_checkin"]
    formfield_overrides = {
        models.TextField: {"widget": widgets.TextInput},
    }


admin.site.register(Worker, WorkerAdmin)
