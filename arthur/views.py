import logging
from functools import wraps

from django.conf import settings
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404,render
from django.views.decorators.csrf import csrf_exempt

from .models import *


logger = logging.getLogger(__name__)


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

    logger.info(f'Assigning worker #{game.worker.id} game #{game.id}')

    return JsonResponse(game.start_data)


@csrf_exempt
def worker_finish(request):
    game_id = request.POST['game_id']

    game = get_object_or_404(Game, pk=game_id)
    if game.worker != request.worker or game.status != Game.STATUS.IN_PROGRESS:
        return HttpResponseForbidden()

    # result is "win", "draw", or "error"
    # Not to be confused with game.status
    result = request.POST['result'].lower()

    if result in ['win', 'draw']:
        game.status = Game.Status.COMPLETED
        game.save()

    winners = request.POST.getlist('winners')


def worker_py(request):
    return render(request, 'arthur/worker.py', {
        'SERVER_ROOT': settings.ARTHUR_SERVER_ROOT,
        'MAX_GAME_DEPTH': settings.ARTHUR_MAX_GAME_DEPTH,
    }, content_type='text/x-python')
