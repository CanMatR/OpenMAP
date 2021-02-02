from django.shortcuts import render

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.decorators import authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.permissions import IsAuthenticated

from surrogate_base.models import Experiment, ExpModule, ExpOutVar
from surrogate_base.serializers import NewExperimentSerializer, IdSerializer
from surrogate_base.serializers import ModuleConfigSerializer
from surrogate_base.serializers import StatusSerializer
from surrogate_base.serializers import OutputSerializer

from surrogate_base.models import MiscConfig
import parabolic.tasks as celery_task

############################################################
#
############################################################
@api_view(['POST'])
def new_experiment(request):
    # only enable api if configured to be able to send responses
    try:
        orch_url = MiscConfig.objects.get(name='orchestrator_api_url')
        orch_token = MiscConfig.objects.get(name='orchestrator_api_token')
    except MiscConfig.DoesNotExist:
        content = {'error': 'server missing configuration to initiate communications to orchestrator'}
        return Response(content, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    req_serializer = NewExperimentSerializer(data=request.data)
    if req_serializer.is_valid():
        experiment = req_serializer.save()
        ret_serializer = IdSerializer(experiment)
        return Response(ret_serializer.data, status=status.HTTP_201_CREATED)
    else:
        return Response(req_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

############################################################
#
############################################################
@api_view(['POST'])
def module_config(request, exp_id, module):
    # only enable api if configured to be able to send responses
    try:
        orch_url = MiscConfig.objects.get(name='orchestrator_api_url')
        orch_token = MiscConfig.objects.get(name='orchestrator_api_token')
    except MiscConfig.DoesNotExist:
        content = {'error': 'server missing configuration to initiate communications to orchestrator'}
        return Response(content, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    try:
        exp_module = ExpModule.objects.get(experiment__id=exp_id, module__name=module)
    except ExpModule.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    req_serializer = ModuleConfigSerializer(data=request.data, many=True, context={'exp_module': exp_module})
    if req_serializer.is_valid():
        mod_inps = req_serializer.save()
        return Response(status=status.HTTP_200_OK)
    else:
        return Response(req_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

############################################################
#
############################################################
@api_view(['POST'])
def queue_append(request):
    # only enable api if configured to be able to send responses
    try:
        orch_url = MiscConfig.objects.get(name='orchestrator_api_url')
        orch_token = MiscConfig.objects.get(name='orchestrator_api_token')
    except MiscConfig.DoesNotExist:
        content = {'error': 'server missing configuration to initiate communications to orchestrator'}
        return Response(content, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    req_serializer = IdSerializer(data=request.data)
    if req_serializer.is_valid():
        experiment = Experiment.objects.get(id=req_serializer.validated_data.get('id'))
        experiment.status = 'Q'
        experiment.save()

        exp_module = experiment.modules.all()[0]
        inp_var = exp_module.inp_vars.all()
        out_var = exp_module.module.out_vars.filter(inp_true=False)[0]
        module = exp_module.module
        celery_task.calc_parabolic_2d.delay(
                    inp_var[0].module_input.name,
                    inp_var[1].module_input.name,
                    out_var.name,
                    experiment.id,
                    module.name
                )

        return Response(status.HTTP_200_OK)
    else:
        return Response(req_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

############################################################
#
############################################################
@api_view(['GET'])
def experiment_status(request, exp_id):
    try:
        experiment = Experiment.objects.get(id=exp_id)
    except Experiment.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    ret_serializer = StatusSerializer(experiment)
    return Response(ret_serializer.data, status=status.HTTP_200_OK)

############################################################
#
############################################################
@api_view(['GET'])
def module_status(request, exp_id, module):
    try:
        exp_module = ExpModule.objects.get(experiment__id=exp_id, module__name=module)
    except ExpModule.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    ret_serializer = StatusSerializer(exp_module)
    return Response(ret_serializer.data, status=status.HTTP_200_OK)

############################################################
#
############################################################
@api_view(['GET'])
def experiment_results(request, exp_id):
    try:
        experiment = Experiment.objects.get(id=exp_id)
    except Experiment.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    outputs = ExpOutVar.objects.filter( experiment=experiment )
    serializer = OutputSerializer(outputs, many=True)

    ret_dict = {}
    for out_dict in serializer.data:
        ret_dict.update(out_dict['name_value'])

    return Response(ret_dict, status=status.HTTP_200_OK)

############################################################
#
############################################################
@api_view(['GET'])
def module_results(request, exp_id, module):
    try:
        exp_module = ExpModule.objects.get(experiment__id=exp_id, module__name=module)
    except ExpModule.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    outputs = ExpOutVar.objects.filter( experiment=exp_module.experiment, module_output__module=exp_module.module )
    serializer = OutputSerializer(outputs, many=True)

    ret_dict = {}
    for out_dict in serializer.data:
        ret_dict.update(out_dict['name_value'])

    return Response(ret_dict, status=status.HTTP_200_OK)
