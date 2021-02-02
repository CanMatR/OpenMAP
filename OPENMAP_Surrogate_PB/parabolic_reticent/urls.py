# parabolic/urls.py

from django.urls import include, path
from parabolic_reticent import views

urlpatterns = [
        path('experiment/new/', views.new_experiment),
        path('experiment/<exp_id>/config/<module>/', views.module_config),
        path('experiment/<exp_id>/status/<module>/', views.module_status),
        path('experiment/<exp_id>/status/', views.experiment_status),
        path('queue/append/', views.queue_append),
        path('experiment/<exp_id>/results/<module>/', views.module_results),
        path('experiment/<exp_id>/results/', views.experiment_results),
        ]
