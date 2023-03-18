from .glicko import Rating
from .models import *


def calculate_ratings():
    games = Game.objects.filter(status='C')

    ratings = {}

    for game in games:
        winner = game.gameplayer_set.filter(winner=True)
        loser = game.gameplayer_set.filter(winner=False)

        # TODO implement draws
        if len(winner) != 1 or len(loser) != 1:
            print('Skipping game', game.id)
            continue

        winner = winner[0].player
        loser = loser[0].player

        if winner not in ratings:
            ratings[winner] = Rating()
        if loser not in ratings:
            ratings[loser] = Rating()
        
        winner_rating = ratings[winner]
        loser_rating = ratings[loser]

        new_winner_rating = winner_rating.update(wins=[loser_rating])
        new_loser_rating = loser_rating.update(losses=[winner_rating])

        ratings[winner] = new_winner_rating
        ratings[loser] = new_loser_rating

    ratings = ratings.items()
    ratings = sorted(ratings, key=lambda item: item[1].r, reverse=True)
    ratings = [(player, rating.r, rating.rd) for (player, rating) in ratings]
    return ratings
