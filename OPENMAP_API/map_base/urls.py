from django.urls import re_path
from map_base import views

urlpatterns = [
        re_path(r'viewCampaign/(?P<campaign_name>[-:\w\s]+)', views.campaign_experiments),
        ]
