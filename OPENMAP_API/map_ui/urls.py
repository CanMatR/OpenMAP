from django.urls import path, re_path
from map_ui import views

app_name = 'ui'
urlpatterns = [
        path('campaign/add/', views.campaign_new, name='campaign_new'),
        re_path(r'campaign/add/(?P<map_name>[-:\w\s]+)', views.campaign_new_for_map, name='campaign_new_for_map'),
        re_path(r'campaign/view/(?P<campaign_name>[-:\w\s]+)', views.campaign_detail, name='campaign_detail'),
        re_path(r'campaign/list/(?P<map_name>[-:\w\s]+)', views.campaign_index, name='campaign_index'),
        re_path(r'experiment/view/(?P<campaign_name>[-:\w\s]+)/(?P<experiment_name>[-:\w\s]+)', views.experiment_detail, name='experiment_detail'),
        re_path(r'experiment/propose/(?P<campaign_name>[-:\w\s]+)', views.propose_user_experiment, name='user_propose'),
        path('', views.map_index, name='map_index'),
        ]
