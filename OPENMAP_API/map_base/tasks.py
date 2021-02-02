from __future__ import absolute_import, unicode_literals
from celery import shared_task, Task
from celery.exceptions import TaskError
import requests
from paramiko import SSHClient

from django.conf import settings

from rest_framework.status import HTTP_200_OK, HTTP_201_CREATED

from map_base.models import Campaign, Experiment, ExpStage, ExpInputVal, ExpOutputVal
from map_base.models import MapFacility
from map_base.serializers import StageStatusSerializer, ExperimentStatusSerializer

############################################################
#  custom task exceptions
############################################################
class RedundantTask(TaskError):
    """The current state indicates that a more recent task should have been generated which renders this task redundant."""

############################################################
#  custom task classes
############################################################
class ExpectedOutputTask(Task):
    max_retries = None
    default_retry_delay = {'countdown': 2*60}
    retry_backoff = True
    retry_backoff_max = 60*30

############################################################
#   
############################################################
@shared_task(bind=True, ignore_result=True)
def monitor_training_status(self, campaign_name, status):
    continue_monitoring = False
    campaign = Campaign.objects.get(name=campaign_name)

    if (campaign.ml_model_status == status):
        # check for change of status, possible problems
        pass
    else:
        # end monitoring or respond to new status
        pass

    if ( continue_monitoring ):
        self.retry()

############################################################
#   
############################################################
@shared_task(bind=True, ignore_result=True)
def probe_model(self, campaign_name):
    campaign = Campaign.objects.get(name=campaign_name)
    ml_host = campaign.with_ml.location
    probe_command = campaign.with_ml.probe_script
    model_name = campaign.uid_node
    db_name = settings.DATABASES['default']['NAME']
    num_samples = 1                     # hardcoded until scheme for determining how many to multi-select
    api_base = 'http://localhost:8000/ml-api/' # hardcoded for testing

    ssh = SSHClient()
    ssh.load_system_host_keys()
    ssh.connect(ml_host)

    stdin, stdout, stderr = ssh.exec_command('{} "{}" {} {} {} {}'.format(probe_command, campaign_name, model_name, db_name, num_samples, api_base))

    ssh.close()

############################################################
#   
############################################################
@shared_task(bind=True, ignore_result=True)
def update_model(self, campaign_name):
    campaign = Campaign.objects.get(name=campaign_name)
    ml_host = campaign.with_ml.location
    train_command = campaign.with_ml.train_script
    model_name = campaign.uid_node
    db_name = settings.DATABASES['default']['NAME']
    api_base = 'http://localhost:8000/ml-api/' # hardcoded for testing

    if ( campaign.ml_model_status in [ "R", "T" ] ):
        # don't bother if already updating model or just updated
        return # possibly change to raising an exception to prevent followups in a chain?
    else:
        campaign.ml_model_status = "R"
        campaign.save()

        ssh = SSHClient()
        ssh.load_system_host_keys()
        ssh.connect(ml_host)

        stdin, stdout, stderr = ssh.exec_command('{} "{}" {} {} {}'.format(train_command, campaign_name, model_name, db_name, api_base))

        ssh.close()

############################################################
#   send new experiment to a facility
############################################################
@shared_task(bind=True, ignore_result=True)
def place_experiment(self, campaign_name, experiment_name):
    placed = False

    experiment = Experiment.objects.get(campaign__name=campaign_name, name=experiment_name)
    exp_uid = { 'experiment_name': experiment_name, 'campaign_name': campaign_name }

    for facility in MapFacility.objects.all():
        url_new_experiment = facility.location + 'experiment/new/'

        new_exp_response = requests.post( url_new_experiment, json=exp_uid )
        if ( new_exp_response.status_code == HTTP_201_CREATED ):
            placed = True
            experiment.facility = facility
            experiment.facility_expid = new_exp_response.json()['id']
            experiment.status = 'Q'
            experiment.save()

            # facilty expects input values to be provided stage-by-stage
            for stage in experiment.stages.all():
                url_inp = facility.location + 'experiment/{}/config/{}/'.format(experiment.facility_expid, stage.map_stage.name)
                stage_inputs = experiment.input_values.filter(map_input__for_stage__name=stage.map_stage.name)
                inp_data = [ {'input_name': i.map_input.name, 'input_value': i.value_request} for i in stage_inputs ]

                stage_config_response = requests.post( url_inp, json=inp_data )
                # if ( stage_config_response != HTTP_200_OK )
                    # respond to status code

            url_queue = facility.location + 'queue/append/'
            queue_data = { 'id': experiment.facility_expid }

            queue_response = requests.post( url_queue, json=queue_data )
            #if ( queue_response.status_code == sHTTP_200_OK ):
                # trigger status monitoring
            #else:
                # respond to alternate status codes


            # don't need to check additional facilities
            break

    if not placed:
        self.retry()

############################################################
# if stage has completed
#   check if haven't received expected stage outputs
#   and request them
#
#   DEPRECATED
#
############################################################
@shared_task(bind=True, ignore_result=True, base=ExpectedOutputTask)
def stage_complete_check_expected_returns(self, campaign_name, experiment_name, stage_name):
    ask_again = False
    experiment = Experiment.objects.get(campaign__name=campaign_name, name=experiment_name)

    awaiting_real_inputs = ExpInputVal.objects.filter( experiment=experiment, map_input__for_stage__name=stage_name, value_actual=None )
    for real_input_ask in awaiting_real_inputs:
        # request value from experiment.facility
        # if ( fail to receive valid value ):
        #   ask_again = True
        pass

    awaiting_outputs = ExpOutputVal.objects.filter( experiment=experiment, map_output__from_stage__name=stage_name, value=None )
    for output_ask in awaiting_outputs:
        # request value from experiment.facility
        # if ( fail to receive valid value ):
        #   ask_again = True
        pass

    if ( ask_again ):
        self.retry()

############################################################
# if experiment has completed
#   check if haven't received expected experiment outputs
#   and request them
#
#   DEPRECATED
#
############################################################
@shared_task(bind=True, ignore_result=True, base=ExpectedOutputTask)
def experiment_complete_check_expected_returns(self, campaign_name, experiment_name):
    ask_again = False
    experiment = Experiment.objects.get(campaign__name=campaign_name, name=experiment_name)

    awaiting_real_inputs = ExpInputVal.objects.filter( experiment=experiment, value_actual=None )
    for real_input_ask in awaiting_real_inputs:
        # request value from experiment.facility
        # if ( fail to receive valid value ):
        #   ask_again = True
        pass

    awaiting_outputs = ExpOutputVal.objects.filter( experiment=experiment, value=None )
    for output_ask in awaiting_outputs:
        # request value from experiment.facility
        # if ( fail to receive valid value ):
        #   ask_again = True
        ask_again = True

    if ( ask_again ):
        self.retry()
    else:
        campaign = Campaign.objects.get(name=campaign_name)
        campaign.ml_model_status = "O"
        campaign.save()

############################################################
# monitor experiment for unusual time in status
############################################################
@shared_task(bind=True, ignore_result=True, max_retries=None, throws=(RedundantTask,))
def monitor_experiment_status(self, campaign_name, experiment_name, status):
    continue_monitoring = False
    experiment = Experiment.objects.get(campaign__name=campaign_name, name=experiment_name)

    if ( status == 'C' ):
        #
        # should be final status
        # monitor a Complete experiment until all inputs have real values and all outputs have values
        #
        awaiting_real_inputs = ExpInputVal.objects.filter( experiment=experiment, value_actual=None )
        awaiting_outputs = ExpOutputVal.objects.filter( experiment=experiment, value=None )

        if ( len(awaiting_real_inputs) > 0 or len(awaiting_outputs) > 0 ):
            received_results = {}
            for stage in experiment.stages.all():
                url_results = stage.experiment.facility.location + 'experiment/{}/results/{}/'.format(experiment.facility_expid, stage.map_stage.name)
                response = requests.get( url_results )
                received_results.update( response.json() )

        for real_input_ask in awaiting_real_inputs:
            # request value from experiment.facility
            # if ( fail to receive valid value ):
            #   ask_again = True
            if ( real_input_ask.map_input.name in received_results ):
                real_input_ask.value_actual = received_results[real_input_ask.map_input.name]
                real_input_ask.save()
            else:
                continue_monitoring = True

        for output_ask in awaiting_outputs:
            # request value from experiment.facility
            # if ( fail to receive valid value ):
            #   ask_again = True
            if ( output_ask.map_output.name in received_results ):
                output_ask.value = received_results[output_ask.map_output.name]
                output_ask.save()
            else:
                continue_monitoring = True

        if ( continue_monitoring ):
            raise self.retry()
        else:
            campaign = Campaign.objects.get(name=campaign_name)
            campaign.ml_model_status = "O"
            campaign.save()

    else:
        if ( experiment.status == status ):
            # contact facility to check for change of status, possible problems
            url_status = experiment.facility.location + 'experiment/{}/status/'.format(experiment.facility_expid)
            response = requests.get( url_status )
            if (response.status_code == HTTP_200_OK):
                res_serializer = ExperimentStatusSerializer(experiment, data=response.json())
                if res_serializer.is_valid():
                    updated_experiment = res_serializer.save()

                    if ( updated_experiment.status != status ):
                        raise self.retry( (campaign_name, experiment_name, updated_experiment.status) )

            raise self.retry()
        else:
            # if the experiment status was changed outside of this task, it should have triggered new monitoring
            # to avoid duplication, let this one end
            raise RedundantTask()

############################################################
# monitor stage for unusual time in status
############################################################
@shared_task(bind=True, ignore_result=True, max_retries=None, throws=(RedundantTask,))
def monitor_stage_status(self, campaign_name, experiment_name, stage_name, status):
    continue_monitoring = False
    stage = ExpStage.objects.get(experiment__campaign__name=campaign_name, experiment__name=experiment_name, map_stage__name=stage_name)

    if ( status == 'C' ):
        #
        # should be final status
        # monitor a Complete stage until all inputs have real values and all outputs have values
        #
        awaiting_real_inputs = ExpInputVal.objects.filter( map_input__for_stage=stage.map_stage, value_actual=None )
        awaiting_outputs = ExpOutputVal.objects.filter( map_output__from_stage=stage.map_stage, value=None )

        if ( len(awaiting_real_inputs) > 0 or len(awaiting_outputs) > 0 ):
            url_results = stage.experiment.facility.location + 'experiment/{}/results/{}/'.format(stage.experiment.facility_expid, stage_name)
            response = requests.get( url_results )
            received_results = response.json()

        for real_input_ask in awaiting_real_inputs:
            # request value from experiment.facility
            # if ( fail to receive valid value ):
            #   ask_again = True
            if ( real_input_ask.map_input.name in received_results ):
                real_input_ask.value_actual = received_results[real_input_ask.map_input.name]
                real_input_ask.save()
            else:
                continue_monitoring = True

        for output_ask in awaiting_outputs:
            # request value from experiment.facility
            # if ( fail to receive valid value ):
            #   ask_again = True
            if ( output_ask.map_output.name in received_results ):
                output_ask.value = received_results[output_ask.map_output.name]
                output_ask.save()
            else:
                continue_monitoring = True

        if ( continue_monitoring ):
            raise self.retry()

    else:
        if ( stage.status == status ):
            # contact facility to check for change of status, possible problems
            url_status = stage.experiment.facility.location + 'experiment/{}/status/{}/'.format(stage.experiment.facility_expid, stage_name)
            response = requests.get( url_status )
            if (response.status_code == HTTP_200_OK):
                res_serializer = StageStatusSerializer(stage, data=response.json())
                if res_serializer.is_valid():
                    updated_stage = res_serializer.save()

                    if ( updated_stage.status != status ):
                        raise self.retry( (campaign_name, experiment_name, stage_name, updated_stage.status) )

            raise self.retry()
        else:
            # if the stage status was changed outside of this task, it should have triggered new monitoring
            # to avoid duplication, let this one end
            raise RedundantTask()
