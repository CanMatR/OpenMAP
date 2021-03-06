from __future__ import absolute_import, unicode_literals
from celery import Task, shared_task
import requests
from surrogate_base.models import MiscConfig
from surrogate_base.models import ModuleOutVar
from surrogate_base.models import Experiment, ExpModuleInpVar, ExpOutVar
from surrogate_base.serializers import StatusSerializer

############################################################
#
############################################################
@shared_task(bind=True)
def calc_parabolic_2d(self, i0_name, i1_name, o_name, e_id, m_name):
    try:
        base_url = MiscConfig.objects.get(name='orchestrator_api_url').value
        token = MiscConfig.objects.get(name='orchestrator_api_token').value

        header = { "Authorization": "token {}".format(token) }
    except MiscConfig.DoesNotExist:
        return

    experiment = Experiment.objects.get(id=e_id)
    exp_module = experiment.modules.get(module__name=m_name)
    inp0 = ExpModuleInpVar.objects.get(exp_module__experiment=experiment, module_input__name=i0_name)
    inp1 = ExpModuleInpVar.objects.get(exp_module__experiment=experiment, module_input__name=i1_name)
    mout = ModuleOutVar.objects.get(name=o_name)

    c_name = experiment.campaign_name
    e_name = experiment.experiment_name

    url_exp_status = base_url + "experimentStatus/{}/{}/".format(c_name, e_name)
    url_mod_status = base_url + "stageStatus/{}/{}/{}/".format(c_name, e_name, m_name)
    url_inp0 = base_url + "input/{}/{}/{}/".format(c_name, e_name, i0_name)
    url_inp1 = base_url + "input/{}/{}/{}/".format(c_name, e_name, i1_name)
    url_out = base_url + "output/{}/{}/{}/".format(c_name, e_name, o_name)

    # send experiment running
    experiment.status= 'R'
    experiment.save()
    status_response = requests.post( url_exp_status, json=StatusSerializer(experiment).data, headers=header )
    # send stage queued
    exp_module.status = 'Q'
    exp_module.save()
    status_response = requests.post( url_mod_status, json=StatusSerializer(exp_module).data, headers=header )
    # send stage running
    exp_module.status = 'R'
    exp_module.save()
    status_response = requests.post( url_mod_status, json=StatusSerializer(exp_module).data, headers=header )

    result = inp0.input_value**2 + inp1.input_value**2
    out = ExpOutVar.objects.create(experiment=experiment, module_output=mout, output_value=result)

    # send stage complete
    exp_module.status = 'C'
    exp_module.save()
    status_response = requests.post( url_mod_status, json=StatusSerializer(exp_module).data, headers=header )
    # send input actuals
    data_i0 = {'value': inp0.input_value}
    data_i1 = {'value': inp1.input_value}
    status_response = requests.put( url_inp0, json=data_i0, headers=header )
    status_response = requests.put( url_inp1, json=data_i1, headers=header )
    # send output
    data_o = {'value': result}
    status_response = requests.put( url_out, json=data_o, headers=header )
    # send experiment complete
    experiment.status= 'C'
    experiment.save()
    status_response = requests.post( url_exp_status, json=StatusSerializer(experiment).data, headers=header )

    return result
