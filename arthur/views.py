import logging
from functools import wraps
from random import choice

from django.conf import settings
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.csrf import csrf_exempt

from .models import *


logger = logging.getLogger(__name__)


def worker_start(request):
    # TODO use a better method for player scheduling
    all_players = Player.objects.all()
    assert all_players.count() > 1

    player1 = choice(all_players)
    player2 = choice(all_players)
    while player1 == player2:
        player2 = choice(all_players)

    game = Game.objects.create(
        worker=request.worker,
        initial_state="1",
    )
    game.add_player(player1)
    game.add_player(player2)

    logger.info(f"Assigning worker #{game.worker.id} game #{game.id}")

    return JsonResponse(game.start_data)


@csrf_exempt
def worker_finish(request):
    game_id = request.POST["game_id"]

    game = get_object_or_404(Game, pk=game_id)
    if game.worker != request.worker or game.status != Game.Status.IN_PROGRESS:
        return HttpResponseForbidden()

    # result is "win", "draw", or "error"
    # Not to be confused with game.status
    result = request.POST["result"].lower()

    if result in ["win", "draw"]:
        game.status = Game.Status.COMPLETED
        game.save()
    # TODO Support other results
    else:
        return HttpResponseForbidden()

    winner = get_object_or_404(Player, pk=request.POST['winner'])
    if not game.gameplayer_set.filter(player=winner).count():
        return HttpResponseForbidden()

    # TODO We're running this query twice
    gameplayer = game.gameplayer_set.filter(player=winner)[0]
    gameplayer.winner = True
    gameplayer.save()

    return JsonResponse({'result': 'ok'})


def worker_py(request):
    return render(
        request,
        "arthur/worker.py",
        {
            "SERVER_ROOT": settings.ARTHUR_SERVER_ROOT,
            "MAX_GAME_DEPTH": settings.ARTHUR_MAX_GAME_DEPTH,
        },
        content_type="text/x-python",
    )
