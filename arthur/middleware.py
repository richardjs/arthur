from .models import Player, Worker


class WorkerStatsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if 'Arthur-Hostname' in request.headers:
            hostname = request.headers['Arthur-Hostname']
            worker, created = Worker.objects.get_or_create(hostname=hostname)

            if created:
                print(f'New worker with hostname {hostname}')
            else:
                # Update check-in time
                worker.save()

            print(f'Worker ID #{worker.id}')

        return self.get_response(request)
