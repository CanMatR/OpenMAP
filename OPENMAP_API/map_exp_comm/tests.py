from django.urls import reverse
from django.contrib.auth.models import User

from rest_framework.test import APITestCase
from rest_framework import status

from unittest import mock

from map_exp_comm import views
from map_base.models import MapStage, MapInput, MapOutput
from map_base.models import Campaign, Experiment, ExpStage, ExpInputVal, ExpOutputVal
from map_base.tests import MapAPITestCase

############################################################
#
# test updating experiment status
#
############################################################
@mock.patch('map_exp_comm.views.celery_task')
class ExperimentStatusTests(MapAPITestCase):

    def setUp(self):
        MapAPITestCase.setUp(self)
        self.experiment = Experiment.objects.create( campaign=self.campaign, name=self.base_uid['experiment_name'] )

        self.uid_use = { 'campaign_name': self.base_uid['campaign_name'], 'experiment_name': self.base_uid['experiment_name'] }

    ##############################
    # POST
    ##############################
    def test_experiment_does_not_exist(self, mock_task):
        url = reverse( views.experiment_status, kwargs = {'campaign_name': 'api_testing', 'experiment_name': 'noExperiment'} )
        data = { 'status': 'Running' }

        response = self.client.post(url, data, format='json')
        self.assertEqual( response.status_code, status.HTTP_404_NOT_FOUND )

        mock_task.monitor_experiment_status.signature.assert_not_called()

    def test_experiment_status_by_display(self, mock_task):
        url = reverse( views.experiment_status, kwargs = self.uid_use )
        data = { 'status': 'Running' }

        response = self.client.post(url, data, format='json')
        self.assertEqual( response.status_code, status.HTTP_200_OK )

        experiment = Experiment.objects.get( campaign__name=self.uid_use['campaign_name'], name=self.uid_use['experiment_name'] )
        self.assertEqual( experiment.status, 'R' )
        self.assertEqual( experiment.get_status_display(), 'Running' )

        mock_task.monitor_experiment_status.signature.assert_called_once()

    def test_experiment_status_by_value(self, mock_task):
        url = reverse( views.experiment_status, kwargs = self.uid_use )
        data = { 'status': 'R' }

        response = self.client.post(url, data, format='json')
        self.assertEqual( response.status_code, status.HTTP_200_OK )

        experiment = Experiment.objects.get( campaign__name=self.uid_use['campaign_name'], name=self.uid_use['experiment_name'] )
        self.assertEqual( experiment.status, 'R' )
        self.assertEqual( experiment.get_status_display(), 'Running' )

        mock_task.monitor_experiment_status.signature.assert_called_once()

    def test_experiment_status_bad_display(self, mock_task):
        url = reverse( views.experiment_status, kwargs = self.uid_use )
        data = { 'status': 'Garbage' }

        response = self.client.post(url, data, format='json')
        self.assertEqual( response.status_code, status.HTTP_400_BAD_REQUEST )

        experiment = Experiment.objects.get( campaign__name=self.uid_use['campaign_name'], name=self.uid_use['experiment_name'] )
        self.assertEqual( experiment.status, 'P' )
        self.assertEqual( experiment.get_status_display(), 'Proposed' )

        mock_task.monitor_experiment_status.signature.assert_not_called()

    def test_experiment_status_bad_value(self, mock_task):
        url = reverse( views.experiment_status, kwargs = self.uid_use )
        data = { 'status': 'G' }

        response = self.client.post(url, data, format='json')
        self.assertEqual( response.status_code, status.HTTP_400_BAD_REQUEST )

        experiment = Experiment.objects.get( campaign__name=self.uid_use['campaign_name'], name=self.uid_use['experiment_name'] )
        self.assertEqual( experiment.status, 'P' )
        self.assertEqual( experiment.get_status_display(), 'Proposed' )

        mock_task.monitor_experiment_status.signature.assert_not_called()

    def test_experiment_completed(self, mock_task):
        self.experiment.status = 'R'
        self.experiment.save()

        url = reverse( views.experiment_status, kwargs = self.uid_use )
        data = { 'status': 'C' }

        response = self.client.post(url, data, format='json')
        self.assertEqual( response.status_code, status.HTTP_200_OK )

        experiment = Experiment.objects.get( campaign__name=self.uid_use['campaign_name'], name=self.uid_use['experiment_name'] )
        self.assertEqual( experiment.status, 'C' )
        self.assertEqual( experiment.get_status_display(), 'Completed' )

        mock_task.monitor_experiment_status.signature.assert_called_once_with( (self.uid_use['campaign_name'], self.uid_use['experiment_name'], data['status']), ignore_result=False, immutable=True )
        mock_task.update_model.si.assert_called_once_with(self.uid_use['campaign_name'])


############################################################
#
# test updating stage status
#
############################################################
@mock.patch('map_exp_comm.views.celery_task')
class StageStatusTests(MapAPITestCase):

    def setUp(self):
        MapAPITestCase.setUp(self)
        map_stg = MapStage.objects.create( for_map=self.test_map, name=self.base_uid['stage_name'] )
        self.experiment = Experiment.objects.create( campaign=self.campaign, name=self.base_uid['experiment_name'] )
        self.stage = ExpStage.objects.create( experiment=self.experiment, map_stage=map_stg )

        self.uid_use = {
                    'campaign_name': self.base_uid['campaign_name'],
                    'experiment_name': self.base_uid['experiment_name'],
                    'stage_name': self.base_uid['stage_name']
                }

    ##############################
    # POST
    ##############################
    def test_stage_does_not_exist(self, mock_task):
        url = reverse( views.stage_status,
                        kwargs = {
                            'campaign_name': 'api_testing',
                            'experiment_name': 'noExperiment',
                            'stage_name': 'noStage'
                            }
                        )
        data = { 'status': 'Running' }

        response = self.client.post(url, data, format='json')
        self.assertEqual( response.status_code, status.HTTP_404_NOT_FOUND )

        mock_task.monitor_stage_status.apply_async.assert_not_called()

    def test_stage_status_by_display(self, mock_task):
        url = reverse( views.stage_status, kwargs = self.uid_use )
        data = { 'status': 'Running' }

        response = self.client.post(url, data, format='json')
        self.assertEqual( response.status_code, status.HTTP_200_OK )

        stage = ExpStage.objects.get( experiment__campaign__name=self.uid_use['campaign_name'],
                                        experiment__name=self.uid_use['experiment_name'],
                                        map_stage__name=self.uid_use['stage_name']
                                    )
        self.assertEqual( stage.status, 'R' )
        self.assertEqual( stage.get_status_display(), 'Running' )

        mock_task.monitor_stage_status.apply_async.assert_called_once()

    def test_stage_status_by_value(self, mock_task):
        url = reverse( views.stage_status, kwargs = self.uid_use )
        data = { 'status': 'R' }

        response = self.client.post(url, data, format='json')
        self.assertEqual( response.status_code, status.HTTP_200_OK )

        stage = ExpStage.objects.get( experiment__campaign__name=self.uid_use['campaign_name'],
                                        experiment__name=self.uid_use['experiment_name'],
                                        map_stage__name=self.uid_use['stage_name']
                                    )
        self.assertEqual( stage.status, 'R' )
        self.assertEqual( stage.get_status_display(), 'Running' )

        mock_task.monitor_stage_status.apply_async.assert_called_once()

    def test_stage_status_bad_display(self, mock_task):
        url = reverse( views.stage_status, kwargs = self.uid_use )
        data = { 'status': 'Garbage' }

        response = self.client.post(url, data, format='json')
        self.assertEqual( response.status_code, status.HTTP_400_BAD_REQUEST )

        stage = ExpStage.objects.get( experiment__campaign__name=self.uid_use['campaign_name'],
                                        experiment__name=self.uid_use['experiment_name'],
                                        map_stage__name=self.uid_use['stage_name']
                                    )
        self.assertEqual( stage.status, 'P' )
        self.assertEqual( stage.get_status_display(), 'Proposed' )

        mock_task.monitor_stage_status.apply_async.assert_not_called()

    def test_stage_status_bad_value(self, mock_task):
        url = reverse( views.stage_status, kwargs = self.uid_use )
        data = { 'status': 'G' }

        response = self.client.post(url, data, format='json')
        self.assertEqual( response.status_code, status.HTTP_400_BAD_REQUEST )

        stage = ExpStage.objects.get( experiment__campaign__name=self.uid_use['campaign_name'],
                                        experiment__name=self.uid_use['experiment_name'],
                                        map_stage__name=self.uid_use['stage_name']
                                    )
        self.assertEqual( stage.status, 'P' )
        self.assertEqual( stage.get_status_display(), 'Proposed' )

        mock_task.monitor_stage_status.apply_async.assert_not_called()

    def test_stage_completed(self, mock_task):
        self.stage.status = 'R'
        self.stage.save()

        url = reverse( views.stage_status, kwargs = self.uid_use )
        data = { 'status': 'C' }

        response = self.client.post(url, data, format='json')
        self.assertEqual( response.status_code, status.HTTP_200_OK )

        stage = ExpStage.objects.get( experiment__campaign__name=self.uid_use['campaign_name'],
                                        experiment__name=self.uid_use['experiment_name'],
                                        map_stage__name=self.uid_use['stage_name']
                                    )
        self.assertEqual( stage.status, 'C' )
        self.assertEqual( stage.get_status_display(), 'Completed' )

        mock_task.monitor_stage_status.apply_async.assert_called_once_with(
                    (self.uid_use['campaign_name'], self.uid_use['experiment_name'], self.uid_use['stage_name'], data['status']), countdown=10
                )

############################################################
#
# test input values
#
############################################################
class ExpInputValTests(MapAPITestCase):

    def setUp(self):
        MapAPITestCase.setUp(self)
        self.map_input = MapInput.objects.create( for_map=self.test_map, name=self.base_uid['input_name'], min_val=0.0, max_val=10.0 )
        self.experiment = Experiment.objects.create( campaign=self.campaign, name=self.base_uid['experiment_name'] )
        self.input = ExpInputVal.objects.create( experiment=self.experiment, map_input=self.map_input, value_request=3.14 )
        self.uid_use = {
                    'campaign_name': self.base_uid['campaign_name'],
                    'experiment_name': self.base_uid['experiment_name'],
                    'input_name': self.base_uid['input_name']
                }


    ##############################
    # PUT
    ##############################
    def test_put_expinp_does_not_exist(self):
        url = reverse( views.input_value,
                kwargs = {
                    'campaign_name': self.uid_use['campaign_name'],
                    'experiment_name': self.uid_use['experiment_name'],
                    'input_name': 'noInp'
                    }
                )
        data = { 'value': 3.14159 }

        response = self.client.put(url, data, format='json')
        self.assertEqual( response.status_code, status.HTTP_404_NOT_FOUND )

    def test_put_expinp_exists(self):
        url = reverse( views.input_value, kwargs = self.uid_use)
        data = { 'value': 3.14159 }

        response = self.client.put(url, data, format='json')
        self.assertEqual( response.status_code, status.HTTP_200_OK )

        expinp = ExpInputVal.objects.get( experiment=self.experiment, map_input__name=self.uid_use['input_name'] )
        self.assertEqual( expinp.value_request, 3.14 )
        self.assertEqual( expinp.value_actual, data['value'] )

############################################################
#
# test output values
#
############################################################
class ExpOutputValTests(MapAPITestCase):

    def setUp(self):
        MapAPITestCase.setUp(self)
        self.map_output1 = MapOutput.objects.create( for_map=self.test_map, name=self.base_uid['output_name'] )
        self.map_output2 = MapOutput.objects.create( for_map=self.test_map, name='measure2' )
        self.experiment = Experiment.objects.create( campaign=self.campaign, name=self.base_uid['experiment_name'] )

        self.uid_use = {
                    'campaign_name': self.base_uid['campaign_name'],
                    'experiment_name': self.base_uid['experiment_name'],
                }

    ##############################
    # POST
    ##############################
    def test_post_experiment_does_not_exist(self):
        url = reverse( views.output_values,
                kwargs = {
                    'campaign_name': self.uid_use['campaign_name'],
                    'experiment_name': 'noExperiment',
                    }
                )
        data = [ { 'name': 'measure1', 'value': 3.14159 } ]

        response = self.client.post(url, data, format='json')
        self.assertEqual( response.status_code, status.HTTP_404_NOT_FOUND )

    def test_post_experiment_1_output(self):
        url = reverse( views.output_values, kwargs = self.uid_use )
        data = [ { 'name': 'measure1', 'value': 3.14159 } ]

        response = self.client.post(url, data, format='json')
        self.assertEqual( response.status_code, status.HTTP_200_OK )

        expout = ExpOutputVal.objects.get(experiment=self.experiment, map_output__name=data[0]['name'])
        self.assertEqual( expout.value, data[0]['value'] )

    def test_post_experiment_2_output(self):
        url = reverse( views.output_values, kwargs = self.uid_use )
        data = [ { 'name': 'measure1', 'value': 3.14159 }, { 'name': 'measure2', 'value': 6.28318} ]

        response = self.client.post(url, data, format='json')
        self.assertEqual( response.status_code, status.HTTP_200_OK )

        expout_count = ExpOutputVal.objects.filter(experiment=self.experiment).count()
        self.assertEqual( expout_count, 2 )
        
        for out_sent in data:
            expout = ExpOutputVal.objects.get(experiment=self.experiment, map_output__name=out_sent['name'])
            self.assertEqual( expout.value, out_sent['value'] )

    def test_post_experiment_not_float(self):
        url = reverse( views.output_values, kwargs = self.uid_use )
        data = [ { 'name': 'measure1', 'value': 'pi' } ]

        response = self.client.post(url, data, format='json')
        self.assertEqual( response.status_code, status.HTTP_400_BAD_REQUEST )

    def test_post_experiment_overwrite_existing(self):
        url = reverse( views.output_values, kwargs = self.uid_use )
        data = [ { 'name': 'measure1', 'value': 3.14159 } ]

        old_expout = ExpOutputVal.objects.create(experiment=self.experiment, map_output=self.map_output1, value=6.28318)

        response = self.client.post(url, data, format='json')
        self.assertEqual( response.status_code, status.HTTP_200_OK )

        expout = ExpOutputVal.objects.get(experiment=self.experiment, map_output__name=data[0]['name'])
        self.assertEqual( expout.value, data[0]['value'] )

    def test_post_experiment_1_nonlist(self):
        url = reverse( views.output_values, kwargs = self.uid_use )
        data = { 'name': 'measure1', 'value': 3.14159 }

        response = self.client.post(url, data, format='json')
        self.assertEqual( response.status_code, status.HTTP_400_BAD_REQUEST )

    def test_post_experiment_unknown_output(self):
        url = reverse( views.output_values, kwargs = self.uid_use )
        data = [ { 'name': 'measure1', 'value': 3.14159 }, { 'name': 'garbage', 'value': 6.28318} ]

        response = self.client.post(url, data, format='json')
        self.assertEqual( response.status_code, status.HTTP_400_BAD_REQUEST )

class ExpSingleOutputValTests(APITestCase):

    def setUp(self):
        MapAPITestCase.setUp(self)
        self.map_output = MapOutput.objects.create( for_map=self.test_map, name=self.base_uid['output_name'] )
        self.experiment = Experiment.objects.create( campaign=self.campaign, name=self.base_uid['experiment_name'] )
        self.expout = ExpOutputVal.objects.create( experiment=self.experiment, map_output=self.map_output )

        self.uid_use = {
                    'campaign_name': self.base_uid['campaign_name'],
                    'experiment_name': self.base_uid['experiment_name'],
                    'output_name': self.base_uid['output_name']
                }

    ##############################
    # PUT
    ##############################
    def test_post_expout_does_not_exist(self):
        url = reverse( views.output_value,
                kwargs = {
                    'campaign_name': self.uid_use['campaign_name'],
                    'experiment_name': self.uid_use['experiment_name'],
                    'output_name': 'noOut'
                    }
                )
        data = { 'value': 3.14159 }

        response = self.client.put(url, data, format='json')
        self.assertEqual( response.status_code, status.HTTP_404_NOT_FOUND )

    def test_post_expout_exists(self):
        url = reverse( views.output_value, kwargs = self.uid_use )
        data = { 'value': 3.14159 }

        response = self.client.put(url, data, format='json')
        self.assertEqual( response.status_code, status.HTTP_200_OK )

        expout = ExpOutputVal.objects.get(experiment=self.experiment, map_output__name=self.uid_use['output_name'])
        self.assertEqual( expout.value, data['value'] )

    def test_post_expout_no_sent_value(self):
        url = reverse( views.output_value, kwargs = self.uid_use )
        data = { 'garbage': 3.14159 }

        response = self.client.put(url, data, format='json')
        self.assertEqual( response.status_code, status.HTTP_400_BAD_REQUEST )
