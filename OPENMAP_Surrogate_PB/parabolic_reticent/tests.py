from django.urls import reverse

from rest_framework import status

from unittest import mock

from surrogate_base.tests import Surrogate2dTestCase
from surrogate_base.models import ModuleInpVar, ModuleOutVar
from surrogate_base.models import Experiment, ExpModule, ExpModuleInpVar, ExpOutVar
from parabolic_reticent import views

############################################################
#
# test new experiment
#
############################################################
class NewExperimentTests(Surrogate2dTestCase):

    def setUp(self):
        super().setUp()

    def test_new_experiment_no_orch(self):
        url = reverse( views.new_experiment )
        data = {
                'experiment_name': self.test_values['experiment_name'],
                'campaign_name': self.test_values['campaign_name'],
                }

        response = self.client.post(url, data, format='json')
        self.assertEqual( response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR )

    def test_new_experiment_missing_field(self):
        self.confOrch()

        url = reverse( views.new_experiment )
        data = {
                'experiment_name': self.test_values['experiment_name'],
                'garbage': 'garbage',
                }

        response = self.client.post(url, data, format='json')
        self.assertEqual( response.status_code, status.HTTP_400_BAD_REQUEST )

    def test_new_experiment(self):
        self.confOrch()

        url = reverse( views.new_experiment )
        data = {
                'experiment_name': self.test_values['experiment_name'],
                'campaign_name': self.test_values['campaign_name'],
                }

        response = self.client.post(url, data, format='json')
        self.assertEqual( response.status_code, status.HTTP_201_CREATED )
        
        experiment_id = response.data['id']
        experiment = Experiment.objects.get(id=experiment_id)
        self.assertEqual( experiment.experiment_name, data['experiment_name'] )
        self.assertEqual( experiment.campaign_name, data['campaign_name'] )

############################################################
#
# test setting input parameters
#
############################################################
class ExpInpTests(Surrogate2dTestCase):

    def setUp(self):
        super().setUp()

        self.experiment = Experiment.objects.create(experiment_name=self.test_values['experiment_name'], campaign_name=self.test_values['campaign_name'])
        self.exp_module = ExpModule.objects.create(experiment=self.experiment, module=self.module)

    def test_set_inputs(self):
        self.confOrch()

        url = reverse( views.module_config, kwargs={'exp_id': self.experiment.id, 'module': self.module.name} )
        data = self.test_values['test_inp']

        response = self.client.post(url, data, format='json')
        self.assertEqual( response.status_code, status.HTTP_200_OK )

        for inp in data:
            expinp = ExpModuleInpVar.objects.get(exp_module=self.exp_module, module_input__name=inp['input_name'])
            self.assertEqual( expinp.input_value, inp['input_value'] )

    def test_set_inputs_plus_garbage(self):
        self.confOrch()

        url = reverse( views.module_config, kwargs={'exp_id': self.experiment.id, 'module': self.module.name} )
        data = self.test_values['test_inp']
        data.append( {'input_name': 'garbage', 'input_value': 5.0} )

        response = self.client.post(url, data, format='json')
        self.assertContains( response, "is not a known input", status_code=status.HTTP_400_BAD_REQUEST )

############################################################
#
# test append queue (mocking celery task)
#
############################################################
@mock.patch('parabolic_reticent.views.celery_task')
class ExpQueueTests(Surrogate2dTestCase):

    def setUp(self):
        super().setUp()

        self.experiment = Experiment.objects.create(experiment_name=self.test_values['experiment_name'], campaign_name=self.test_values['campaign_name'])
        self.exp_module = ExpModule.objects.create(experiment=self.experiment, module=self.module)
        self.exp_inp = [
                            ExpModuleInpVar.objects.create( exp_module = self.exp_module,
                                                            module_input = ModuleInpVar.objects.get(name=test_inp['input_name']),
                                                            input_value = test_inp['input_value']
                                                          )
                            for test_inp in self.test_values['test_inp']
                       ]

    def test_queue_orchestrator_unconfigured(self, mock_task):
        url = reverse( views.queue_append )
        data = { 'id': self.experiment.id }

        response = self.client.post(url, data, format='json')

        self.assertEqual( response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR )
        mock_task.calc_parabolic_2d.delay.assert_not_called()

    def test_no_experiment(self, mock_task):
        self.confOrch()

        url = reverse( views.queue_append )
        data = { 'id': 'garbage' }

        response = self.client.post(url, data, format='json')

        self.assertEqual( response.status_code, status.HTTP_400_BAD_REQUEST )
        mock_task.calc_parabolic_2d.delay.assert_not_called()

    def test_queue(self, mock_task):
        self.confOrch()

        url = reverse( views.queue_append )
        data = { 'id': self.experiment.id }

        response = self.client.post(url, data, format='json')

        self.assertEqual( response.status_code, status.HTTP_200_OK )
        mock_task.calc_parabolic_2d.delay.assert_called_once()

############################################################
#
# test getting experiment and module status
#
############################################################
class StatusTests(Surrogate2dTestCase):

    def setUp(self):
        super().setUp()

        self.experiment = Experiment.objects.create(experiment_name=self.test_values['experiment_name'], campaign_name=self.test_values['campaign_name'])
        self.exp_module = ExpModule.objects.create(experiment=self.experiment, module=self.module)
        self.exp_inp = [
                            ExpModuleInpVar.objects.create( exp_module = self.exp_module,
                                                            module_input = ModuleInpVar.objects.get(name=test_inp['input_name']),
                                                            input_value = test_inp['input_value']
                                                          )
                            for test_inp in self.test_values['test_inp']
                       ]

    def test_experiment_status(self):
        url = reverse( views.experiment_status, kwargs={'exp_id': self.experiment.id} )
        response = self.client.get(url, format='json')
        self.assertEqual( response.status_code, status.HTTP_200_OK )

    def test_module_status(self):
        url = reverse( views.module_status, kwargs={'exp_id': self.experiment.id, 'module': self.module.name} )
        response = self.client.get(url, format='json')
        self.assertEqual( response.status_code, status.HTTP_200_OK )

############################################################
#
# test getting experiment and module status
#
############################################################
class ResultsTests(Surrogate2dTestCase):
    def setUp(self):
        super().setUp()

        self.experiment = Experiment.objects.create(experiment_name=self.test_values['experiment_name'], campaign_name=self.test_values['campaign_name'])
        self.exp_module = ExpModule.objects.create(experiment=self.experiment, module=self.module)
        self.exp_inp = [
                            ExpModuleInpVar.objects.create( exp_module = self.exp_module,
                                                            module_input = ModuleInpVar.objects.get(name=test_inp['input_name']),
                                                            input_value = test_inp['input_value']
                                                          )
                            for test_inp in self.test_values['test_inp']
                       ]
        self.exp_inp_true = [
                            ExpOutVar.objects.create( experiment = self.experiment,
                                                      module_output = ModuleOutVar.objects.get(name=test_inp['input_name']),
                                                      output_value = test_inp['input_value']
                                                    )
                            for test_inp in self.test_values['test_inp']
                            ]
        self.exp_out = ExpOutVar.objects.create( experiment = self.experiment,
                                                 module_output = ModuleOutVar.objects.get(name=self.test_values['test_out']['output_name']),
                                                 output_value = self.test_values['test_out']['output_value']
                                               )

    def test_get_module_result(self):
        url = reverse( views.module_results, kwargs={'exp_id': self.experiment.id, 'module': self.module.name} )
        response = self.client.get(url, format='json')

        expected = {self.test_values['test_out']['output_name']: self.test_values['test_out']['output_value']}
        for test_inp in self.test_values['test_inp']:
            expected.update( { '{}'.format(test_inp['input_name']): test_inp['input_value'] } )

        self.assertEqual( response.status_code, status.HTTP_200_OK )
        self.assertEqual( response.json(), expected )

    def test_get_experiment_result(self):
        url = reverse( views.experiment_results, kwargs={'exp_id': self.experiment.id} )
        response = self.client.get(url, format='json')

        expected = {self.test_values['test_out']['output_name']: self.test_values['test_out']['output_value']}
        for test_inp in self.test_values['test_inp']:
            expected.update( { '{}'.format(test_inp['input_name']): test_inp['input_value'] } )

        self.assertEqual( response.status_code, status.HTTP_200_OK )
        self.assertEqual( response.json(), expected )
