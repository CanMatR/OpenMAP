from django.urls import include, path, re_path
from map_ml import views

urlpatterns = [
        re_path(r'trained/(?P<campaign_name>[-:\w\ ]+)/', views.ml_trained),
        re_path(r'failed/(?P<campaign_name>[-:\w\ ]+)/', views.ml_training_failed),
        re_path(r'proposeExperiment/(?P<campaign_name>[-:\w\ ]+)/', views.propose_experiment),
        ]
