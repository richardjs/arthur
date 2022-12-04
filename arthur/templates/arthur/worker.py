import socket
import urllib.request


SERVER_ROOT = '{{ SERVER_ROOT }}'
GET_REPO = '{{ GIT_REPO }}'

hostname = socket.gethostname()


def request_server(path):
    request = urllib.request.Request(
        SERVER_ROOT + path,
        headers={
            'Arthur-Hostname': hostname,
        },
    )
    res = urllib.request.urlopen(request)

    return(res.read().decode())



print(request_server('/worker/start'))
