from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("video_feed/", views.video_feed, name="video_feed"),
    
    # http://127.0.0.1:8000/game 주소로 접속하면 game_page 함수 실행
    path('game/', views.game_page), 
]