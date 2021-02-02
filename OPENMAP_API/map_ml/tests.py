from django.urls import reverse
from django.contrib.auth.models import User

from rest_framework.test import APITransactionTestCase
from rest_framework import status

from unittest import mock
from celery.contrib.testing.worker import start_worker
from time import sleep

from map_api.celery import app
from map_ml import views
from map_base.models import MapStage, MapInput, MapOutput
from map_base.models import Campaign, Experiment, ExpInputVal
from map_base.tests import MapAPITestCase, MapAPITransactionTestCase

############################################################
#
# test ml model training messages
#
############################################################
class MlStatusTests(MapAPITestCase):

    def setUp(self):
        super().setUp()

        self.uid_use = { 'campaign_name': self.base_uid['campaign_name'] }

    ##############################
    # POST
    ##############################
    def test_trained_campaign_does_not_exist(self):
        url = reverse( views.ml_trained, kwargs = {'campaign_name': 'noCampaign'} )
        data = {}

        response = self.client.post(url, data, format='json')
        self.assertEqual( response.status_code, status.HTTP_404_NOT_FOUND )

    def test_trained(self):
        url = reverse( views.ml_trained, kwargs = self.uid_use )
        data = {}

        response = self.client.post(url, data, format='json')
        self.assertEqual( response.status_code, status.HTTP_200_OK )

    def test_traininig_failed_campaign_does_not_exist(self):
        url = reverse( views.ml_training_failed, kwargs = {'campaign_name': 'noCampaign'} )
        data = {}

        response = self.client.post(url, data, format='json')
        self.assertEqual( response.status_code, status.HTTP_404_NOT_FOUND )

    def test_traininig_failed(self):
        url = reverse( views.ml_training_failed, kwargs = self.uid_use )
        data = {}

        response = self.client.post(url, data, format='json')
        self.assertEqual( response.status_code, status.HTTP_200_OK )

############################################################
#
# test sending new proposed experiment
#
############################################################
@mock.patch('map_ml.views.celery_task')
class ProposeExperimentTests(MapAPITransactionTestCase):
    def setUp(self):
        super().setUp()
        self.input_dicts = [
                        {'name': 'parameter_1', 'value': 1.0},
                        {'name': 'parameter_2', 'value': 2.0},
                    ]
        self.map_inputs = [ MapInput.objects.create(for_map=self.test_map, name=inp['name'], min_val=0.0, max_val=10.0) for inp in self.input_dicts ]
        self.map_stage = MapStage.objects.create(for_map=self.test_map, name=self.base_uid['stage_name'])
        self.map_output = MapOutput.objects.create(for_map=self.test_map, name=self.base_uid['output_name'])

        self.uid_use = { 'campaign_name': self.base_uid['campaign_name'] }

    ##############################
    # POST
    ##############################
    def test_campaign_does_not_exist(self, mock_task):
        url = reverse( views.propose_experiment, kwargs = {'campaign_name': 'noCampaign'} )
        data = {
                'mode': 'random',
                'inputs': self.input_dicts,
                }

        response = self.client.post(url, data, format='json')
        self.assertEqual( response.status_code, status.HTTP_404_NOT_FOUND )

        mock_task.place_experiment.delay.assert_not_called()
        mock_task.place_experiment.apply_async.assert_not_called()

    def test_new_experiment(self,mock_task):
        url = reverse( views.propose_experiment, kwargs = self.uid_use )
        data = {
                'mode': 'random',
                'inputs': self.input_dicts,
                }

        response = self.client.post(url, data, format='json')
        self.assertContains( response, 'campaign_name', count=1, status_code=status.HTTP_200_OK )
        self.assertContains( response, 'experiment_name', count=1, status_code=status.HTTP_200_OK )
        self.assertContains( response, 'Experiment - {}'.format(data['mode']), count=1, status_code=status.HTTP_200_OK )

        # asyncronous task not called, but verify arguments
        mock_task.place_experiment.delay.assert_called_once_with(response.data['campaign_name'], response.data['experiment_name'])

    def test_unknown_input_name(self, mock_task):
        url = reverse( views.propose_experiment, kwargs = self.uid_use )
        data = {
                'mode': 'random',
                'inputs': [ {'name': 'mytery_parameter', 'value': 1.0} ]
                }

        response = self.client.post(url, data, format='json')
        self.assertEqual( response.status_code, status.HTTP_400_BAD_REQUEST )

        mock_task.place_experiment.delay.assert_not_called()
        mock_task.place_experiment.apply_async.assert_not_called()

    def test_value_out_of_bounds(self, mock_task):
        url = reverse( views.propose_experiment, kwargs = self.uid_use )
        data = {
                'mode': 'random',
                'inputs': [ {'name': self.input_dicts[0]['name'], 'value': -1.0} ]
                }

        response = self.client.post(url, data, format='json')
        self.assertEqual( response.status_code, status.HTTP_400_BAD_REQUEST )

        mock_task.place_experiment.delay.assert_not_called()
        mock_task.place_experiment.apply_async.assert_not_called()

#    def test_celery_new_experiment(self):
#        url = reverse( views.propose_experiment, kwargs = self.uid_use )
#        data = {
#                'mode': 'random',
#                'inputs': self.input_dicts,
#                }
#
#        response = self.client.post(url, data, format='json')
#        self.assertContains( response, 'campaign_name', count=1, status_code=status.HTTP_200_OK )
#        self.assertContains( response, 'experiment_name', count=1, status_code=status.HTTP_200_OK )
#        self.assertContains( response, 'Experiment - {}'.format(data['mode']), count=1, status_code=status.HTTP_200_OK )
#
#        # pause to give time for celery task to run before database destroyed
#        sleep(30)
