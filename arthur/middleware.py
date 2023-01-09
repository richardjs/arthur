from .models import Player, Worker


class WorkerMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path_info.startswith('/worker/'):
            hostname = request.headers['Arthur-Hostname']

            worker, created = Worker.objects.get_or_create(hostname=hostname)

            request.worker = worker

            if created:
                print(f'New worker with hostname {hostname}')
            else:
                # Update check-in time
                worker.save()

            print(f'Worker ID #{worker.id}')

        return self.get_response(request)
