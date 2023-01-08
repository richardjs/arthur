from django.db import models


class Game(models.Model):
    players = models.ManyToManyField('Player', through='GamePlayer')

    start_timestamp = models.DateTimeField(auto_now_add=True)
    end_timestamp = models.DateTimeField(null=True)

    class Status(models.TextChoices):
        IN_PROGRESS = 'I'
        FINISHED = 'F'
        ERROR = 'E'
        ABANDONED = 'A'
    status = models.CharField(
        max_length=1,
        choices=Status.choices,
        default=Status.IN_PROGRESS,
    )


class GamePlayer(models.Model):
    game = models.ForeignKey('Game', on_delete=models.CASCADE)
    player = models.ForeignKey('Player', on_delete=models.CASCADE)

    number = models.IntegerField()
    winner = models.BooleanField(default=False)


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
