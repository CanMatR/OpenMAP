from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'map_api.settings')

app = Celery('map_api')

# all celery-related configuration keys to start with 'CELERY_' prefix
app.config_from_object('django.conf:settings', namespace='CELERY')

# configure routing
app.conf.task_default_queue = 'map_orchestration'

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))
