from functools import wraps

from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render

from arthur.models import Player, Worker


def worker_endpoint(view_func):
    @wraps(view_func)
    def wrapper_view(request, *args, **kwargs):
        hostname = request.headers['Arthur-Hostname']
        worker, created = Worker.objects.get_or_create(hostname=hostname)

        if created:
            print(f'New worker with hostname {hostname}')
        else:
            # Update check-in time
            worker.save()

        print(f'Worker ID #{worker.id}')


        return view_func(request, *args, **kwargs)

    return wrapper_view


@worker_endpoint
def worker_start(request):
    players = [
        Player.objects.get(pk=1),
        Player.objects.get(pk=2),
    ]

    return JsonResponse({
        'players': [{
                'id': player.id,
                'commit': player.commit,
                'invocation': player.invocation,
            } for player in players
        ],
        'state': '0000000000000000000000000xxxxxxxx1',
    })


def worker_py(request):
    print(request.headers)

    return render(request, 'arthur/worker.py', {
        'SERVER_ROOT': settings.ARTHUR_SERVER_ROOT,
        'GIT_REPO': settings.ARTHUR_GIT_REPO,
    }, content_type='text/x-python')
