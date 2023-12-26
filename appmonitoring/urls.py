from django.urls import path
from . import views

urlpatterns = [
    #Dashboard
    path('', views.dashboard, name='dashboard'),
    path('data', views.datapenelitian, name='data'),
    # path('upload_results', views.upload_results, name='upload_results'),
    path('tesupload', views.tes_upload, name='tesupload'),
    
]