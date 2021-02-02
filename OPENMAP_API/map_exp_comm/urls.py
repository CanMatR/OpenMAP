from django.urls import include, path, re_path
from map_exp_comm import views

urlpatterns = [
        re_path(r'experimentStatus/(?P<campaign_name>[-:\w\ ]+)/(?P<experiment_name>[-:\w\ ]+)/', views.experiment_status),
        re_path(r'stageStatus/(?P<campaign_name>[-:\w\ ]+)/(?P<experiment_name>[-:\w\ ]+)/(?P<stage_name>[-:\w\ ]+)/', views.stage_status),
        re_path(r'input/(?P<campaign_name>[-:\w\ ]+)/(?P<experiment_name>[-:\w\ ]+)/(?P<input_name>[\w]+)/', views.input_value),
        re_path(r'output/(?P<campaign_name>[-:\w\ ]+)/(?P<experiment_name>[-:\w\ ]+)/(?P<output_name>[\w]+)/', views.output_value),
        re_path(r'output/(?P<campaign_name>[-:\w\ ]+)/(?P<experiment_name>[-:\w\ ]+)/', views.output_values),
        ]
