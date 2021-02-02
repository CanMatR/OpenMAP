from django.shortcuts import render
from django.db import transaction

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.decorators import authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.permissions import IsAuthenticated
from map_base.models import Campaign, Experiment
from map_ml.serializers import ProposeExperimentSerializer, NewExperimentSerializer

import map_base.tasks as celery_task

############################################################
# ml_trained
# notify model trained
############################################################
@api_view(['POST'])
@authentication_classes([TokenAuthentication, SessionAuthentication, BasicAuthentication])
@permission_classes([IsAuthenticated])
def ml_trained(request, campaign_name):
    try:
        campaign = Campaign.objects.get(name=campaign_name)
    except Campaign.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    old_ml_model_status = campaign.ml_model_status

    campaign.ml_model_status = "T"
    campaign.save()

    if ( len(campaign.experiments.all()) < campaign.max_experiments ):
        if ( old_ml_model_status == "R" ):
            transaction.on_commit( lambda: celery_task.probe_model.apply_async( (campaign_name,) ) )
        elif ( old_ml_model_status in [ "U", "O" ] ):
            # if new results came in while ML was running, update again after proposing new experiments
            probe_then_update = chain(
                                        celery_task.probe_model.signature( (campaign_name,), ignore_result=False, immutable=True ),
                                        celery_task.update_model.si( campaign_name )
                                     )
            transaction.on_commit( lambda: probe_then_update.apply_async() )

    return Response(status=status.HTTP_200_OK)

############################################################
# ml_training_failed
# notify model trained
############################################################
@api_view(['POST'])
@authentication_classes([TokenAuthentication, SessionAuthentication, BasicAuthentication])
@permission_classes([IsAuthenticated])
def ml_training_failed(request, campaign_name):
    try:
        campaign = Campaign.objects.get(name=campaign_name)
    except Campaign.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    campaign.ml_model_status = "E"
    campaign.save()

    return Response(status=status.HTTP_200_OK)

############################################################
# propose_experiment
# provide input parameters for new experiment
############################################################
@api_view(['POST'])
@authentication_classes([TokenAuthentication, SessionAuthentication, BasicAuthentication])
@permission_classes([IsAuthenticated])
def propose_experiment(request, campaign_name):
    try:
        campaign = Campaign.objects.get(name=campaign_name)
    except Campaign.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    req_serializer = ProposeExperimentSerializer(data=request.data, context={'campaign': campaign, 'for_map': campaign.for_map})
    if req_serializer.is_valid():
        experiment = req_serializer.save()
        transaction.on_commit( lambda: celery_task.place_experiment.delay(campaign_name, experiment.name) )
        ret_serializer = NewExperimentSerializer(experiment)
        return Response(ret_serializer.data, status=status.HTTP_200_OK)
    else:
        return Response(req_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
