from django.urls import path

from arthur import views


urlpatterns = [
    path('worker.py', views.worker_py),

    path('worker/start', views.worker_start, name='worker-start'),
    path('worker/finish', views.worker_finish, name='worker-finish'),
]
