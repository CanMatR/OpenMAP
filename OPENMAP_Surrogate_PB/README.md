# map_surrogate
API to surrogate functions for testing MAP

#### to start test server
`python manage.py runserver [host]:[port]`

#### to start celery worker
`celery -A map_surrogate worker -l info -Q map_surrogate`
