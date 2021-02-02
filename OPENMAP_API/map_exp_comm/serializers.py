from rest_framework import serializers
from map_base.models import MapInput, MapOutput
from map_base.models import Experiment, ExpStage
from map_base.models import ExpInputVal, ExpOutputVal

class ExpInputSerializer(serializers.Serializer):
    value = serializers.FloatField(allow_null=True, source='value_actual')

    def update(self, instance, validated_data):
        instance.value_actual = validated_data.get('value_actual', instance.value_actual)
        instance.save()
        return instance

class ExpOutputSerializer(serializers.Serializer):
    name = serializers.CharField(source='map_output.name')
    value = serializers.FloatField(allow_null=True)

    def validate_name(self, name):
        try:
            map_output = MapOutput.objects.get(for_map=self.context.get('for_map'), name=name)
        except MapOutput.DoesNotExist:
            message = "'{}' is not a known output for MAP".format(name)
            raise serializers.ValidationError(message)

        return name

    def create(self, validated_data):
        map_output = MapOutput.objects.get(for_map=self.context.get('for_map'), name=validated_data.get('map_output')['name'])
        exp_out, created = ExpOutputVal.objects.get_or_create(experiment=self.context.get('experiment'), map_output=map_output)
        exp_out.value = validated_data.get('value', exp_out.value)
        exp_out.save()
        return exp_out

    def update(self, instance, validated_data):
        instance.value = validated_data.get('value', instance.value)
        instance.save()
        return instance
