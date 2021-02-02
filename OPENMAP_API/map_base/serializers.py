from rest_framework import serializers
from map_base.models import Experiment, ExpStage
from django.utils import timezone

class ExperimentStatusSerializer(serializers.Serializer):
    status = serializers.CharField()
    time = serializers.DateTimeField(required=False)

    def validate_status(self, value):
        for choice in Experiment.EXP_STATUS_CHOICES:
            if value in choice:
                return choice[0]

        raise serializers.ValidationError("string=\"{}\" is not a valid choice.".format(value), code="invalid_choice")

    def update(self, instance, validated_data):
        old_status = instance.status
        instance.status = validated_data.get('status', instance.status)
        if ( instance.status == 'R' and old_status in ('P', 'Q') ):
            instance.start_time = validated_data.get('time', timezone.localtime())
        elif ( instance.status == 'C' and old_status in ('P', 'Q', 'R', 'H') ):
            instance.end_time = validated_data.get('time', timezone.localtime())
        instance.save()
        return instance

class StageStatusSerializer(serializers.Serializer):
    status = serializers.CharField()
    time = serializers.DateTimeField(required=False)

    def validate_status(self, value):
        for choice in ExpStage.STAGE_STATUS_CHOICES:
            if value in choice:
                return choice[0]

        raise serializers.ValidationError("string=\"{}\" is not a valid choice.".format(value), code="invalid_choice")

    def update(self, instance, validated_data):
        old_status = instance.status
        instance.status = validated_data.get('status', instance.status)
        if ( instance.status == 'R' and old_status in ('P', 'Q') ):
            instance.start_time = validated_data.get('time', timezone.localtime())
        elif ( instance.status == 'C' and old_status in ('P', 'Q', 'R', 'H') ):
            instance.end_time = validated_data.get('time', timezone.localtime())
        instance.save()
        return instance
