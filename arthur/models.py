from django.db import models


class Game(models.Model):
    players = models.ManyToManyField('Player', through='GamePlayer')
    worker = models.ForeignKey('Worker', on_delete=models.PROTECT)

    initial_state = models.TextField()

    start_timestamp = models.DateTimeField(auto_now_add=True)
    end_timestamp = models.DateTimeField(null=True)

    class Status(models.TextChoices):
        IN_PROGRESS = 'I'
        COMPLETED = 'C'
        ERROR = 'E'
        ABANDONED = 'A'
    status = models.CharField(
        max_length=1,
        choices=Status.choices,
        default=Status.IN_PROGRESS,
    )

    @property
    def start_data(self):
        return {
            'game_id': self.id,
            'players': [{
                    'number': game_player.number,
                    'id': game_player.player.id,
                    'repository': game_player.player.repository,
                    'commit': game_player.player.commit,
                    'invocation': game_player.player.invocation,
                } for game_player in self.gameplayer_set.order_by('number')
            ],
            'state': self.initial_state,
        }


    def add_player(self, player):
        GamePlayer.objects.create(
            game=self,
            player=player,
            number=self.players.count()
        )

    def __str__(self):
        return f'{self.worker} {self.status} {self.start_timestamp}'


class GamePlayer(models.Model):
    game = models.ForeignKey('Game', on_delete=models.CASCADE)
    player = models.ForeignKey('Player', on_delete=models.PROTECT)

    number = models.IntegerField()
    winner = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.game} player {self.number + 1}'


class Player(models.Model):
    name = models.TextField(null=True, blank=True)
    repository = models.TextField()
    commit = models.CharField(max_length=40)
    invocation = models.TextField()

    def __str__(self):
        return self.name or f'Player #{self.id}'


class Worker(models.Model):
    hostname = models.TextField()
    first_checkin = models.DateTimeField(auto_now_add=True)
    last_checkin = models.DateTimeField(auto_now=True)
 
    def __str__(self):
        return self.hostname
