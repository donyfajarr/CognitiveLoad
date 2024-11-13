from django.urls import path
from . import views

urlpatterns = [
    #Dashboard
    path('', views.dashboard, name='dashboard'),
    # path('data', views.datapenelitian, name='data'),
    # path('upload_results', views.upload_results, name='upload_results'),
    # path('tesupload', views.tes_upload, name='tesupload'),
    path('emg', views.emg, name='emg'),
    path('heartrate', views.heartrate, name='heartrate'),
    path('temp', views.temp, name='temp'),
    path('video_feed/', views.video_feed, name='video_feed'),
]