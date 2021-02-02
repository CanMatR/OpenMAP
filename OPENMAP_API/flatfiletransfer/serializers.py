from rest_framework import serializers
from map_base.models import Experiment
from flatfiletransfer.models import ExpFile, Metadata

class FileHashRequestSerializer(serializers.Serializer):
    name_orig = serializers.CharField()
    name_hash = serializers.CharField(required=False)

    def create(self, validated_data):
        exp_file = ExpFile.objects.hashed_exp_filename(self.context.get('experiment'), validated_data.get('name_orig'))
        return exp_file

class TransferReportSerializer(serializers.Serializer):
    name_orig = serializers.CharField()

    def validate_name_orig(self, value):
        if ( value != self.instance.name_orig ):
            raise serializers.ValidationError("Incorrect original filename ('{}' given, should be '{}')".format(value, self.instance.name_orig) )
        return value

    def update(self, instance, validated_data):
        instance.transfered = True
        instance.save()
        return instance

class MetadataSerializer(serializers.Serializer):
    field = serializers.CharField(max_length=80)
    value = serializers.CharField(max_length=255)

    def create(self, validated_data):
        metadata = Metadata(exp_file = self.context.get('exp_file'), field = validated_data.get('field'), value = validated_data.get('value'))
        metadata.save()
        return metadata

    def update(self, instance, validated_data):
        instance.field = validated_data.get('field', instance.field)
        instance.value = validated_data.get('value', instance.value)
        instance.save()
        return instance
