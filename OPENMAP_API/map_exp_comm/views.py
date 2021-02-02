from django.shortcuts import render

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.decorators import authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.permissions import IsAuthenticated

from celery import chain

from map_base.models import Experiment, ExpStage
from map_base.models import ExpInputVal, ExpOutputVal

from map_base.serializers import ExperimentStatusSerializer, StageStatusSerializer
from map_exp_comm.serializers import ExpInputSerializer, ExpOutputSerializer

import map_base.tasks as celery_task

############################################################
# experiment_status
# update experiment status
############################################################
@api_view(['POST'])
@authentication_classes([TokenAuthentication, SessionAuthentication, BasicAuthentication])
@permission_classes([IsAuthenticated])
def experiment_status(request, campaign_name, experiment_name):
    try:
        experiment = Experiment.objects.get(campaign__name=campaign_name, name=experiment_name)
        old_status = experiment.status
    except Experiment.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    req_serializer = ExperimentStatusSerializer(experiment, data=request.data)
    if req_serializer.is_valid():
        updated_experiment = req_serializer.save()
        new_status = updated_experiment.status

        # check to trigger monitoring
        if ( new_status != old_status ):
            if ( new_status == "R" ):
                # should calculate an estimated experiment length for countdown instead
                # chained in case monitoring picks up complete status before map facility offers the update
                exp_monitor = chain(
                                    celery_task.monitor_experiment_status.signature( (campaign_name, experiment_name, new_status), ignore_result=False, immutable=True),
                                    celery_task.update_model.si(campaign_name)
                                   )
                exp_monitor.apply_async( countdown=60 )
            elif ( new_status == "C" ):
                exp_finalize = chain(
                                    celery_task.monitor_experiment_status.signature( (campaign_name, experiment_name, new_status), ignore_result=False, immutable=True),
                                    celery_task.update_model.si(campaign_name)
                                    )
                exp_finalize.apply_async( countdown=10 )

        return Response(req_serializer.data, status=status.HTTP_200_OK)
    else:
        return Response(req_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

############################################################
# stage_status
# update stage status
############################################################
@api_view(['POST'])
@authentication_classes([TokenAuthentication, SessionAuthentication, BasicAuthentication])
@permission_classes([IsAuthenticated])
def stage_status(request, campaign_name, experiment_name, stage_name):
    try:
        stage = ExpStage.objects.get(experiment__campaign__name=campaign_name, experiment__name=experiment_name, map_stage__name=stage_name)
        old_status = stage.status
    except ExpStage.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    req_serializer = StageStatusSerializer(stage, data=request.data)
    if req_serializer.is_valid():
        updated_stage = req_serializer.save()
        new_status = updated_stage.status

        # check to trigger monitoring
        if ( new_status != old_status ):
            if ( new_status in ("R", "C") ):
                # should calculate an estimated stage length for countdown instead
                celery_task.monitor_stage_status.apply_async( (campaign_name, experiment_name, stage_name, new_status), countdown=10)

        return Response(req_serializer.data, status=status.HTTP_200_OK)
    else:
        return Response(req_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

############################################################
# input_value
# 
############################################################
@api_view(['PUT'])
@authentication_classes([TokenAuthentication, SessionAuthentication, BasicAuthentication])
@permission_classes([IsAuthenticated])
def input_value(request, campaign_name, experiment_name, input_name):
    try:
        exp_inp = ExpInputVal.objects.get(experiment__campaign__name=campaign_name, experiment__name=experiment_name, map_input__name=input_name)
    except ExpInputVal.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    req_serializer = ExpInputSerializer(exp_inp, data=request.data)
    if req_serializer.is_valid():
        req_serializer.save()
        return Response(req_serializer.data, status=status.HTTP_200_OK)
    else:
        return Response(req_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

############################################################
# output_value
# 
############################################################
@api_view(['POST'])
@authentication_classes([TokenAuthentication, SessionAuthentication, BasicAuthentication])
@permission_classes([IsAuthenticated])
def output_values(request, campaign_name, experiment_name):
    try:
        experiment = Experiment.objects.get(campaign__name=campaign_name, name=experiment_name)
    except Experiment.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    req_serializer = ExpOutputSerializer(data=request.data, many=True, context={'experiment': experiment, 'for_map': experiment.campaign.for_map})
    if req_serializer.is_valid():
        req_serializer.save()
        return Response(status=status.HTTP_200_OK)
    else:
        return Response(req_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['PUT'])
@authentication_classes([TokenAuthentication, SessionAuthentication, BasicAuthentication])
@permission_classes([IsAuthenticated])
def output_value(request, campaign_name, experiment_name, output_name):
    try:
        exp_out = ExpOutputVal.objects.get(experiment__campaign__name=campaign_name, experiment__name=experiment_name, map_output__name=output_name)
    except ExpOutputVal.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    request.data['name'] = output_name
    req_serializer = ExpOutputSerializer(exp_out, data=request.data, context={'for_map': exp_out.map_output.for_map})
    if req_serializer.is_valid():
        req_serializer.save()
        return Response(req_serializer.data, status=status.HTTP_200_OK)
    else:
        return Response(req_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
