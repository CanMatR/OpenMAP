# map_api
### python dependencies
* Django
* djangorestframework
* requests (for test script)
* paramiko (for test script)
* scp (for test script)
* celery
* django-tables2

### other dependencies
* running instance of rabbitmq (celery backend)

### unit tests
* **all**:  
python manage.py test
* **filetransfer**:  
python manage.py test flatfiletransfer
* **ML to Orchestrator**:  
python manage.py test map_ml
* **MAP Experiment Facility to Orchestrator**:  
python manage.py test map_exp_comm

### getting started for live testing:
#### setup database:
1. python manage.py makemigrations
2. python manage.py makemigrations map_base
3. python manage.py makemigrations flatfiletransfer
4. python manage.py migrate

#### create admin account
* python manage.py createsuperuser

#### to start test server:
* python manage.py runserver

#### add some dummy data
Logging in to the admin interface at localhost:8000/admin will let you populate the database with some objects.
* The test script livetest_request__map_api.py expects a Campaign called "api_testing" and an Experiment called "test_1".
* The script additionally expects a user "client" with password "ftTestPW"

### configuration before running with ML and MAP Surrogate
* User, Token
    * can be 1 each for ML and surrogate, or just 1 shared
    * configure ML system and surrogate with token
* Map base (just need a name)
* Map facility
    * note: remember to include http:// or https:// when specifying api url for surrogate
* ML facility
    * location just hostname for ssh
	* "train script" and "probe script" are the shell one-liners to launch their respective scripts e.g. "cd path/to/ML/script; ./action.sh"
* Map stages
    * corresponding to Modules in surrogate
* Map inputs
    * corresponding to those defined in surrogate
* Map outputs
    * corresponding to surrogate
* Campaign

#### to start celery worker
`celery -A map_api worker -l info -Q map_orchestration`
