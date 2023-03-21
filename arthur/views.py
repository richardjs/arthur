import logging
from functools import wraps
from random import choice

from django.conf import settings
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.csrf import csrf_exempt

from .models import *
from .ratings import calculate_ratings


logger = logging.getLogger(__name__)


def worker_start(request):
    # TODO use a better method for player scheduling
    all_players = Player.objects.all()
    assert all_players.count() > 1

    if Request.objects.count():
        r = Request.objects.first()

        player1 = r.player
        if r.opponent:
            player2 = r.opponent
        else:
            player2 = choice(all_players)
            while player1 == player2:
                player2 = choice(all_players)

        r.number -= 1
        if r.number:
            r.save()
        else:
            r.delete()

        if choice([True, False]):
            t = player2
            player2 = player1
            player1 = t

    else:
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
def worker_log(request):
    # TODO This code is used in several places
    game_id = request.POST["game_id"]

    game = get_object_or_404(Game, pk=game_id)
    if game.worker != request.worker or game.status != Game.Status.IN_PROGRESS:
        return HttpResponseForbidden()

    player = request.POST["player"]
    if not game.gameplayer_set.filter(player=player).count():
        return HttpResponseForbidden()
    # TODO We're running this query twice
    player = game.gameplayer_set.filter(player=player)[0].player

    log = GameLog(
        game=game,
        player=player,
        number=request.POST["number"],
        state=request.POST["state"],
        text=request.POST["text"],
    )
    log.save()
    return JsonResponse({"result": "ok"})


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
    elif result == "depth_out":
        game.state = Game.Status.DEPTH_OUT
    elif result == "error":
        game.state = Game.Status.ERROR
    else:
        return HttpResponseForbidden()

    game.save()

    if result == "win":
        winner = get_object_or_404(Player, pk=request.POST["winner"])
        if not game.gameplayer_set.filter(player=winner).count():
            return HttpResponseForbidden()

        # TODO We're running this query twice
        gameplayer = game.gameplayer_set.filter(player=winner)[0]
        gameplayer.winner = True
        gameplayer.save()

    return JsonResponse({"result": "ok"})


def worker_py(request):
    return render(
        request,
        "arthur/worker.py",
        {
            "SERVER_ROOT": settings.ARTHUR_SERVER_ROOT,
            "MAX_GAME_DEPTH": settings.ARTHUR_MAX_GAME_DEPTH,
            "DRAW_REPITITIONS": settings.ARTHUR_DRAW_REPITITIONS,
        },
        content_type="text/x-python",
    )


def dashboard(request):
    ratings = calculate_ratings()
    player_ratings = {player: r for player, r, rd in ratings}
    data = []
    for player, r, rd in ratings:
        gps = GamePlayer.objects.filter(player=player)

        games = [
            gp.game
            for gp in gps
            if gp.game.status == Game.Status.COMPLETED
            and gp.game.gameplayer_set.filter(winner=True).count()
        ]

        wins = [
            game
            for game in games
            if game.gameplayer_set.filter(player=player, winner=True).count()
        ]

        losses = [
            game
            for game in games
            if game.gameplayer_set.filter(player=player, winner=False).count()
        ]

        win_pct = len(wins)/len(games) * 100

        game_moves = [
            game.gamelog_set.count()
            for game in games
        ]
        game_moves_avg = sum(game_moves)/len(game_moves)

        opponent_ratings = []
        for game in games:
            opponent = [gp for gp in game.gameplayer_set.all() if gp.player != player][
                0
            ].player
            opponent_ratings.append(player_ratings[opponent])
        if opponent_ratings:
            avg_opponent_rating = sum(opponent_ratings)/len(opponent_ratings)
        else:
            avg_opponent_rating = ' '

        win_opponent_ratings = []
        for game in wins:
            opponent = [gp for gp in game.gameplayer_set.all() if gp.player != player][
                0
            ].player
            win_opponent_ratings.append(player_ratings[opponent])
        if win_opponent_ratings:
            avg_win_rating = sum(win_opponent_ratings)/len(win_opponent_ratings)
        else:
            avg_win_rating = ' '

        loss_opponent_ratings = []
        for game in losses:
            opponent = [gp for gp in game.gameplayer_set.all() if gp.player != player][
                0
            ].player
            loss_opponent_ratings.append(player_ratings[opponent])
        if loss_opponent_ratings:
            avg_loss_rating = sum(loss_opponent_ratings)/len(loss_opponent_ratings)
        else:
            avg_loss_rating = ' '

        data.append(
            {
                "player_id": player.id,
                "name": player.name,
                "r": int(r),
                "rd": int(rd),
                "num_games": len(games),
                "num_wins": len(wins),
                "num_losses": len(losses),
                "best_win": int(max(win_opponent_ratings))
                if win_opponent_ratings
                else " ",
                "worst_loss": int(min(loss_opponent_ratings))
                if loss_opponent_ratings
                else " ",
                'avg_opponent_rating': avg_opponent_rating,
                'avg_win_rating': avg_win_rating,
                'avg_loss_rating': avg_loss_rating,
                'win_pct': win_pct,
                'game_moves_avg': game_moves_avg,
            }
        )
    return render(request, "arthur/dashboard.html", locals())
