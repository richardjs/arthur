from django.db import models


class Player(models.Model):
    git_hash = models.CharField(max_length=40)
    invocation = models.TextField()


class Worker(models.Model):
    hostname = models.TextField()
    first_checkin = models.DateTimeField(auto_now_add=True)
    last_checkin = models.DateTimeField(auto_now=True)
 
    def __str__(self):
        return self.hostname
