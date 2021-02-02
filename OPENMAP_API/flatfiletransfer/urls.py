# flatfiletransfer/urls.py

from django.urls import include, path, re_path
from flatfiletransfer import views

urlpatterns = [
        re_path(r'getFilenameHashes/(?P<campaign_name>[-:\w\s]+)/(?P<experiment_name>[-:\w\ ]+)/', views.file_hashes),
        path('reportFileTransfer/<name_hash>/', views.file_transfer_report),
        path('fileMetadata/<name_hash>/<field>/', views.file_metadata_detail),
        path('fileMetadata/<name_hash>/', views.file_metadata),
        ]
