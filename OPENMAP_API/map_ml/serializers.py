from rest_framework import serializers
from map_base.models import MapStage, MapInput, MapOutput
from map_base.models import Experiment, ExpStage, ExpInputVal, ExpOutputVal

class ProposedExpInputSerializer(serializers.Serializer):
    name = serializers.CharField()
    value = serializers.FloatField()

    def validate(self, data):
        try:
            map_input = MapInput.objects.get(for_map=self.context.get('for_map'), name=data['name'])
            if ( data['value'] < map_input.min_val or data['value'] > map_input.max_val ):
                message = "value for '{}' must be between min ({}) and max ({})".format(data['name'], map_input.min_val, map_input.max_val)
                raise serializers.ValidationError(message)
        except MapInput.DoesNotExist:
            message = "'{}' is not a known input for MAP".format(data['name'])
            raise serializers.ValidationError(message)

        return data

class ProposeExperimentSerializer(serializers.Serializer):
    mode = serializers.CharField()
    inputs = ProposedExpInputSerializer(many=True)

    def create(self, validated_data):
        inputs_data = validated_data.pop('inputs')
        experiment = Experiment.objects.new_proposed(campaign=self.context.get('campaign'), mode=validated_data.get('mode'))

        for proposed_input in inputs_data:
            map_input = MapInput.objects.get(for_map=self.context.get('for_map'), name=proposed_input['name'])
            ExpInputVal.objects.create(experiment=experiment, map_input=map_input, value_request=proposed_input['value'])

        map_stages = MapStage.objects.filter(for_map=self.context.get('for_map'))
        for map_stg in map_stages:
            new_exp_stg = ExpStage.objects.create(experiment=experiment, map_stage=map_stg)

        map_outputs = MapOutput.objects.filter(for_map=self.context.get('for_map'))
        for map_out in map_outputs:
            new_exp_out = ExpOutputVal.objects.create(experiment=experiment, map_output=map_out)

        return experiment

class NewExperimentSerializer(serializers.Serializer):
    campaign_name = serializers.CharField(source='campaign.name')
    experiment_name = serializers.CharField(source='name')
