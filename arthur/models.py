from collections import Counter

from django.db import models


class GameManager(models.Manager):
    def start_data(self):
        start_actions = Counter()
        start_actions_wins = Counter()
        start_logs = [g.gamelog_set.filter(number=0).first() for g in self.all()]
        for log in start_logs:
            if not log:
                continue
            for line in log.text.split("\n"):
                if not line.startswith("action:"):
                    continue
                _, action = line.split(":")
                action = action.strip()
                start_actions[action] += 1

            win_gp = log.game.gameplayer_set.filter(winner=True).first()
            if win_gp and win_gp.player == log.player:
                start_actions_wins[action] += 1

        print(start_actions)
        print(start_actions_wins)
        for key in start_actions:
            print(key, start_actions_wins[key] / start_actions[key])

        second_actions = Counter()
        second_actions_wins = Counter()
        second_logs = [g.gamelog_set.filter(number=1).first() for g in self.all()]
        for log in second_logs:
            if not log:
                continue
            for line in log.text.split("\n"):
                if not line.startswith("action:"):
                    continue
                _, action = line.split(":")
                action = action.strip()[:2]
                second_actions[action] += 1

            win_gp = log.game.gameplayer_set.filter(winner=True).first()
            if win_gp and win_gp.player == log.player:
                second_actions_wins[action] += 1

        print(second_actions)
        print(second_actions_wins)
        for key in second_actions:
            print(key, second_actions_wins[key] / second_actions[key])


class Game(models.Model):
    players = models.ManyToManyField("Player", through="GamePlayer")
    worker = models.ForeignKey("Worker", on_delete=models.PROTECT)

    initial_state = models.TextField()

    start_timestamp = models.DateTimeField(auto_now_add=True)
    end_timestamp = models.DateTimeField(null=True)

    objects = GameManager()

    class Status(models.TextChoices):
        IN_PROGRESS = "I"
        COMPLETED = "C"
        DEPTH_OUT = "D"
        ERROR = "E"
        ABANDONED = "A"

    status = models.CharField(
        max_length=1,
        choices=Status.choices,
        default=Status.IN_PROGRESS,
    )

    @property
    def start_data(self):
        return {
            "game_id": self.id,
            "players": [
                {
                    "number": game_player.number,
                    "id": game_player.player.id,
                    "repository": game_player.player.repository,
                    "commit": game_player.player.commit,
                    "invocation": game_player.player.invocation,
                }
                for game_player in self.gameplayer_set.order_by("number")
            ],
            "state": self.initial_state,
        }

    def add_player(self, player):
        GamePlayer.objects.create(game=self, player=player, number=self.players.count())

    def max_state_repititions(self):
        states = [log.state for log in self.gamelog_set.all()]
        counts = Counter()
        for state in states:
            counts[state] += 1
        return max(counts.values())

    def matchups(self):
        pass

    def __str__(self):
        return f"{self.worker} {self.status} {self.start_timestamp}"


class GameLog(models.Model):
    game = models.ForeignKey("Game", on_delete=models.CASCADE)
    player = models.ForeignKey("Player", on_delete=models.PROTECT)
    number = models.IntegerField()
    state = models.TextField()
    text = models.TextField()


class GamePlayer(models.Model):
    game = models.ForeignKey("Game", on_delete=models.CASCADE)
    player = models.ForeignKey("Player", on_delete=models.PROTECT)

    number = models.IntegerField()
    winner = models.BooleanField(default=False)

    def opponent(self):
        return [gp for gp in gameplayer_set.all() if gp != self][0]

    def __str__(self):
        return f"{self.game} player {self.number + 1}"


class Player(models.Model):
    name = models.TextField(null=True, blank=True)
    repository = models.TextField()
    commit = models.CharField(max_length=40)
    invocation = models.TextField()

    def __str__(self):
        return self.name or f"Player #{self.id}"


class Request(models.Model):
    player = models.ForeignKey(
        "Player", on_delete=models.CASCADE, related_name="request_set"
    )
    opponent = models.ForeignKey(
        "Player",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name="request_opponent_set",
    )
    number = models.IntegerField(default=1)


class Worker(models.Model):
    name = models.TextField()
    first_checkin = models.DateTimeField(auto_now_add=True)
    last_checkin = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
