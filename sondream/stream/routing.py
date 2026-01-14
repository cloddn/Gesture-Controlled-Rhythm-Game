from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    # ws://127.0.0.1:8000/stream/ 주소로 들어오는 소켓 요청을 처리
    re_path(r'ws/stream/$', consumers.RhythmGameConsumer.as_asgi()),
]