from django.contrib.auth.models import User
from rest_framework.test import APITestCase, APITransactionTestCase
from surrogate_base.models import Module, ModuleInpVar, ModuleOutVar
from surrogate_base.models import MiscConfig

class Surrogate2dTestCase(APITestCase):
    def setUp(self):
        self.setup_dict = {
                    'module_name': 'calc',
                    'inp': [ 'x0', 'x1' ],
                    'out': 'y',
                }

        self.module = Module.objects.create(name = self.setup_dict['module_name'])
        self.inputs = [ ModuleInpVar.objects.create(module=self.module, name=inp_name) for inp_name in self.setup_dict['inp'] ]
        self.output = ModuleOutVar.objects.create(module=self.module, name=self.setup_dict['out'])
        self.inputs_true = [ ModuleOutVar.objects.create(module=self.module, name=inp_name, inp_true=True) for inp_name in self.setup_dict['inp'] ]

        self.test_values = {
                    'experiment_name': 'test experiment',
                    'campaign_name': 'test campaign',
                    'test_inp': [
                            {'input_name': self.setup_dict['inp'][0], 'input_value': 3.0},
                            {'input_name': self.setup_dict['inp'][1], 'input_value': 4.0},
                        ],
                    'test_out': {'output_name': self.setup_dict['out'], 'output_value': 25.0},
                    'orch_url': 'placeholder',
                    'orch_token': 'placeholder',
                }

    def confOrch(self):
        self.orch_url = MiscConfig.objects.create(name='orchestrator_api_url', value=self.test_values['orch_url'])
        self.orch_token = MiscConfig.objects.create(name='orchestrator_api_token', value=self.test_values['orch_token'])
