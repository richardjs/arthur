import logging

from .models import Player, Worker


logger = logging.getLogger(__name__)


class WorkerMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path_info.startswith("/worker/"):
            worker_name = request.headers["Arthur-Worker"]

            worker, created = Worker.objects.get_or_create(name=worker_name)
            if created:
                logger.info(f"New worker #{worker.id} with name {worker_name}")
            else:
                # Update check-in time
                worker.save()

            request.worker = worker

            logger.debug(f"Worker #{worker.id} requests {request.path_info}")

        return self.get_response(request)
