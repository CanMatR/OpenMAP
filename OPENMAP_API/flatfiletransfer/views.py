from django.shortcuts import render
from django.db import IntegrityError
from django.db import transaction

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.decorators import authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.permissions import IsAuthenticated
from map_base.models import Experiment
from flatfiletransfer.models import ExpFile, Metadata
from flatfiletransfer.serializers import FileHashRequestSerializer
from flatfiletransfer.serializers import TransferReportSerializer
from flatfiletransfer.serializers import MetadataSerializer


############################################################
# file_hashes
# get hashed filenames
############################################################
@api_view(['POST'])
@authentication_classes([TokenAuthentication, SessionAuthentication, BasicAuthentication])
@permission_classes([IsAuthenticated])
def file_hashes(request, campaign_name, experiment_name):
    try:
        experiment = Experiment.objects.get(campaign__name=campaign_name,name=experiment_name)
    except Experiment.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    req_serializer = FileHashRequestSerializer(data=request.data, many=True, context={'experiment': experiment})
    if req_serializer.is_valid():
        files = req_serializer.save()
        ret_serializer = FileHashRequestSerializer(files, many=True)
        return Response(req_serializer.data)
    else:
        return Response(req_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

############################################################
# file_transfer_report
# record that file transfer has completed
############################################################
@api_view(['PUT'])
@authentication_classes([TokenAuthentication, SessionAuthentication, BasicAuthentication])
@permission_classes([IsAuthenticated])
def file_transfer_report(request, name_hash):
    try:
        exp_file = ExpFile.objects.get(name_hash=name_hash)

        serializer = TransferReportSerializer(exp_file, request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    except ExpFile.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

############################################################
# file_metadata
# GET: list all of a file's metadata
# POST: add new metadata
############################################################
@api_view(['GET','POST'])
@authentication_classes([TokenAuthentication, SessionAuthentication, BasicAuthentication])
@permission_classes([IsAuthenticated])
def file_metadata(request, name_hash):
    try:
        exp_file = ExpFile.objects.get(name_hash=name_hash)
    except ExpFile.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    # list all metadata for file
    if request.method == 'GET':
        metadata = Metadata.objects.filter(exp_file=exp_file)
        serializer = MetadataSerializer(metadata, many=True)
        return Response(serializer.data)

    # add new metadata to file
    elif request.method == 'POST':
        serializer = MetadataSerializer(data=request.data, context={'exp_file': exp_file})
        if serializer.is_valid():
            try:
                with transaction.atomic():
                    serializer.save()
                    return Response(status=status.HTTP_201_CREATED)
            except IntegrityError:
                return Response("Error: metadata field already exists", status=status.HTTP_409_CONFLICT)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


############################################################
# file_metadata_detail
# GET: get specific metadata
# POST: modify specific metadata
# DELETE: remove specific metadata
############################################################
@api_view(['GET','PUT','DELETE'])
@authentication_classes([TokenAuthentication, SessionAuthentication, BasicAuthentication])
@permission_classes([IsAuthenticated])
def file_metadata_detail(request, name_hash, field):
    try:
        metadata = Metadata.objects.get(exp_file__name_hash=name_hash, field=field)
    except Metadata.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    # return metadata
    if request.method == 'GET':
        serializer = MetadataSerializer(metadata)
        return Response(serializer.data)

    # modify metadata
    elif request.method == 'PUT':
        serializer = MetadataSerializer(metadata, data=request.data)
        if serializer.is_valid():
            try:
                with transaction.atomic():
                    serializer.save()
                    return Response(serializer.data)
            except IntegrityError:
                return Response("Error: new metadata field already exists", status=status.HTTP_409_CONFLICT)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        metadata.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

