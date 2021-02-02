from django.contrib.auth.models import User
from rest_framework.test import APITestCase, APITransactionTestCase
from map_base.models import MapBase, Campaign

class MapAPITestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user( 'client', 'client@apitest', 'ftTestPW' )
        self.client.login( username='client', password='ftTestPW' )
        self.base_uid = {
                    'map_name': 'test_map',
                    'campaign_name': 'api_testing',
                    'experiment_name': 'Experiment - test 1',
                    'stage_name': 'measure',
                    'input_name': 'input1',
                    'output_name': 'measure1',
                }

        self.test_map = MapBase.objects.create(name=self.base_uid['map_name'], storage_location='localhost')
        self.campaign = Campaign.objects.create(for_map=self.test_map, name=self.base_uid['campaign_name'])

class MapAPITransactionTestCase(APITransactionTestCase):
    def setUp(self):
        self.user = User.objects.create_user( 'client', 'client@apitest', 'ftTestPW' )
        self.client.login( username='client', password='ftTestPW' )
        self.base_uid = {
                    'map_name': 'test_map',
                    'campaign_name': 'api_testing',
                    'experiment_name': 'Experiment - test 1',
                    'stage_name': 'measure',
                    'input_name': 'input1',
                    'output_name': 'measure1',
                }

        self.test_map = MapBase.objects.create(name=self.base_uid['map_name'], storage_location='localhost')
        self.campaign = Campaign.objects.create(for_map=self.test_map, name=self.base_uid['campaign_name'])
