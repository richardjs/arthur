from functools import wraps

from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render

from .models import *


def worker_start(request):
    # TODO actually select players
    players = [
        Player.objects.get(pk=1),
        Player.objects.get(pk=2),
    ]

    game = Game.objects.create(
        worker=request.worker,
        initial_state='0000000000000000000000000xxxxxxxx1',
    )
    for player in players:
        game.add_player(player)

    return JsonResponse(game.start_data)


def worker_py(request):
    return render(request, 'arthur/worker.py', {
        'SERVER_ROOT': settings.ARTHUR_SERVER_ROOT,
        'MAX_GAME_DEPTH': settings.ARTHUR_MAX_GAME_DEPTH,
    }, content_type='text/x-python')
